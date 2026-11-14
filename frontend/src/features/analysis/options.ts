export const q001 = [
  ['NO_DEVICE', 'گوشی ندارم'], ['UNUSABLE', 'گوشی فعلی قابل استفاده نیست'],
  ['SERIOUS_PROBLEM', 'مشکل جدی دارد'], ['MINOR_PROBLEM', 'مشکل جزئی دارد'],
  ['WORKS_WELL', 'خوب کار می‌کند'], ['UNKNOWN', 'نمی‌دانم'],
] as const

export const q002 = [
  ['RESTORE_ESSENTIAL_ACCESS', 'دسترسی ضروری را دوباره داشته باشم'], ['SOLVE_MAJOR_LIMIT', 'یک محدودیت مهم را حل کنم'],
  ['ENABLE_IMPORTANT_NEW_USE', 'یک استفادهٔ مهم جدید ممکن شود'], ['SOLVE_MINOR_LIMIT', 'یک محدودیت جزئی را حل کنم'],
  ['PERSONAL_ENJOYMENT', 'لذت و ترجیح شخصی'], ['NO_CLEAR_BENEFIT', 'فایدهٔ مشخصی ندارم'], ['UNKNOWN', 'نمی‌دانم'],
] as const

export const q003 = [
  ['CALLS_MESSAGES', 'تماس و پیام'], ['PHOTO_VIDEO', 'عکس و ویدئو'], ['WORK_STUDY', 'کار یا تحصیل'],
  ['GAMING', 'بازی'], ['ACCESSIBILITY', 'نیازهای دسترس‌پذیری'], ['GENERAL_USE', 'استفادهٔ عمومی'],
  ['OTHER', 'کاربرد دیگر'], ['UNKNOWN', 'نمی‌دانم'],
] as const

export const q004 = [
  ['WITHIN_48_HOURS', 'تا ۴۸ ساعت آینده'], ['WITHIN_2_WEEKS', 'تا دو هفتهٔ آینده'],
  ['WITHIN_3_MONTHS', 'تا سه ماه آینده'], ['FLEXIBLE', 'زمان انعطاف‌پذیر است'], ['UNKNOWN', 'نمی‌دانم'],
] as const

export const q006 = [
  ['REPAIR_CURRENT', 'تعمیر گوشی فعلی'], ['WAIT', 'صبر کردن'], ['KEEP_CURRENT', 'ادامه با گوشی فعلی'],
  ['CHANGE_REQUIREMENTS', 'تغییر نیازها یا انتخاب'], ['ACCEPTED_TARGET_TRADEOFFS', 'محدودیت‌های مدل را پذیرفته‌ام'],
  ['NONE', 'هیچ‌کدام'], ['UNKNOWN', 'نمی‌دانم'],
] as const
