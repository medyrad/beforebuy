import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from PIL import Image

from analysis.models import UploadedImage

from .test_conversations import csrf_client


def image_bytes(*, exif=False, size=(32, 24), format="JPEG"):
    output = io.BytesIO()
    image = Image.new("RGB", size, "indigo")
    metadata = Image.Exif()
    if exif:
        metadata[0x010E] = "private metadata"
    options = {"exif": metadata} if format == "JPEG" else {}
    image.save(output, format, **options)
    return output.getvalue()


class CopilotUploadTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        self.conversation = self.client.post(
            "/api/v1/conversations", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token
        ).json()

    def upload(self, content, name="ignored.svg"):
        return self.client.post(
            "/api/v1/uploads",
            {"conversation_id": self.conversation["id"], "image": SimpleUploadedFile(name, content, content_type="text/html")},
            HTTP_X_CSRFTOKEN=self.token,
        )

    def test_decoded_type_wins_and_metadata_is_stripped(self):
        response = self.upload(image_bytes(exif=True))
        self.assertEqual(response.status_code, 201, response.content)
        upload_id = response.json()["id"]
        downloaded = self.client.get(f"/api/v1/uploads/{upload_id}")
        self.assertEqual(downloaded["Content-Type"], "image/jpeg")
        clean = Image.open(io.BytesIO(downloaded.content))
        self.assertFalse(clean.getexif())
        self.assertNotIn("private metadata", downloaded.content.decode("latin1", errors="ignore"))

    def test_invalid_bytes_and_svg_are_rejected(self):
        self.assertEqual(self.upload(b"<svg><script>alert(1)</script></svg>").status_code, 415)
        self.assertEqual(UploadedImage.objects.count(), 0)

    def test_raw_size_dimension_pixel_and_count_limits(self):
        oversized = b"x" * (5 * 1024 * 1024 + 1)
        self.assertEqual(self.upload(oversized, "large.jpg").status_code, 413)
        self.assertEqual(self.upload(image_bytes(size=(4097, 1), format="PNG"), "wide.png").status_code, 413)
        self.assertEqual(self.upload(image_bytes(size=(4000, 4000), format="PNG"), "bomb.png").status_code, 413)
        for number in range(3):
            self.assertEqual(self.upload(image_bytes(), f"{number}.jpg").status_code, 201)
        self.assertEqual(self.upload(image_bytes(), "fourth.jpg").status_code, 429)

    def test_upload_requires_csrf_and_referenced_upload_cannot_be_deleted_alone(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/api/v1/session")
        rejected = client.post(
            "/api/v1/uploads",
            {"conversation_id": self.conversation["id"], "image": SimpleUploadedFile("x.jpg", image_bytes())},
        )
        self.assertEqual(rejected.status_code, 403)
        upload_id = self.upload(image_bytes()).json()["id"]
        from analysis.models import Message
        message = Message.objects.create(
            conversation_id=self.conversation["id"], role="USER", state="ACCEPTED", text="دارای تصویر"
        )
        UploadedImage.objects.filter(id=upload_id).update(message=message)
        response = self.client.delete(f"/api/v1/uploads/{upload_id}", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 409)

    def test_owner_isolation_and_delete(self):
        upload_id = self.upload(image_bytes()).json()["id"]
        foreign = Client()
        foreign.get("/api/v1/session")
        self.assertEqual(foreign.get(f"/api/v1/uploads/{upload_id}").status_code, 404)
        deleted = self.client.delete(f"/api/v1/uploads/{upload_id}", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(deleted.status_code, 204)
