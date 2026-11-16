"""User-entered observations. No retrieval, factual claims or identity inference."""
import hashlib
import ipaddress
import json
import re
import uuid
from datetime import timedelta
from urllib.parse import urlsplit
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.response import Response
from analysis.guest import get_or_create_guest
from analysis.models import GuestContext, Product, Variant, Offer, SourcePolicy, SourceSnapshot, ResearchJob, StreamOperation
from .base import CsrfProtectedAPIView
from .choices import revision_error
from .conversations import active_conversation, error

MARKER = 'USER-ENTRY-v1'
IDENTITY_FIELDS = {'brand', 'model_name', 'model_code', 'category', 'capacity', 'size', 'year', 'region', 'warranty', 'condition', 'bundle'}
DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def money(value):
    if value is None or value == '': return None
    if not isinstance(value, str) or len(value) > 32: raise ValueError('مبلغ را با رقم و بدون اعشار وارد کنید.')
    value = value.translate(DIGITS).strip().replace('٬', ',')
    if not re.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)', value):
        raise ValueError('مبلغ را با رقم و بدون اعشار وارد کنید.')
    result = int(value.replace(',', ''))
    if result > 10**13: raise ValueError('مبلغ بیش از محدودهٔ مجاز است.')
    return result


def safe_source_url(value):
    if not isinstance(value, str) or len(value) > 1000 or any(ord(c) <= 32 for c in value) or '\\' in value:
        raise ValueError('لینک عمومی HTTPS معتبر لازم است.')
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or '').encode('idna').decode('ascii').lower()
        if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.fragment
                or parsed.port not in (None, 443) or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}', host)
                or host.endswith(('.localhost', '.local', '.internal', '.invalid'))):
            raise ValueError()
        try: ipaddress.ip_address(host)
        except ValueError: pass
        else: raise ValueError()
    except (ValueError, UnicodeError):
        raise ValueError('لینک عمومی HTTPS بدون نام کاربری، رمز یا پورت سفارشی لازم است.') from None
    return value


def validate(data):
    allowed = {'expected_revision', 'variant_id', 'same_variant_confirmed', 'identity', 'seller', 'source_url',
               'amount', 'currency', 'shipping_toman', 'mandatory_toman', 'availability', 'observed_at'}
    if not isinstance(data, dict) or set(data) - allowed: raise ValueError('فیلد نامعتبر در پیشنهاد فروش.')
    identity = data.get('identity')
    if (not isinstance(identity, dict) or set(identity) != IDENTITY_FIELDS
            or any(not isinstance(v, str) or not 1 <= len(v.strip()) <= 120 for v in identity.values())):
        raise ValueError('مدل دقیق و ویژگی‌های نسخه را کامل کنید؛ موارد نامعلوم را UNKNOWN بنویسید.')
    identity = {k: v.strip() for k, v in identity.items()}
    if (identity['category'] not in {'electronics', 'home', 'sports'} or identity['condition'] not in {'NEW', 'USED', 'REFURBISHED', 'UNKNOWN'}
            or identity['bundle'] not in {'YES', 'NO', 'UNKNOWN'}): raise ValueError('دسته یا وضعیت نسخه نامعتبر است.')
    seller = data.get('seller')
    if not isinstance(seller, str) or not 1 <= len(seller.strip()) <= 200: raise ValueError('نام فروشنده لازم است.')
    url = safe_source_url(data.get('source_url'))
    amount = money(data.get('amount'))
    currency = data.get('currency')
    if currency not in {'IRR', 'TOMAN'}: raise ValueError('واحد باید ریال یا تومان باشد.')
    if amount is not None and currency == 'IRR' and amount % 10: raise ValueError('مبلغ ریالی باید به تومان کامل تبدیل شود؛ گرد نمی‌کنیم.')
    price = amount // 10 if amount is not None and currency == 'IRR' else amount
    shipping, mandatory = money(data.get('shipping_toman')), money(data.get('mandatory_toman'))
    if any(v is not None and v > 10**12 for v in (price, shipping, mandatory)): raise ValueError('مبلغ بیش از محدودهٔ مجاز است.')
    stock = data.get('availability')
    if stock not in {'IN_STOCK', 'OUT_OF_STOCK', 'UNKNOWN', 'PREORDER'}: raise ValueError('وضعیت موجودی نامعتبر است.')
    observed = data.get('observed_at')
    try: observed = parse_datetime(observed) if isinstance(observed, str) else None
    except ValueError: observed = None
    if observed is None or timezone.is_naive(observed) or observed > timezone.now(): raise ValueError('زمان مشاهده باید گذشته و دارای منطقهٔ زمانی باشد.')
    return identity, seller.strip(), url, amount, currency, price, shipping, mandatory, stock, observed


class ManualOfferView(CsrfProtectedAPIView):
    @transaction.atomic
    def post(self, request, conversation_id):
        guest = get_or_create_guest(request)
        GuestContext.objects.select_for_update().get(id=guest.id)
        c = active_conversation(guest, conversation_id, lock=True)
        if not isinstance(request.data, dict):
            return error('VALIDATION_ERROR', 'بدنهٔ پیشنهاد باید یک شیء باشد.', 422)
        failure = revision_error(request.data, c)
        if failure is not None: return failure
        try:
            identity, seller, url, amount, currency, price, shipping, mandatory, stock, observed = validate(request.data)
        except ValueError as exc:
            return error('VALIDATION_ERROR', str(exc), 422)
        if c.brief.category in {'electronics', 'home', 'sports'} and c.brief.category != identity['category']:
            return error('VALIDATION_ERROR', 'دستهٔ محصول با نیاز تأییدشده متفاوت است.', 422)
        descriptor = {**identity, 'category': identity['category']}
        variant_id = request.data.get('variant_id')
        variant = None
        if variant_id:
            try: variant_id = uuid.UUID(str(variant_id))
            except ValueError: return error('VALIDATION_ERROR', 'نسخهٔ محصول نامعتبر است.', 422)
            variant = Variant.objects.filter(id=variant_id, offers__snapshot__research_job__conversation=c,
                offers__snapshot__extractor_version=MARKER).first()
            if variant is None or request.data.get('same_variant_confirmed') is not True or variant.attributes != descriptor:
                return error('VARIANT_MISMATCH', 'یکسانی تمام ویژگی‌های نسخه را تأیید کنید؛ نسخهٔ متفاوت را جدا ثبت کنید.', 422)
        canonical = [identity, seller, url, amount, currency, shipping, mandatory, stock, observed.isoformat()]
        fingerprint = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        existing = Offer.objects.filter(snapshot__research_job__conversation=c, snapshot__extractor_version=MARKER,
                                         snapshot__fingerprint=fingerprint).first()
        if existing:
            return Response({'variant_id': str(existing.variant_id), 'offer_id': str(existing.id), 'attribution': 'USER_REPORTED'})
        if Offer.objects.filter(snapshot__research_job__conversation=c, snapshot__extractor_version=MARKER).count() >= 100:
            return error('MANUAL_OFFER_LIMIT', 'سقف صد مشاهدهٔ دستی این گفتگو پر شده است.', 409)
        now = timezone.now()
        policy, _ = SourcePolicy.objects.get_or_create(hostname='user-entry.beforebuy.invalid', defaults={
            'live_enabled': False, 'source_role': 'USER_REPORTED', 'freshness_seconds': 21600})
        if variant is None:
            product = Product.objects.create(brand=identity['brand'], model_name=identity['model_name'])
            variant = Variant.objects.create(product=product, attributes=descriptor,
                identifiers={'user_reported_model_code': identity['model_code']}, region=identity['region'],
                condition=identity['condition'], bundle=identity['bundle'] == 'YES')
        operation = StreamOperation.objects.create(conversation=c, operation_kind='RESEARCH', status='COMPLETED',
            expected_brief_revision=c.brief_revision, idempotency_key=str(uuid.uuid4()), request_hash=fingerprint, completed_at=now)
        job = ResearchJob.objects.create(conversation=c, operation=operation, brief_revision=c.brief_revision,
            generation_epoch=c.generation_epoch, request_hash=fingerprint, mode='MANUAL', status='SUCCESS',
            stage='COMPLETED', total_units=1, completed_units=1, started_at=now, completed_at=now)
        snapshot = SourceSnapshot.objects.create(research_job=job, source_policy=policy, canonical_url=url,
            source_role='USER_REPORTED', status='EXTRACTED', retrieval_time=observed,
            fingerprint=fingerprint, extractor_version=MARKER, raw_expires_at=now)
        offer = Offer.objects.create(snapshot=snapshot, variant=variant, item_price_minor=amount, currency=currency,
            price_toman=price, shipping_minor=shipping, mandatory_charges_minor=mandatory,
            total_payable_minor=sum((price, shipping, mandatory)) if all(v is not None for v in (price, shipping, mandatory)) else None,
            seller=seller, merchant_url=url, observation_kind='USER_REPORTED', warranty=identity['warranty'],
            availability=stock, observed_at=observed)
        c.choice_sets.update(evidence_valid_until=now)
        return Response({'variant_id': str(variant.id), 'offer_id': str(offer.id), 'attribution': 'USER_REPORTED'}, status=201)
