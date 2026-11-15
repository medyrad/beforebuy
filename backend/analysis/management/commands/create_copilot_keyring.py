import os
from pathlib import Path
from cryptography.fernet import Fernet
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a new mode-0600 encryption keyring; never print or overwrite a key.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, path, **options):
        target = Path(path).resolve()
        if not Path(path).is_absolute():
            raise CommandError('Use an absolute path outside the repository.')
        repository = Path(__file__).resolve().parents[4]
        if target.is_relative_to(repository):
            raise CommandError('The keyring must be outside the repository.')
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(Fernet.generate_key() + b'\n')
        except OSError:
            raise CommandError('Cannot create keyring; check parent permissions or choose a new path.') from None
        self.stdout.write('Keyring created; secret value not displayed. Keep a protected separate backup.')
