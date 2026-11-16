from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from analysis.models import Conversation, Offer, EvidenceClaim
from tests.api.test_research_api import csrf_client


class ManualOfferTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        c = self.client.post('/api/v1/conversations', {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token).json()
        self.path = '/api/v1/conversations/' + c['id']
        self.client.patch(self.path + '/brief', {'expected_revision': 0, 'changes': {
            'recipient_context': 'SELF', 'category': 'electronics', 'budget_toman': 20000000}},
            content_type='application/json', HTTP_X_CSRFTOKEN=self.token)
        self.post('/brief/confirm', {'expected_revision': 1})
        self.payload = {'expected_revision': 1, 'identity': {
            'brand': 'Test', 'model_name': 'Synthetic television', 'model_code': 'TV-55', 'category': 'electronics',
            'capacity': 'UNKNOWN', 'size': '55', 'year': '2024', 'region': 'UNKNOWN', 'warranty': 'UNKNOWN',
            'condition': 'NEW', 'bundle': 'NO'}, 'seller': 'فروشگاه آزمایشی',
            'source_url': 'https://merchant.example/product/tv', 'amount': '۱۵۰٬۰۰۰٬۰۰۰', 'currency': 'IRR',
            'shipping_toman': None, 'mandatory_toman': None, 'availability': 'IN_STOCK',
            'observed_at': (timezone.now() - timedelta(minutes=5)).isoformat()}

    def post(self, suffix, data):
        return self.client.post(self.path + suffix, data, content_type='application/json', HTTP_X_CSRFTOKEN=self.token)

    def submit(self, **changes):
        return self.post('/choices/manual-offers', {**self.payload, **changes})

    def test_persist_original_units_times_and_never_promote_to_technical_evidence(self):
        response = self.submit()
        self.assertEqual(response.status_code, 201, response.content)
        offer = Offer.objects.get(id=response.json()['offer_id'])
        self.assertEqual((offer.item_price_minor, offer.currency, offer.price_toman), (150000000, 'IRR', 15000000))
        self.assertIsNone(offer.total_payable_minor)
        self.assertGreater(offer.snapshot.created_at, offer.observed_at)
        self.assertFalse(EvidenceClaim.objects.filter(snapshot=offer.snapshot).exists())
        candidate = self.client.get(self.path + '/choices/candidates').json()['items'][0]
        self.assertEqual(candidate['sources'][0]['attribution'], 'USER_REPORTED')
        self.assertEqual(candidate['offers'][0]['original_amount'], 150000000)
        job = self.client.get('/api/v1/research-jobs/' + str(offer.snapshot.research_job_id)).json()
        self.assertEqual(job['mode'], 'MANUAL')
        self.assertEqual(job['offers'][0]['evidence_state'], 'USER_REPORTED')
        choice = self.post('/choices', {'expected_revision': 1, 'variant_ids': [candidate['id']], 'intended_variant_id': candidate['id']}).json()
        self.assertEqual(choice['result']['outcome'], 'UNRESOLVED')
        self.assertEqual(choice['result']['leaders'], [])

    def test_same_variant_requires_owner_exact_descriptor_and_confirmation(self):
        first = self.submit().json()
        self.assertEqual(self.submit(variant_id=first['variant_id']).status_code, 422)
        wrong = {**self.payload['identity'], 'size': '65'}
        self.assertEqual(self.submit(variant_id=first['variant_id'], same_variant_confirmed=True, identity=wrong).status_code, 422)
        second = self.submit(variant_id=first['variant_id'], same_variant_confirmed=True, seller='فروشگاه دوم',
                             amount='۱۴۰۰۰۰۰۰', currency='TOMAN', shipping_toman='۲۰۰۰۰', mandatory_toman='٠')
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(Offer.objects.get(id=second.json()['offer_id']).total_payable_minor, 14020000)
        self.assertEqual(self.submit().status_code, 200)
        self.assertEqual(Offer.objects.count(), 2)

    def test_same_merchant_deduplicates_but_conflicting_values_are_retained(self):
        first = self.submit().json()
        for amount in ['150000000', '140000000']:
            self.assertEqual(self.submit(variant_id=first['variant_id'], same_variant_confirmed=True, amount=amount,
                source_url='https://comparison.example/item/tv').status_code, 201)
        offers = self.client.get(self.path + '/choices/candidates').json()['items'][0]['offers']
        self.assertEqual(len(offers), 2)
        self.assertTrue(all(o['conflicting'] for o in offers))

    def test_invalid_money_url_timestamp_and_revision_fail_without_writes(self):
        for changes in [{'amount': '-1'}, {'amount': '10.5'}, {'amount': '11'}, {'amount': True},
                        {'currency': 'USD'}, {'source_url': 'javascript:alert(1)'},
                        {'source_url': 'https://127.0.0.1/x'}, {'source_url': 'https://user:pass@merchant.example/x'},
                        {'source_url': 'https://localhost/x'}, {'source_url': 'https://merchant.example:8080/x'},
                        {'observed_at': (timezone.now() + timedelta(days=1)).isoformat()}, {'unexpected': True}]:
            with self.subTest(changes=changes): self.assertEqual(self.submit(**changes).status_code, 422)
        self.assertEqual(self.submit(expected_revision=0).status_code, 409)
        self.assertEqual(self.submit(expected_revision=True).status_code, 422)
        self.assertEqual(Offer.objects.count(), 0)

    def test_foreign_expired_and_csrf_rejected(self):
        other, token = csrf_client()
        self.assertEqual(other.post(self.path + '/choices/manual-offers', self.payload, content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code, 404)
        self.assertEqual(self.client.post(self.path + '/choices/manual-offers', self.payload, content_type='application/json').status_code, 403)
        Conversation.objects.filter(id=self.path.split('/')[-1]).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.submit().status_code, 404)
        self.assertFalse(Offer.objects.exists())

    def test_malformed_body_rejected(self):
        self.assertEqual(self.post('/choices/manual-offers', []).status_code, 422)

    def test_stale_missing_price_and_out_of_stock_remain_visible_unverified(self):
        response = self.submit(amount=None, availability='OUT_OF_STOCK', observed_at=(timezone.now()-timedelta(days=2)).isoformat())
        self.assertEqual(response.status_code, 201, response.content)
        offer = self.client.get(self.path + '/choices/candidates').json()['items'][0]['offers'][0]
        self.assertFalse(offer['fresh'])
        self.assertIsNone(offer['price'])
        self.assertEqual(offer['stock'], 'OUT_OF_STOCK')
        self.assertEqual(offer['attribution'], 'USER_REPORTED')


class ManualPublicationTests(TransactionTestCase):
    setUp = ManualOfferTests.setUp
    post = ManualOfferTests.post

    def test_edit_wins_before_waiting_manual_publication(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from django.db import transaction, close_old_connections
        started = Event()
        def publish():
            close_old_connections()
            try:
                started.set()
                return self.post('/choices/manual-offers', self.payload).status_code
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                c = Conversation.objects.select_for_update().get(id=self.path.split('/')[-1])
                pending = pool.submit(publish)
                self.assertTrue(started.wait(3))
                c.brief_revision += 1; c.generation_epoch += 1; c.save()
            self.assertEqual(pending.result(timeout=10), 409)
        self.assertFalse(Offer.objects.exists())
