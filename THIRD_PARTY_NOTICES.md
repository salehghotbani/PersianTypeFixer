# مجوز وابستگی‌ها و دریافت سورس

کد Persian Typo Fixer با مجوز [MIT](LICENSE) منتشر می‌شود. این مجوز جایگزین
مجوز اجزای همراه برنامه نیست. نسخه‌های انتشار از کتابخانه‌های زیر، بدون تغییر
در سورس آن‌ها، استفاده می‌کنند.

| جزء | نسخه ساخت 1.0.0 | مجوز / اطلاعات |
| --- | --- | --- |
| CPython | 3.11.9 | Python Software Foundation؛ متن کامل در `licenses/Python.txt` |
| PySide6 Essentials و Shiboken6 | 6.12.0 | LGPL-3.0؛ متعلق به The Qt Company Ltd. و مشارکت‌کنندگان |
| Qt Core، Gui، Network، Widgets و افزونه‌های سیستم‌عامل | 6.12.0 | LGPL-3.0؛ متعلق به The Qt Company Ltd. و مشارکت‌کنندگان |
| PyInstaller bootloader | 6.22.3 | GPL-2.0-or-later با استثنای انتشار bootloader؛ `licenses/PyInstaller.txt` |
| OpenSSL، وابستگی Python | 3.0.13 | Apache-2.0؛ `licenses/OpenSSL.txt`؛ Copyright 1998–2024 The OpenSSL Project Authors |
| Microsoft Visual C++ runtime | همراه wheel رسمی Qt / Python | جزء اجرایی قابل بازتوزیع مایکروسافت؛ مجوز آن متعلق به مایکروسافت است |
| Python Xlib (لینوکس) | 0.33 | LGPL-2.1-or-later؛ مجوز همراه فرادادهٔ بسته در `_internal` قرار دارد |
| six (لینوکس) | 1.17.0 | MIT؛ مجوز همراه فرادادهٔ بسته در `_internal` قرار دارد |
| dbus-next (Linux) | 0.2.3 | MIT؛ مجوز همراه فرادادهٔ بسته در `_internal` قرار دارد |

متن کامل LGPLv3 و GPLv3 در `licenses/LGPL-3.0.txt` و `licenses/GPL-3.0.txt`
همراه بسته قرار دارد. مجموعه اعلان‌های upstream مربوط به Qt Base نیز در
`licenses/QtBase-6.12.0-NOTICES.txt` ارائه می‌شود. Qt شامل اجزای ثالث با مجوزهای مستقل نیز هست؛ فهرست و
متن آن‌ها در سورس همان نسخه و [مستندات مجوزهای Qt](https://doc.qt.io/qt-6/licenses-used-in-qt.html)
ارائه شده است. برای Qt for Python نیز [اعلان‌های upstream](https://doc.qt.io/qtforpython-6/licenses.html)
را ببینید. برنامه از Qt Virtual Keyboard، WebEngine یا افزونه‌های GPL-only استفاده نمی‌کند.

## سورس متناظر کتابخانه‌ها

دانلود سورس متناظر با کتابخانه‌های 6.12.0 این انتشار:

- [Qt Base 6.12.0](https://download.qt.io/archive/qt/6.12/6.12.0/submodules/qtbase-everywhere-src-6.12.0.tar.xz)
- [Qt Wayland 6.12.0](https://download.qt.io/archive/qt/6.12/6.12.0/submodules/qtwayland-everywhere-src-6.12.0.tar.xz)
- [PySide6 / Shiboken6 6.12.0](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/pyside-setup-everywhere-src-6.12.0.tar.xz)
- [سورس CPython 3.11.9](https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tar.xz)
- [سورس OpenSSL 3.0.13](https://github.com/openssl/openssl/releases/tag/openssl-3.0.13)
- [سورس و مجوز PyInstaller 6.22.3](https://github.com/pyinstaller/pyinstaller/tree/v6.22.3)
- [سورس و مجوز Python Xlib 0.33](https://github.com/python-xlib/python-xlib/tree/0.33)
- [سورس و مجوز six 1.17.0](https://github.com/benjaminp/six/tree/1.17.0)
- [سورس و مجوز dbus-next 0.2.3](https://pypi.org/project/dbus-next/0.2.3/#files)

کد برنامه و تمام دستورهای ساخت در tag همین انتشار در مخزن موجود است. هیچ
محدودیتی برای اشکال‌زدایی، مهندسی معکوس یا تغییر کتابخانه‌ها به منظور استفاده
از حقوق LGPL از طرف این پروژه اعمال نمی‌شود.

## جایگزینی کتابخانه‌ها و بازسازی

برای جایگزینی ساده DLLها، از بسته `portable.zip` استفاده کنید. پس از خروج کامل
از برنامه، کتابخانه‌های هم‌معماری و سازگار Qt / PySide6 / Shiboken6 را در پوشه
`_internal` جایگزین کنید. مجموعه کتابخانه‌ها باید با یکدیگر سازگار باشد.

برای بازسازی EXE مستقل با نسخه تغییر‌یافته، سورس همین tag را دریافت کنید، محیط
ساخت را طبق README بسازید، نسخه اصلاح‌شده کتابخانه‌ها را در آن محیط نصب کنید و
فایل spec را با همان Python اجرا کنید. استفاده مستقیم از PyInstaller مانع
نصب دوباره نسخه pin‌شده توسط `build.bat` می‌شود:

```powershell
.\build\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean PersianTypoFixer.spec
```

EXE مستقل هنگام اجرا DLLها و اعلان‌های مجوز را در پوشه موقت PyInstaller باز
می‌کند و تا خروج برنامه از آن‌ها استفاده می‌کند. نسخه پوشه‌ای به استخراج موقت
نیاز ندارد. راهنمای نصب و کد برنامه امکان بازسازی و اجرای نسخه تغییر‌یافته را فراهم می‌کنند.
