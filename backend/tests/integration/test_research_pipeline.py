import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from analysis.conversation.streaming import claim_operation
from analysis.models import EvidenceClaim, Offer, Product, ResearchJob, SourcePolicy, SourceSnapshot, Variant
from analysis.research.fetch import FetchBudget, SafeFetcher
from analysis.research.jobs import (
    _cached_candidate, cancel_research_job, create_research_job, perform_research, publish_evidence_unit,
)


PRODUCT = {
    "@context": "https://schema.org", "@type": "Product", "name": "گوشی کنترل‌شده E1",
    "brand": {"@type": "Brand", "name": "نمونه"}, "sku": "CONTROL-E1-256",
    "offers": {"@type": "Offer", "price": "12500000", "priceCurrency": "IRT",
               "availability": "https://schema.org/InStock", "seller": {"name": "فروشگاه کنترل‌شده"}},
}


@override_settings(BEFOREBUY_RESEARCH_MODE="LIVE")
class ControlledResearchPipelineTests(TestCase):
    def setUp(self):
        self.observed = []

        observed = self.observed
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                observed.append((self.headers.get("Host"), self.path))
                body = ("<html><script type='application/ld+json'>" + json.dumps(PRODUCT) +
                        "</script></html>").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.policy = SourcePolicy.objects.create(
            hostname="products.example", allowed_ports=[self.port], allowed_path_prefixes=["/products/"],
            redirect_hostnames=[], source_role="MERCHANT", readiness="ENABLED", live_enabled=True,
            min_interval_ms=0,
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.get("/api/v1/session")
        self.token = self.client.cookies["csrftoken"].value
        self.conversation = self.client.post(
            "/api/v1/conversations", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token
        ).json()
        self.client.patch(
            f"/api/v1/conversations/{self.conversation['id']}/brief",
            {"expected_revision": 0, "changes": {"recipient_context": "SELF", "category": "موبایل",
                                                  "budget_toman": 20_000_000, "use_cases": ["روزمره"]}},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )
        self.client.post(
            f"/api/v1/conversations/{self.conversation['id']}/brief/confirm",
            {"expected_revision": 1}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _fetcher(self):
        def connector(_scheme, _hostname, _port, approved_ip, timeout):
            self.assertEqual(approved_ip, "93.184.216.34")
            return http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        return SafeFetcher(resolver=lambda *_: ["93.184.216.34"], connector=connector)

    @patch("analysis.api.research.submit_research_reserved", return_value=True)
    @patch("analysis.api.research.release_research_slot")
    @patch("analysis.api.research.reserve_research_slot", return_value=True)
    def test_api_to_real_transport_extractor_and_atomic_evidence(self, _reserve, _release, _submit):
        url = f"http://products.example:{self.port}/products/e1"
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/api/v1/conversations/{self.conversation['id']}/research",
                {"expected_brief_revision": 1,
                 "targets": [{"source_id": "products.example", "url": url}]},
                content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
                HTTP_IDEMPOTENCY_KEY="controlled-pipeline-key-001",
            )
        self.assertEqual(response.status_code, 202, response.content)
        job = ResearchJob.objects.get(id=response.json()["job"]["id"])
        self.assertTrue(claim_operation(job.operation_id, "controlled-worker"))
        self.assertTrue(perform_research(job.id, "controlled-worker", fetcher=self._fetcher()))
        job.refresh_from_db()
        self.assertEqual(job.status, "SUCCESS")
        self.assertEqual((job.request_count, job.redirect_count), (1, 0))
        self.assertGreater(job.wire_bytes, 0)
        self.assertGreater(job.decoded_bytes, 0)
        snapshot = job.snapshots.get()
        self.assertEqual(snapshot.canonical_url, url)
        self.assertEqual(snapshot.status, "EXTRACTED")
        self.assertEqual(snapshot.offers.get().item_price_minor, 12_500_000)
        self.assertTrue(snapshot.claims.filter(field="sku", normalized_value={"value": "CONTROL-E1-256"}).exists())
        self.assertEqual(self.observed, [(f"products.example:{self.port}", "/products/e1")])
        self.assertEqual(job.operation.events.filter(event_type="evidence.published").count(), 1)

    def test_atomic_publication_rollback_leaves_no_identity_or_evidence(self):
        from analysis.models import Conversation, GuestContext
        from analysis.research.jobs import create_research_job
        guest = GuestContext.objects.get(conversations__id=self.conversation["id"])
        conversation = Conversation.objects.get(id=self.conversation["id"])
        job, _ = create_research_job(
            conversation=conversation, idempotency_key="rollback-pipeline-key-001", request_hash="f" * 64,
            source_ids=["synthetic-appliance-v1"], mode="FIXTURE",
        )
        self.assertTrue(claim_operation(job.operation_id, "rollback-worker"))
        candidate = {"kind": "failure", "source_id": "products.example", "policy_id": self.policy.id,
                     "url": f"http://products.example:{self.port}/products/e1", "retrieved_at": job.created_at,
                     "status": "FAILED", "failure_code": "TEST_FAILURE"}
        with self.assertRaisesRegex(RuntimeError, "rollback"):
            publish_evidence_unit(
                job.id, "rollback-worker", candidate, FetchBudget(), completed=1,
                before_complete=lambda: (_ for _ in ()).throw(RuntimeError("rollback")),
            )
        self.assertFalse(SourceSnapshot.objects.filter(research_job=job).exists())
        self.assertEqual(job.operation.events.filter(event_type="evidence.published").count(), 0)
        self.assertEqual((Product.objects.count(), Variant.objects.count(), Offer.objects.count(), EvidenceClaim.objects.count()),
                         (0, 0, 0, 0))

    def test_cancelled_cache_reuse_cannot_publish_a_snapshot(self):
        from analysis.models import Conversation, GuestContext
        guest = GuestContext.objects.get(conversations__id=self.conversation["id"])
        conversation = Conversation.objects.get(id=self.conversation["id"])
        first, _ = create_research_job(
            conversation=conversation, idempotency_key="cache-source-key-001", request_hash="a" * 64,
            source_ids=["synthetic-appliance-v1"], mode="FIXTURE",
        )
        self.assertTrue(claim_operation(first.operation_id, "cache-source-worker"))
        self.assertTrue(perform_research(first.id, "cache-source-worker"))
        second, _ = create_research_job(
            conversation=conversation, idempotency_key="cache-target-key-002", request_hash="b" * 64,
            source_ids=["synthetic-appliance-v1"], mode="FIXTURE",
        )
        self.assertTrue(claim_operation(second.operation_id, "cache-target-worker"))
        candidate = _cached_candidate(second, second.targets[0])
        self.assertIsNotNone(candidate)
        changed, _, _ = cancel_research_job(second.id)
        self.assertTrue(changed)
        self.assertFalse(publish_evidence_unit(
            second.id, "cache-target-worker", candidate, FetchBudget(), completed=1
        ))
        self.assertFalse(SourceSnapshot.objects.filter(research_job=second).exists())
