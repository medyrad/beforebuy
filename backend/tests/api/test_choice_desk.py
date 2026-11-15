from unittest.mock import patch
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from tests.api.test_research_api import csrf_client
from analysis.models import Conversation


class ChoiceDeskTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        c = self.client.post('/api/v1/conversations', {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token).json()
        self.path = '/api/v1/conversations/' + c['id']
        self.client.patch(self.path + '/brief', {'expected_revision': 0, 'changes': {
            'recipient_context': 'SELF', 'category': 'electronics', 'budget_toman': 10000000,
            'comparison': {'intent': 'ENJOYMENT', 'budget_mode': 'STRICT', 'criteria': [], 'prefer_lower_cost': False}}},
            content_type='application/json', HTTP_X_CSRFTOKEN=self.token)
        self.post('/brief/confirm', {'expected_revision': 1})

    def post(self, suffix, data, client=None, token=None):
        return (client or self.client).post(self.path + suffix, data, content_type='application/json',
                                             HTTP_X_CSRFTOKEN=token or self.token)

    def test_demo_uses_persisted_entities_and_immutable_choices(self):
        self.assertIsNone(self.client.get(self.path + '/choices').json())
        result = self.post('/choices/demo', {'expected_revision': 1, 'category': 'electronics'})
        self.assertEqual(result.status_code, 201, result.content)
        choices = self.post('/choices', {'expected_revision': 1, 'variant_ids': result.json()['variant_ids'],
                                        'intended_variant_id': result.json()['variant_ids'][0]})
        self.assertEqual(choices.status_code, 201, choices.content)
        data = choices.json()
        self.assertTrue(data['current'])
        self.assertEqual(data['result']['brief_snapshot']['budget_toman'], 10000000)
        self.assertEqual(len(data['result']['items']), 3)
        self.assertEqual(data['result']['items'][0]['sources'][0]['attribution'], 'SYNTHETIC')
        self.assertEqual(self.client.get(self.path + '/choices').json()['id'], data['id'])
        self.client.patch(self.path + '/brief', {'expected_revision': 1, 'changes': {'budget_toman': 1}},
                          content_type='application/json', HTTP_X_CSRFTOKEN=self.token)
        self.assertFalse(self.client.get(self.path + '/choices').json()['current'])
        self.assertEqual(self.client.get(self.path + '/choices').json()['result']['brief_snapshot']['budget_toman'], 10000000)
        self.assertEqual(self.post('/choices', {'expected_revision': 1}).status_code, 409)

    def test_owner_csrf_expiry_and_validation(self):
        other, token = csrf_client()
        self.assertEqual(self.post('/choices/demo', {'expected_revision': 1, 'category': 'electronics'}, other, token).status_code, 404)
        self.assertEqual(self.client.post(self.path + '/choices', {}, content_type='application/json').status_code, 403)
        self.assertEqual(self.post('/choices/demo', {'expected_revision': True, 'category': 'electronics'}).status_code, 422)
        c = Conversation.objects.get(id=self.path.split('/')[-1]); c.expires_at = timezone.now() - timedelta(seconds=1); c.save()
        self.assertEqual(self.client.get(self.path + '/choices').status_code, 404)

    def test_late_publication_rejects_changed_brief(self):
        from analysis.ranking.service import publish_choice
        c = Conversation.objects.get(id=self.path.split('/')[-1])
        c.brief_revision += 1; c.generation_epoch += 1; c.save()
        with self.assertRaises(ValueError):
            publish_choice(c.id, c.guest_context_id, 1, c.generation_epoch - 1, {}, [])

    def test_limits_foreign_variants_and_invalid_category(self):
        from uuid import uuid4
        ids = self.post('/choices/demo', {'expected_revision': 1, 'category': 'electronics'}).json()['variant_ids']
        for values in [ids * 2, [ids[0], ids[0]], [str(uuid4())], [True]]:
            self.assertEqual(self.post('/choices', {'expected_revision': 1, 'variant_ids': values, 'intended_variant_id': values[0]}).status_code, 422)
        result = self.client.patch(self.path + '/brief', {'expected_revision': 1, 'changes': {'comparison': {'intent': []}}},
                                  content_type='application/json', HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(result.status_code, 422)

    def test_three_categories_and_same_pipeline_captured_attribution(self):
        from analysis.models import SourceSnapshot
        for category, field, value in [('electronics', 'portable', True), ('home', 'dishwasher_safe', True), ('sports', 'size_eu', 42)]:
            c = Conversation.objects.get(id=self.path.split('/')[-1])
            c.brief.category = category
            c.brief.budget_toman = {'electronics': 10000000, 'home': 6000000, 'sports': 2000000}[category]
            c.brief.recipient_context = {'electronics': 'SELF', 'home': 'HOUSEHOLD', 'sports': 'GIFT'}[category]
            scope = {'electronics': 'SELF', 'home': 'HOUSEHOLD', 'sports': 'RECIPIENT'}[category]
            c.brief.comparison = {'budget_mode': 'STRICT', 'criteria': [{'field': field, 'expected': value, 'kind': 'HARD', 'scope': scope}]}
            c.brief.save()
            ids = self.post('/choices/demo', {'expected_revision': 1, 'category': category}).json()['variant_ids']
            response = self.post('/choices', {'expected_revision': 1, 'variant_ids': ids, 'intended_variant_id': ids[0]})
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(next(i for i in response.json()['result']['items'] if i['id'] == ids[0])['group'], 'SUPPORTED')
            self.assertEqual(next(i for i in response.json()['result']['items'] if i['id'] == ids[1])['group'], 'INCOMPATIBLE')
            self.assertEqual(next(i for i in response.json()['result']['items'] if i['id'] == ids[2])['group'],
                             {'electronics': 'SUPPORTED', 'home': 'INCOMPATIBLE', 'sports': 'UNRESOLVED'}[category])
        SourceSnapshot.objects.filter(research_job__conversation=c).update(extractor_version='captured-v1')
        response = self.post('/choices', {'expected_revision': 1, 'variant_ids': ids, 'intended_variant_id': ids[0]})
        self.assertEqual(response.json()['result']['items'][0]['sources'][0]['attribution'], 'CAPTURED_FIXTURE')
        SourceSnapshot.objects.filter(research_job__conversation=c).update(retrieval_time=timezone.now() - timedelta(days=2))
        self.assertEqual(self.post('/choices', {'expected_revision': 1, 'variant_ids': ids, 'intended_variant_id': ids[0]}).json()['result']['outcome'], 'UNRESOLVED')


class ChoiceConcurrencyTests(TransactionTestCase):
    def test_edit_wins_lock_and_old_publication_cannot_commit(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from django.db import transaction, close_old_connections
        from analysis.ranking.service import publish_choice
        client, token = csrf_client()
        data = client.post('/api/v1/conversations', {}, content_type='application/json', HTTP_X_CSRFTOKEN=token).json()
        c = Conversation.objects.get(id=data['id'])
        c.brief.confirmed = True; c.brief.save()
        started = Event()
        def late():
            close_old_connections(); started.set()
            try:
                publish_choice(c.id, c.guest_context_id, 0, 0, {}, [])
                return 'published'
            except ValueError:
                return 'rejected'
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                locked = Conversation.objects.select_for_update().get(id=c.id)
                pending = executor.submit(late)
                self.assertTrue(started.wait(3))
                locked.brief_revision = 1; locked.generation_epoch = 1; locked.save()
            self.assertEqual(pending.result(timeout=5), 'rejected')
        self.assertFalse(c.choice_sets.exists())
