from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from analysis.models import ChoiceSet, Conversation, EvidenceClaim, Offer, SourceSnapshot
from .engine import RULE_VERSION


def candidates_for(conversation, variant_ids=None):
    snapshots = list(SourceSnapshot.objects.filter(research_job__conversation=conversation,
        status__in=['EXTRACTED', 'CACHE_HIT']).select_related('source_policy').order_by('-retrieval_time', 'id')[:200])
    snapshot_map = {s.id: s for s in snapshots}
    now = timezone.now()
    values = {}
    def entry(variant):
        return values.setdefault(str(variant.id), {'id': str(variant.id), 'name': variant.product.model_name,
            'product_id': str(variant.product_id), 'category': variant.attributes.get('category', 'UNKNOWN'),
            'identity': variant.attributes, 'facts': {}, 'offers': [], 'sources': []})
    def source(s):
        label = 'USER_REPORTED' if s.extractor_version == 'USER-ENTRY-v1' else 'SYNTHETIC' if s.extractor_version in {'SYNTHETIC-v1', 'CHOICE-DEMO-v1'} else 'CAPTURED_FIXTURE' if s.fixture_label else 'VERIFIED_SOURCE'
        until = s.retrieval_time + timedelta(seconds=s.source_policy.freshness_seconds)
        return {'id': str(s.id), 'attribution': label, 'url': s.canonical_url,
                'label': s.fixture_label or s.source_policy.hostname, 'observed_at': s.retrieval_time.isoformat(),
                'fresh_until': until.isoformat(), 'fresh': until > now}
    for claim in EvidenceClaim.objects.filter(snapshot__in=snapshots, variant__isnull=False).select_related('variant__product').order_by('id'):
        if variant_ids and str(claim.variant_id) not in variant_ids: continue
        item = entry(claim.variant); s = source(snapshot_map[claim.snapshot_id])
        if s not in item['sources']: item['sources'].append(s)
        value = (claim.normalized_value or {}).get('value')
        if isinstance(value, dict) and 'value' in value: value = value['value']
        fact = {'value': value, 'state': claim.evidence_status if s['fresh'] else 'STALE',
                'attribution': s['attribution'], 'variant_id': str(claim.variant_id), 'evidence_id': str(claim.id),
                'source_id': s['id'], 'source_location': claim.source_location}
        old = item['facts'].get(claim.field)
        if old and (old['value'] != value or old['state'] != 'SUPPORTED' or fact['state'] != 'SUPPORTED'):
            fact['state'] = 'CONFLICTING'
        item['facts'][claim.field] = fact
    for offer in Offer.objects.filter(snapshot__in=snapshots).select_related('variant__product').order_by('id'):
        if variant_ids and str(offer.variant_id) not in variant_ids: continue
        item = entry(offer.variant); s = source(snapshot_map[offer.snapshot_id])
        if s not in item['sources']: item['sources'].append(s)
        item['offers'].append({'id': str(offer.id), 'seller': offer.seller, 'price': offer.price_toman,
            'shipping': offer.shipping_minor, 'mandatory': offer.mandatory_charges_minor,
            'stock': offer.availability, 'fresh': s['fresh'], 'source_id': s['id'], 'attribution': s['attribution'],
            'observation_kind': offer.observation_kind, 'url': offer.merchant_url or s['url'],
            'original_amount': offer.item_price_minor, 'original_currency': offer.currency,
            'entered_at': snapshot_map[offer.snapshot_id].created_at.isoformat(),
            'total': offer.total_payable_minor, 'warranty': offer.warranty,
            'observed_at': offer.observed_at.isoformat()})
    for item in values.values():
        unique, merchant_values = {}, {}
        for offer in sorted(item['offers'], key=lambda o: (o['observed_at'], o['id']), reverse=True):
            seller = ' '.join((offer['seller'] or '').translate(str.maketrans('يك', 'یک')).split()).casefold()
            # Missing merchant identity must never collapse unrelated observations.
            seller = seller or offer['id']
            state = (offer['price'], offer['shipping'], offer['mandatory'], offer['stock'])
            key = (seller, state, offer['attribution'])
            unique.setdefault(key, offer)
            if offer['fresh']:
                merchant_values.setdefault(seller, set()).add(state)
        for (seller, _, _), offer in unique.items():
            offer['conflicting'] = len(merchant_values.get(seller, set())) > 1
        item['offers'] = list(unique.values())
    return sorted(values.values(), key=lambda item: item['id'])


def publish_choice(conversation_id, guest_id, revision, epoch, result, snapshot_ids):
    with transaction.atomic():
        c = Conversation.objects.select_for_update().filter(id=conversation_id, guest_context_id=guest_id,
                                                            expires_at__gt=timezone.now()).first()
        if c is None or c.brief_revision != revision or c.generation_epoch != epoch or not c.brief.confirmed:
            raise ValueError('STALE_COMPARISON')
        sources = list(SourceSnapshot.objects.filter(id__in=snapshot_ids, research_job__conversation=c).select_related('source_policy'))
        if len(sources) != len(set(snapshot_ids)): raise ValueError('EVIDENCE_UNAVAILABLE')
        until = min((s.retrieval_time + timedelta(seconds=s.source_policy.freshness_seconds) for s in sources),
                    default=timezone.now())
        return ChoiceSet.objects.create(conversation=c, brief_revision=revision, generation_epoch=epoch,
            rule_version=RULE_VERSION, result=result, snapshot_ids=snapshot_ids, evidence_valid_until=until)


def serialize_choice(choice, conversation):
    current = (conversation.brief.confirmed and choice.brief_revision == conversation.brief_revision
               and choice.generation_epoch == conversation.generation_epoch and choice.evidence_valid_until > timezone.now())
    return {'id': str(choice.id), 'brief_revision': choice.brief_revision, 'current': current,
            'evidence_valid_until': choice.evidence_valid_until.isoformat(),
            'result': choice.result, 'created_at': choice.created_at.isoformat()}
