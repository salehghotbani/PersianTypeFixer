# مشارکت در توسعه

برای گزارش مشکل، از [Issues](https://github.com/salehghotbani/PersianTypeFixer/issues)
استفاده کنید. نسخه ویندوز، نسخه برنامه، نام برنامه مقصد، چیدمان صفحه‌کلید و
یک نمونه کوتاه و غیرحساس از متن ورودی و خروجی مورد انتظار را بنویسید.

## راه‌اندازی

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

آزمون `tests/native_hotkey_smoke.py` باید روی ویندوز و هنگام بسته بودن نسخه‌های
دیگر برنامه اجرا شود. این آزمون به برنامه‌های دیگر کلید نمی‌فرستد.

تغییرات تبدیل متن را در `layout_conversion.py`، عملیات انتخاب و کلیپ‌بورد را در
`selection_conversion.py` و ارتباط با ویندوز را در `windows_api.py` نگه دارید.
این برنامه فقط متن انتخاب‌شده را با میان‌بر صریح کاربر اصلاح می‌کند؛ افزودن
پایش تایپ عادی یا ارسال متن به شبکه خارج از هدف پروژه است.

پیش از Pull Request، تست‌های مرتبط و `build.bat` را اجرا کنید. پوشه‌های `build`،
`dist` و محیط مجازی را commit نکنید. مشارکت‌ها تحت [مجوز MIT](LICENSE) پروژه
پذیرفته می‌شوند؛ کد دیگر پروژه‌ها باید مجوز و انتساب معتبر خود را حفظ کند.
