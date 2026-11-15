from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from tests.api.test_research_api import csrf_client


class PreferenceMemoryTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()

    def write(self, method, path, data=None):
        return getattr(self.client, method)('/api/v1/' + path, data or {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token)

    def conversation(self, scope='SELF', temporary=False, value=True):
        c = self.write('post', 'conversations', {'temporary': temporary}).json()
        path = 'conversations/' + c['id']
        result = self.write('patch', path + '/brief', {'expected_revision': 0, 'changes': {
            'category': 'electronics', 'recipient_context': scope,
            'comparison': {'criteria': [{'field': 'portable', 'expected': value, 'kind': 'PREFERENCE',
                                        'scope': 'RECIPIENT' if scope == 'GIFT' else scope}]}}})
        self.assertEqual(result.status_code, 200)
        return path

    def enable(self):
        r = self.write('patch', 'copilot/settings', {'expected_revision': 0, 'memory_enabled': True})
        self.assertEqual(r.status_code, 200)

    def propose(self, path):
        self.write('post', path + '/brief/confirm', {'expected_revision': 1})
        return self.write('post', path + '/memory', {'expected_revision': 1})

    def test_default_off_temporary_and_candidates_are_not_reused(self):
        self.assertFalse(self.client.get('/api/v1/copilot/settings').json()['memory_enabled'])
        path = self.conversation()
        self.assertEqual(self.propose(path).status_code, 409)
        self.enable()
        self.assertEqual(self.propose(self.conversation(temporary=True)).status_code, 409)
        r = self.propose(path)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['items'][0]['state'], 'CANDIDATE')
        self.assertEqual(self.client.get('/api/v1/' + path + '/memory').json()['items'], [])

    def test_confirm_reuse_override_scope_export_and_cascade(self):
        self.enable()
        source = self.conversation()
        item = self.propose(source).json()['items'][0]
        r = self.write('patch', 'copilot/memory/' + item['id'], {'expected_revision': 0, 'state': 'CONFIRMED'})
        self.assertEqual(r.status_code, 200)
        target = self.conversation(value=False)
        offered = self.client.get('/api/v1/' + target + '/memory').json()['items']
        self.assertEqual(len(offered), 1)
        applied = self.write('patch', target + '/memory', {'expected_revision': 1, 'memory_id': item['id'], 'memory_revision': 1})
        self.assertEqual(applied.status_code, 200)
        self.assertFalse(applied.json()['comparison']['criteria'][0]['expected'])
        gift = self.conversation('GIFT')
        self.assertEqual(self.client.get('/api/v1/' + gift + '/memory').json()['items'], [])
        exported = self.client.get('/api/v1/copilot/memory/export').json()
        self.assertEqual(exported['items'][0]['id'], item['id'])
        self.write('delete', source)
        self.assertEqual(self.client.get('/api/v1/copilot/memory').json()['items'], [])

    def test_owner_csrf_stale_expiry_and_disable_delete(self):
        self.enable()
        item = self.propose(self.conversation()).json()['items'][0]
        path = 'copilot/memory/' + item['id']
        self.assertEqual(self.client.patch('/api/v1/' + path, {}, content_type='application/json').status_code, 403)
        other, token = csrf_client()
        self.assertEqual(other.delete('/api/v1/' + path, HTTP_X_CSRFTOKEN=token).status_code, 404)
        self.assertEqual(self.write('patch', path, {'expected_revision': 9, 'state': 'CONFIRMED'}).status_code, 409)
        self.write('patch', 'copilot/settings', {'expected_revision': 1, 'memory_enabled': False})
        self.assertEqual(len(self.client.get('/api/v1/copilot/memory').json()['items']), 1)
        from analysis.models import PreferenceMemory
        PreferenceMemory.objects.filter(id=item['id']).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.write('patch', path, {'expected_revision': 0, 'state': 'CONFIRMED'}).status_code, 404)
        self.assertEqual(self.client.get('/api/v1/copilot/memory').json()['items'], [])
        self.assertEqual(self.write('delete', 'copilot/memory').status_code, 204)

    def test_two_conversations_applied_preference_and_explicit_override(self):
        self.enable()
        item = self.propose(self.conversation()).json()['items'][0]
        self.write('patch', 'copilot/memory/' + item['id'], {'expected_revision': 0, 'state': 'CONFIRMED'})
        c = self.write('post', 'conversations').json(); path = 'conversations/' + c['id']
        self.write('patch', path + '/brief', {'expected_revision': 0, 'changes': {'category': 'electronics', 'recipient_context': 'SELF'}})
        result = self.write('patch', path + '/memory', {'expected_revision': 1, 'memory_id': item['id'], 'memory_revision': 1})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['comparison']['criteria'][0]['expected'], True)
        self.assertFalse(result.json()['confirmed'])
        self.assertEqual(result.json()['revision'], 2)
        self.write('post', path + '/brief/confirm', {'expected_revision': 2})
        self.assertEqual(self.write('patch', path + '/memory', {'expected_revision': 2, 'memory_id': item['id'], 'memory_revision': 1}).status_code, 409)
        changed = self.write('patch', path + '/brief', {'expected_revision': 2, 'changes': {'comparison': {
            'criteria': [{'field': 'portable', 'expected': False, 'kind': 'PREFERENCE', 'scope': 'SELF'}]}}})
        self.assertFalse(changed.json()['comparison']['criteria'][0]['expected'])
        self.assertTrue(self.client.get('/api/v1/copilot/memory').json()['items'][0]['criterion']['expected'])
