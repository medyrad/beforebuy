from django.core.management.base import BaseCommand, CommandError
from analysis.ai.credentials import rotate_credentials, CredentialUnavailable


class Command(BaseCommand):
    help = 'Rewrap credential data keys with the first master in the configured runtime keyring.'

    def handle(self, **options):
        try:
            count = rotate_credentials()
        except CredentialUnavailable:
            raise CommandError('Credential rotation failed; no rows changed. Check the keyring locally.') from None
        self.stdout.write(f'rotated={count}')
