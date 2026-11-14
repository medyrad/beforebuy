const labels: Record<string, string> = {
  BUDGET_MISMATCH: 'قیمت بالاتر از بودجه است', INSUFFICIENT_CONTEXT: 'برای جمع‌بندی، اطلاعات بیشتری لازم است',
  RECONSIDER_OR_WAIT: 'بازنگری یا صبر منطقی است', PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN: 'تعویض قابل توجیه است؛ بودجه نامعلوم است',
  DISCRETIONARY_CHOICE_BUDGET_UNKNOWN: 'انتخاب شخصی روشن است؛ بودجه نامعلوم است', PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET: 'تعویض قابل توجیه و در محدودهٔ بودجه است',
  DISCRETIONARY_CHOICE_WITHIN_BUDGET: 'انتخاب شخصی روشن و در محدودهٔ بودجه است', WITHIN_BUDGET: 'در محدودهٔ بودجه',
  ABOVE_BUDGET: 'بالاتر از بودجه', BUDGET_UNKNOWN: 'بودجه نامعلوم', JUSTIFICATION_SUPPORTED: 'وضعیت فعلی و فایدهٔ مورد انتظار، خرید یا تعویض را توجیه می‌کنند',
  DISCRETIONARY_CLEAR: 'انتخاب شخصی روشن', WEAK_OR_NONE: 'دلیل مشخص کافی نیست', JUSTIFICATION_UNKNOWN: 'دلیل خرید نامعلوم',
  CONTRADICTORY: 'پاسخ‌ها نیاز به بازبینی دارند', TARGET_FIT_UNVERIFIED: 'تناسب مدل تأیید نشده', USER_REPORTED_SUPPORT: 'طبق گزارش شما مناسب است',
  USER_REPORTED_MISMATCH: 'طبق گزارش شما مناسب نیست', ACKNOWLEDGED: 'محدودیت‌ها پذیرفته شده‌اند', UNRESOLVED: 'محدودیت‌ها حل نشده‌اند',
  NOT_REQUIRED: 'در این نتیجه تعیین‌کننده نیست', TARGET_MODEL_CAPABILITY: 'توانایی فنی مدل هدف', BUDGET_FIT: 'تناسب با بودجه',
  PURCHASE_JUSTIFICATION: 'دلیل خرید یا تعویض', VERIFY_TARGET_CAPABILITY: 'پیش از خرید، توانایی مدل را از منبع معتبر بررسی کنید.',
  REPAIR_NOTED: 'گزینهٔ تعمیر را نیز مقایسه کنید.', WAIT_NOTED: 'هزینه و نیاز را پس از یک دورهٔ کوتاه دوباره بررسی کنید.',
}

export const faLabel = (value: string) => labels[value] ?? 'وضعیت ثبت‌شده'
