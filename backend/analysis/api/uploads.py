import hashlib
import io
import warnings

from django.http import HttpResponse
from django.utils import timezone
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import status
from rest_framework.response import Response

from analysis.conversation.serializers import serialize_upload
from analysis.guest import get_or_create_guest
from analysis.models import Conversation, UploadedImage

from .base import CsrfProtectedAPIView
from .conversations import error
from .errors import CopilotUnavailable


MAX_BYTES = 5 * 1024 * 1024
MAX_DIMENSION = 4096
MAX_PIXELS = 12_000_000
MAX_COUNT = 3
FORMATS = {"JPEG": ("image/jpeg", "JPEG"), "PNG": ("image/png", "PNG"), "WEBP": ("image/webp", "WEBP")}
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def sanitize_image(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("IMAGE_TOO_LARGE")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            source = Image.open(io.BytesIO(raw))
            detected = source.format
            if detected not in FORMATS:
                raise TypeError("UNSUPPORTED_IMAGE")
            if getattr(source, "n_frames", 1) != 1:
                raise TypeError("ANIMATED_IMAGE_UNSUPPORTED")
            source.load()
            source = ImageOps.exif_transpose(source)
            width, height = source.size
            if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_PIXELS:
                raise ValueError("IMAGE_TOO_LARGE")
            media_type, output_format = FORMATS[detected]
            mode = "RGB" if output_format == "JPEG" else ("RGBA" if "A" in source.getbands() else "RGB")
            converted = source.convert(mode)
            clean = Image.new(converted.mode, converted.size)
            clean.paste(converted)
            output = io.BytesIO()
            options = {"quality": 90} if output_format in {"JPEG", "WEBP"} else {"optimize": True}
            clean.save(output, format=output_format, **options)
            data = output.getvalue()
            if len(data) > MAX_BYTES:
                raise ValueError("IMAGE_TOO_LARGE")
            return data, media_type, width, height
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise TypeError("INVALID_IMAGE") from exc
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("IMAGE_TOO_LARGE") from exc


class UploadCreateView(CsrfProtectedAPIView):
    def post(self, request):
        guest = get_or_create_guest(request)
        conversation = Conversation.objects.filter(
            id=request.data.get("conversation_id"), guest_context=guest, expires_at__gt=timezone.now()
        ).first()
        if conversation is None:
            raise CopilotUnavailable
        if UploadedImage.objects.filter(conversation=conversation, expires_at__gt=timezone.now()).count() >= MAX_COUNT:
            return error("UPLOAD_LIMIT_REACHED", "حداکثر سه تصویر فعال مجاز است.", 429)
        image = request.FILES.get("image")
        if image is None:
            return error("VALIDATION_ERROR", "تصویر الزامی است.", 422)
        if image.size > MAX_BYTES:
            return error("IMAGE_TOO_LARGE", "حجم تصویر بیش از ۵ مگابایت است.", 413)
        raw = image.read(MAX_BYTES + 1)
        try:
            data, media_type, width, height = sanitize_image(raw)
        except ValueError as exc:
            return error(str(exc), "ابعاد، تعداد پیکسل یا حجم تصویر بیش از حد مجاز است.", 413)
        except TypeError as exc:
            return error(str(exc), "فقط تصویر ثابت JPEG، PNG یا WebP معتبر پذیرفته می‌شود.", 415)
        upload = UploadedImage.objects.create(
            conversation=conversation, content=data, media_type=media_type, size_bytes=len(data),
            width=width, height=height, sha256=hashlib.sha256(data).hexdigest(),
        )
        return Response(serialize_upload(upload), status=status.HTTP_201_CREATED)


class UploadDetailView(CsrfProtectedAPIView):
    def get_object(self, request, upload_id):
        item = UploadedImage.objects.filter(
            id=upload_id, conversation__guest_context=get_or_create_guest(request),
            conversation__expires_at__gt=timezone.now(), expires_at__gt=timezone.now(),
        ).first()
        if item is None:
            raise CopilotUnavailable
        return item

    def get(self, request, upload_id):
        item = self.get_object(request, upload_id)
        response = HttpResponse(bytes(item.content), content_type=item.media_type)
        response["Cache-Control"] = "private, no-store"
        response["Content-Security-Policy"] = "default-src 'none'; sandbox"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def delete(self, request, upload_id):
        item = self.get_object(request, upload_id)
        if item.message_id:
            return error("UPLOAD_ALREADY_REFERENCED", "تصویر به پیام پذیرفته‌شده متصل است.", 409)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
