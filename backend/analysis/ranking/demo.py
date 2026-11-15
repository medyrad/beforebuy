"""Project-authored synthetic examples, never historical/current market facts."""
import uuid
from datetime import timedelta
from django.utils import timezone
from analysis.models import Product, Variant, SourcePolicy, SourceSnapshot, ResearchJob, StreamOperation, Offer, EvidenceClaim

DEMO = {
    'electronics': [('رایانهٔ نمایشی آ', 8000000, 0, {'capacity_gb': 256, 'portable': True}),
                    ('رایانهٔ نمایشی ب', 7000000, None, {'capacity_gb': 512, 'portable': False}),
                    ('رایانهٔ نمایشی پ', 9000000, 0, {'capacity_gb': 256, 'portable': True})],
    'home': [('وسیلهٔ خانگی نمایشی آ', 6000000, 0, {'capacity_l': 5, 'dishwasher_safe': True}),
             ('وسیلهٔ خانگی نمایشی ب', 4000000, 0, {'capacity_l': 3, 'dishwasher_safe': False}),
             ('وسیلهٔ خانگی نمایشی پ', 7000000, None, {'capacity_l': 5})],
    'sports': [('کفش نمایشی آ', 2000000, 0, {'size_eu': 42, 'waterproof': True}),
               ('کفش نمایشی ب', 1500000, 0, {'size_eu': 40, 'waterproof': False}),
               ('کفش نمایشی پ', 1800000, None, {'size_eu': 42})],
}


def seed_demo(conversation, category):
    now = timezone.now()
    policy, _ = SourcePolicy.objects.get_or_create(hostname='choice-demo.beforebuy.invalid', defaults={
        'readiness': 'SYNTHETIC_FIXTURE', 'live_enabled': False, 'source_role': 'MERCHANT', 'freshness_seconds': 86400})
    operation = StreamOperation.objects.create(conversation=conversation, operation_kind='RESEARCH',
        expected_brief_revision=conversation.brief_revision,
        idempotency_key=str(uuid.uuid4()), request_hash='demo', status='COMPLETED', completed_at=now)
    job = ResearchJob.objects.create(conversation=conversation, operation=operation, brief_revision=conversation.brief_revision,
        generation_epoch=conversation.generation_epoch, request_hash='demo', mode='FIXTURE', status='SUCCESS',
        stage='COMPLETED', total_units=3, completed_units=3)
    ids = []
    for name, price, shipping, facts in DEMO[category]:
        product = Product.objects.create(brand='نمونهٔ آموزشی', model_name=name)
        variant = Variant.objects.create(product=product, attributes={'category': category})
        snapshot = SourceSnapshot.objects.create(research_job=job, source_policy=policy, source_role='MERCHANT',
            fixture_label='نمونهٔ مصنوعی آموزشی — ' + name, status='EXTRACTED', retrieval_time=now,
            fingerprint='synthetic', extractor_version='CHOICE-DEMO-v1', raw_expires_at=now + timedelta(hours=24))
        for field, value in facts.items():
            EvidenceClaim.objects.create(snapshot=snapshot, variant=variant, field=field,
                normalized_value={'value': value}, evidence_status='SUPPORTED', source_location='project-authored-demo')
        Offer.objects.create(snapshot=snapshot, variant=variant, item_price_minor=price, currency='TOMAN', price_toman=price,
            shipping_minor=shipping, mandatory_charges_minor=0, total_payable_minor=price if shipping == 0 else None,
            seller='فروشندهٔ مصنوعی', availability='IN_STOCK', observed_at=now)
        ids.append(str(variant.id))
    return ids
