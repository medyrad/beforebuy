from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analysis.models import SourcePolicy


POLICIES = {
    "torob.com": {
        "allowed_path_prefixes": ["/p/"], "redirect_hostnames": ["torob.com"],
        "source_role": "COMPARISON", "robots_url": "https://torob.com/robots.txt",
        "terms_url": "https://torob.com/pages/terms/",
        "access_notes": "No relevant explicit automated-access rule found; exact-product narrow factual pilot only.",
    },
    "www.technolife.com": {
        "allowed_path_prefixes": ["/product-597521", "/product-435247"], "redirect_hostnames": ["www.technolife.com"],
        "source_role": "MERCHANT", "robots_url": "https://www.technolife.com/robots.txt",
        "terms_url": "https://www.technolife.com/staticpage/page-14/قوانین%20و%20مقررات",
        "access_notes": "No relevant explicit automated-access rule found; unit-conflict adapter must fail closed.",
    },
    "bkalaa.com": {
        "allowed_path_prefixes": ["/product/"], "redirect_hostnames": ["bkalaa.com", "www.bkalaa.com"],
        "source_role": "MERCHANT", "robots_url": "https://bkalaa.com/robots.txt", "terms_url": None,
        "access_notes": "No relevant explicit automated-access rule found in inspected material.",
    },
    "takkalaban.com": {
        "allowed_path_prefixes": ["/product/"], "redirect_hostnames": ["takkalaban.com", "www.takkalaban.com"],
        "source_role": "MERCHANT", "robots_url": "https://takkalaban.com/robots.txt", "terms_url": None,
        "access_notes": "No relevant explicit automated-access rule found in inspected material.",
    },
}


class Command(BaseCommand):
    help = "Explicitly install or disable the reviewed Phase 9.2 exact-product source policies."

    def add_arguments(self, parser):
        parser.add_argument("--enable", action="store_true", help="Enable the narrow live pilot policies.")
        parser.add_argument("--disable", action="store_true", help="Disable the narrow live pilot policies.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["enable"] == options["disable"]:
            raise CommandError("Choose exactly one of --enable or --disable")
        enabled = options["enable"]
        for hostname, values in POLICIES.items():
            defaults = {
                **values, "allowed_ports": [443], "redirect_rules": {},
                "live_enabled": enabled,
                "access_notes": values["access_notes"] + " Review evidence dated 2026-11-15: "
                    "specs/002-personalized-shopping-copilot/source-feasibility.md; exact review time unknown. "
                    "Configuration toggle does not fetch/review documents or prove technical readiness.",
                "retention_notes": "Raw response <=24h; normalized evidence expires with owning conversation.",
                "display_constraints": "Minimal factual fields with source and merchant attribution; no market-wide claim.",
                "freshness_seconds": 21600, "min_interval_ms": 2000,
            }
            source, created = SourcePolicy.objects.select_for_update().get_or_create(
                hostname=hostname, defaults={**defaults, "readiness": "DISABLED"})
            if not created:
                for evidence_field in ("access_notes", "robots_url", "terms_url"):
                    defaults.pop(evidence_field)
            for key, value in defaults.items():
                setattr(source, key, value)
            source.save(update_fields=list(defaults))
            self.stdout.write(f"{hostname}: {'ENABLED' if enabled else 'DISABLED'}")
