<div align="center">
  <img src="docs/assets/icon.svg" width="80" height="80" alt="آیکون Persian Typo Fixer">
  <h1>Persian Typo Fixer</h1>
  <p dir="rtl"><strong>اصلاح تایپ فارسی و انگلیسی با یک میان‌بر</strong></p>
  <p dir="rtl">متنی را که با چیدمان اشتباه نوشته‌ای انتخاب کن و <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>X</kbd> را بزن.</p>
</div>

<div align="center">

[![آخرین نسخه][release-badge]][releases]
[![دانلود ویندوز][windows-badge]][windows]
[![دانلود لینوکس][linux-badge]][linux]
[![مجوز MIT][license-badge]](LICENSE)

[![ساخت ویندوز][windows-ci]][windows-workflow]
[![ساخت و آزمون لینوکس][linux-ci]][linux-workflow]
[![بررسی وب‌سایت][site-ci]][site-workflow]

**[وب‌سایت و نمایش زنده][website] · [یادداشت‌های انتشار](CHANGELOG.md) · [گزارش مشکل][issues]**

</div>

<div dir="rtl">

## دانلود و نصب

| سیستم‌عامل | پیش‌نیاز | دانلود |
| --- | --- | --- |
| **ویندوز** | ویندوز ۱۰ نسخهٔ ۱۸۰۹ یا جدیدتر و ویندوز ۱۱، معماری x64 | [نصاب EXE][windows] · [نسخهٔ مستقل][standalone] · [نسخهٔ قابل حمل][portable] |
| **لینوکس** | Ubuntu 22.04 یا Debian 12 به بالا، معماری amd64، نشست **X11** و سینی سیستم | [بستهٔ DEB][linux] |

**ویندوز.** نصاب برای کاربر جاری نصب می‌کند و میان‌بر Start Menu و گزینهٔ «اجرا هنگام روشن کردن سیستم» را اضافه می‌کند. فایل EXE مستقل را می‌توانید مستقیم اجرا کنید. برای نسخهٔ قابل حمل، کل فایل ZIP را استخراج کنید و EXE داخل آن را اجرا کنید.

**لینوکس.** در پوشهٔ فایل دانلودشده دستور زیر را اجرا کنید. سپس **Persian Typo Fixer** را از فهرست برنامه‌ها باز کنید.

```sh
sudo apt install ./PersianTypoFixer-v1.3.1-linux-amd64.deb
```

بسته‌های آماده Python را همراه دارند. [هش SHA-256 فایل‌ها][checksums] و [همهٔ فایل‌های انتشار][releases] در GitHub در دسترس‌اند.

## استفاده

| متن انتخاب‌شده | نتیجه |
| --- | --- |
| `sghl` | سلام |
| اثممخ | `hello` |

1. برنامه را باز کنید. آیکون **ف** در سینی سیستم نمایش داده می‌شود.
2. بخش اشتباه متن را در یک کادر قابل ویرایش انتخاب کنید.
3. میان‌بر <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>X</kbd> را بزنید و کلیدها را رها کنید.

با راست‌کلیک روی آیکون، میان‌بر و گزینهٔ **«اجرا هنگام روشن کردن سیستم»** را تنظیم کنید، به‌روزرسانی را بررسی کنید یا از برنامه خارج شوید. با فعال کردن این گزینه، برنامه پس از ورود به حساب کاربری اجرا می‌شود. **دربارهٔ برنامه** نسخهٔ نصب‌شده، نام سازنده، مجوز و لینک سورس را نشان می‌دهد.

- **تبدیل دوطرفه.** در ویندوز چیدمان‌های Persian و Persian (Standard) در کنار English (US) پشتیبانی می‌شوند. در لینوکس نگاشت چیدمان‌های US و Iranian از XKB خوانده می‌شود.
- **پردازش روی دستگاه.** متن انتخاب‌شده روی همان دستگاه اصلاح می‌شود. پس از عملیات، کلیپ‌بورد قبلی بازگردانده می‌شود و اگر در این فاصله دوباره کپی کنید، کپی تازه در اولویت است.
- **شروع سبک.** میان‌بر از آغاز اجرا آماده است. اولین بررسی خودکار نسخه دو دقیقه بعد انجام می‌شود و بخش شبکه فقط هنگام بررسی یا دانلود فعال است. بررسی دستی فوری است.
- **به‌روزرسانی.** برنامه نسخهٔ پایدار را از GitHub بررسی می‌کند. ویندوز پس از تأیید شما نصاب را دانلود و SHA-256 آن را بررسی می‌کند. در لینوکس، پنجرهٔ نسخهٔ تازه شما را به بستهٔ جدید هدایت می‌کند.

<details>
<summary><strong>سازگاری و رفع مشکل میان‌بر</strong></summary>

برنامهٔ مقصد باید از `Ctrl+C` و `Ctrl+V` در یک کادر قابل ویرایش پشتیبانی کند. در ویندوز، برنامه‌های اجراشده با دسترسی Administrator به [سطح دسترسی یکسان برای ارسال ورودی][sendinput] نیاز دارند. در لینوکس، میان‌بر سراسری به X11 نیاز دارد.

اگر میان‌بر در اختیار برنامهٔ دیگری است، پس از آزاد کردن آن گزینهٔ **فعال** را در منوی آیکون بزنید. در متن ترکیبی، چیدمان با توجه به حروف غالب تشخیص داده می‌شود. انتخاب بخش کوتاه و مشخص، نتیجه را قابل پیش‌بینی‌تر می‌کند.

</details>

## فناوری‌ها

[![Python][python-badge]][python]
[![PySide6 Essentials][pyside-badge]][pyside]
[![Python Xlib][xlib-badge]][xlib]
[![PyInstaller][pyinstaller-badge]][pyinstaller]
[![Inno Setup][inno-badge]][inno]

| فناوری | کاربرد |
| --- | --- |
| **Python و PySide6 Essentials** | منوی سینی سیستم، پنجره‌ها و کلیپ‌بورد مشترک بین دو نسخه |
| **Win32 API** | ثبت میان‌بر سراسری و ارسال ورودی در ویندوز |
| **Python Xlib و XKB** | میان‌بر، کلیپ‌بورد و خواندن چیدمان در لینوکس X11 |
| **PyInstaller** | بسته‌بندی برنامه و وابستگی‌ها برای هر دو سیستم‌عامل |
| **Inno Setup و dpkg-deb** | ساخت نصاب EXE ویندوز و بستهٔ DEB لینوکس |

## توسعه و ساخت

نسخهٔ Python مورد استفاده در CI، **3.11** است. نسخهٔ بسته‌ها در [requirements.txt](requirements.txt) و [requirements-build.txt](requirements-build.txt) ثبت شده است.

<details>
<summary><strong>ویندوز</strong></summary>

برای اجرای سورس و تست‌ها در PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

برای ساخت نصاب، Inno Setup 6.7.4 یا جدیدتر را نصب کنید. اگر کامپایلر به‌طور خودکار پیدا نشد، مسیر کامل `ISCC.exe` را در متغیر `ISCC` قرار دهید. بعد از خروج از برنامه، `.\build.bat` را اجرا کنید. فایل‌های انتشار در `dist\release` و نسخهٔ پوشه‌ای در `dist\PersianTypoFixer` ساخته می‌شوند.

`tests/native_hotkey_smoke.py` میان‌بر واقعی را بررسی می‌کند و `tools/smoke_release.py` برای آزمون نسخهٔ مستقل، ZIP و هش‌هاست. هنگام اجرای این آزمون‌ها نمونهٔ در حال اجرای برنامه را ببندید.

</details>

<details>
<summary><strong>لینوکس X11</strong></summary>

ابتدا وابستگی‌های سیستمی بخش نصب را از [گردش‌کار لینوکس][linux-workflow] فراهم کنید. برای اجرای سورس، ساخت بسته و آزمودن آن:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-build.txt
python main.py
```

پس از خروج از برنامه:

```sh
python -m PyInstaller --noconfirm --clean packaging/linux.spec
python tools/package_linux.py
sudo apt install ./dist/release/PersianTypoFixer-v1.3.1-linux-amd64.deb
xvfb-run -a -s '-screen 0 1280x720x24 -noreset' \
  python tests/linux_x11_smoke.py /opt/persiantypefixer/PersianTypoFixer
```

</details>

GitHub Actions بستهٔ ویندوز را می‌سازد، بستهٔ لینوکس را در Xvfb نصب و آزمایش می‌کند و فایل‌های وب‌سایت را بررسی می‌کند. در اجرای دستی ساخت، گزینهٔ `upload_artifacts` فایل‌ها را به Artifacts اضافه می‌کند.

## مجوز و مشارکت

ساختهٔ **Seyed Mohammad Saleh Ghotbani**. کد پروژه با [مجوز MIT](LICENSE) منتشر می‌شود. مجوز و سورس وابستگی‌ها در [اعلان‌های نرم‌افزارهای ثالث](THIRD_PARTY_NOTICES.md) آمده است. برای ارسال تغییرات، [راهنمای مشارکت](CONTRIBUTING.md) را ببینید.

</div>

[website]: https://persiantypefixer.ghotbani.ir/
[issues]: https://github.com/salehghotbani/PersianTypeFixer/issues
[releases]: https://github.com/salehghotbani/PersianTypeFixer/releases/latest
[windows]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.3.1/PersianTypoFixer-v1.3.1-windows-x64-setup.exe
[standalone]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.3.1/PersianTypoFixer-v1.3.1-windows-x64.exe
[portable]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.3.1/PersianTypoFixer-v1.3.1-windows-x64-portable.zip
[linux]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.3.1/PersianTypoFixer-v1.3.1-linux-amd64.deb
[checksums]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.3.1/SHA256SUMS.txt
[release-badge]: https://img.shields.io/github/v/release/salehghotbani/PersianTypeFixer?label=Release&color=2454e6
[windows-badge]: https://img.shields.io/badge/Windows-x64-2563eb
[linux-badge]: https://img.shields.io/badge/Linux-X11%20%7C%20amd64-16836b?logo=linux&logoColor=white
[license-badge]: https://img.shields.io/badge/License-MIT-475569
[windows-workflow]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/windows.yml
[linux-workflow]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/linux.yml
[site-workflow]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/site-check.yml
[windows-ci]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/windows.yml/badge.svg?branch=main&event=push
[linux-ci]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/linux.yml/badge.svg?branch=main&event=push
[site-ci]: https://github.com/salehghotbani/PersianTypeFixer/actions/workflows/site-check.yml/badge.svg?branch=main&event=push
[python-badge]: https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white
[pyside-badge]: https://img.shields.io/badge/PySide6_Essentials-6.12.0-167a4b?logo=qt&logoColor=white
[xlib-badge]: https://img.shields.io/badge/Python_Xlib-0.33-475569
[pyinstaller-badge]: https://img.shields.io/badge/PyInstaller-6.22.3-345d9d
[inno-badge]: https://img.shields.io/badge/Inno_Setup-6.7.4-475569
[python]: https://www.python.org/
[pyside]: https://doc.qt.io/qtforpython-6/
[xlib]: https://github.com/python-xlib/python-xlib
[pyinstaller]: https://pyinstaller.org/
[inno]: https://jrsoftware.org/isinfo.php
[sendinput]: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
