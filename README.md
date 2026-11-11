<div align="center">
  <img src="docs/assets/icon.svg" width="80" height="80" alt="آیکون Persian Typo Fixer">
  <h1>Persian Typo Fixer</h1>
  <p dir="rtl"><strong>اصلاح تایپ فارسی و انگلیسی با یک میان‌بر</strong></p>
  <p dir="rtl">متنی را که با چیدمان اشتباه نوشته‌اید انتخاب کنید و <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>X</kbd> را بزنید.</p>
</div>

<div align="center">

[![آخرین نسخه][release-badge]][releases]
[![دانلود ویندوز][windows-badge]][windows]
[![دانلود Ubuntu][linux-badge]][linux]
[![دانلود Fedora][fedora-badge]][fedora]
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
| **Windows** | Windows 10 نسخهٔ 1809 به بعد یا Windows 11، معماری x64 | [نصاب EXE][windows] · [Standalone EXE][standalone] · [Portable ZIP][portable] |
| **Ubuntu / Debian** | x86-64، Ubuntu 22.04 یا Debian 12 به بعد برای X11. برای Wayland به Portal سازگار نیاز است. | [بستهٔ DEB][linux] |
| **Fedora** | x86-64، Fedora 44 یا جدیدتر با X11 یا Wayland و Portal سازگار | [بستهٔ RPM][fedora] |

**Windows.** نصاب برنامه را برای حساب کاربری فعلی نصب می‌کند، میان‌بر آن را به Start Menu اضافه می‌کند و امکان فعال کردن «اجرا هنگام روشن کردن سیستم» را می‌دهد. فایل Standalone EXE را مستقیم اجرا کنید. برای نسخهٔ Portable ابتدا فایل ZIP را کامل از حالت فشرده خارج کنید و سپس EXE داخل پوشه را اجرا کنید.

**Ubuntu و Debian.** دستور زیر را در پوشهٔ فایل دانلودشده اجرا کنید.

```sh
sudo apt install ./PersianTypoFixer-v1.6.3-linux-amd64.deb
```

فایل‌های دانلودی Python را همراه دارند. [SHA-256 فایل‌ها][checksums] و [همهٔ فایل‌های انتشار][releases] در GitHub در دسترس‌اند.

**Fedora.** پس از دانلود RPM، در همان پوشه اجرا کنید.

```sh
sudo dnf install ./PersianTypoFixer-v1.6.3-linux-x86_64.rpm
```

در Linux، **Persian Typo Fixer** را از منوی برنامه‌ها باز کنید. روی Fedora Workstation با GNOME، برای دیدن آیکون System Tray افزونهٔ [AppIndicator][fedora-indicator] را نصب و فعال کنید.

پشتیبانی **Wayland آزمایشی** است و به Portalهای Remote Desktop و Clipboard نیاز دارد. در محیط‌های دارای Global Shortcuts، مانند GNOME 50، بار اول ثبت میان‌بر را تأیید کنید. برای تغییر آن، در صفحهٔ «عمومی» روی «تنظیم میان‌بر در سیستم» بزنید.

### میان‌بر Wayland در Ubuntu 24.04

GNOME 46 ثبت خودکار میان‌بر توسط برنامه را ندارد. یک بار این مراحل را انجام دهید.

1. از منوی کنار ساعت «تنظیمات» را باز کنید. در صفحهٔ «عمومی»، «فعال‌بودن اصلاح متن» را روشن کنید و «کپی فرمان میان‌بر» را بزنید.
2. در **Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**، یک میان‌بر جدید بسازید. در قسمت **Command** فرمان کپی‌شده را بچسبانید و کلیدهای دلخواه، مثلاً `Ctrl+Alt+X`، را ثبت کنید.
3. بار اولی که میان‌بر را می‌زنید، دسترسی Keyboard و Clipboard را تأیید کنید. سپس به کادر متن برگردید، متن را انتخاب کنید و دوباره میان‌بر را بزنید. همین مرحلهٔ تأیید در نسخه‌های جدیدتر Wayland هم لازم است.

## استفاده

| متن انتخاب‌شده | نتیجه |
| --- | --- |
| `sghl` | سلام |
| اثممخ | `hello` |

1. برنامه را باز کنید. آیکون **ف** در System Tray نمایش داده می‌شود.
2. بخش اشتباه متن را در یک کادر قابل ویرایش انتخاب کنید.
3. میان‌بر پیش‌فرض <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>X</kbd> را بزنید و کلیدها را رها کنید.

در Windows و X11، میان‌بر با همان کلید فیزیکی در هر دو چیدمان کار می‌کند. برای نمونه، در چیدمان فارسی `Ctrl` و `Alt` همراه «ط» همان `Ctrl+Alt+X` است. در Wayland، تطبیق کلیدها به محیط دسکتاپ بستگی دارد.

با کلیک چپ یا راست روی آیکون برنامه، منوی **System Tray** باز می‌شود. اولین گزینه، **تنظیمات**، پنجرهٔ برنامه را باز می‌کند. از نوار کناری به این بخش‌ها دسترسی دارید.

- **عمومی** شامل فعال‌بودن، اجرای خودکار، تغییر میان‌بر و ظاهر برنامه است. در «ظاهر برنامه» تم روشن، تیره یا مطابق سیستم را انتخاب کنید. برای میان‌بر یک حرف از `A` تا `Z` و دست‌کم یکی از `Ctrl`، `Alt` یا `Shift` انتخاب کنید. در Wayland، میان‌بر از تنظیمات محیط دسکتاپ تغییر می‌کند.
- **به‌روزرسانی** بررسی نسخهٔ جدید و تاریخچهٔ آفلاین نسخه‌ها را کنار هم نشان می‌دهد.
- **دربارهٔ برنامه** نسخه، نام سازنده، مجوز و لینک کد منبع را نشان می‌دهد.

با بستن پنجره، برنامه در پس‌زمینه به کار ادامه می‌دهد. برای بستن کامل برنامه، **خروج** را از منوی آیکون بزنید.

- **تبدیل دوطرفه.** نسخهٔ Windows از چیدمان‌های Persian، Persian (Standard) و English (US) پشتیبانی می‌کند. نسخهٔ Linux چیدمان‌های US و Iranian را از XKB می‌خواند.
- **پردازش روی دستگاه.** متن انتخاب‌شده روی همان دستگاه اصلاح می‌شود. برنامه پس از تبدیل، محتوای قبلی Clipboard را برمی‌گرداند. اگر در این فاصله دوباره چیزی کپی کنید، محتوای تازه حفظ می‌شود.
- **اجرا در پس‌زمینه.** میان‌بر به‌محض اجرای برنامه در دسترس است. اولین بررسی خودکار دو دقیقه بعد انجام می‌شود. برنامه فقط برای بررسی یا دانلود به‌روزرسانی به اینترنت وصل می‌شود.
- **به‌روزرسانی.** تا وقتی برنامه باز است، روزی یک بار GitHub Releases را بررسی می‌کند و برای نسخهٔ پایدار جدید اعلان می‌دهد. اگر **«بررسی به‌روزرسانی»** را بزنید و نسخهٔ جدیدی وجود داشته باشد، جزئیات آن مستقیم باز می‌شود. در Windows، برنامه پس از تأیید شما نصاب را دانلود می‌کند و SHA-256 آن را می‌سنجد. در Linux، همین پنجره لینک دریافت بستهٔ جدید را نشان می‌دهد.

<details>
<summary><strong>سازگاری و رفع مشکل میان‌بر</strong></summary>

برنامهٔ مقصد باید از `Ctrl+C` و `Ctrl+V` در کادر قابل ویرایش پشتیبانی کند. در Windows، اگر برنامهٔ مقصد با دسترسی Administrator اجرا شده، Persian Typo Fixer هم برای ارسال کلیدها به [همان سطح دسترسی][sendinput] نیاز دارد. در Wayland، تا پایان اصلاح روی همان کادر بمانید و `Ctrl+C` یا `Ctrl+V` را برای میان‌بر اصلاح انتخاب نکنید، چون برنامه از آن‌ها برای کپی و چسباندن استفاده می‌کند.

اگر میان‌بر در اختیار برنامهٔ دیگری است، در صفحهٔ **عمومی** ترکیب دیگری انتخاب کنید. در متن ترکیبی، چیدمان با توجه به حروف غالب تشخیص داده می‌شود. انتخاب بخش کوتاه و مشخص، نتیجه را قابل پیش‌بینی‌تر می‌کند.

</details>

## فناوری‌ها

[![Python][python-badge]][python]
[![PySide6 Essentials][pyside-badge]][pyside]
[![Python Xlib][xlib-badge]][xlib]
[![PyInstaller][pyinstaller-badge]][pyinstaller]
[![Inno Setup][inno-badge]][inno]

| فناوری | کاربرد |
| --- | --- |
| **Python و PySide6 Essentials** | منوی System Tray، پنجره‌ها و دسترسی به Clipboard در هر دو نسخه |
| **Win32 API** | ثبت میان‌بر سراسری و ارسال کلیدها در Windows |
| **Python Xlib و XKB** | میان‌بر، Clipboard و خواندن چیدمان صفحه‌کلید در Linux X11 |
| **PyInstaller** | بسته‌بندی برنامه و وابستگی‌ها برای هر دو سیستم‌عامل |
| **XDG Desktop Portal و dbus-next** | میان‌بر و Clipboard در Wayland |
| **Inno Setup، dpkg-deb و rpmbuild** | ساخت نصاب EXE، DEB و RPM |

## توسعه و ساخت

نسخهٔ Python مورد استفاده در CI، **3.11** است. نسخهٔ بسته‌ها در [requirements.txt](requirements.txt) و [requirements-build.txt](requirements-build.txt) ثبت شده است.

<details>
<summary><strong>Windows</strong></summary>

برای اجرای برنامه از روی کد منبع و اجرای آزمون‌ها در PowerShell، از این دستورها استفاده کنید.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

برای ساخت نصاب، Inno Setup 6.7.4 یا جدیدتر را نصب کنید. اگر کامپایلر به‌طور خودکار پیدا نشد، مسیر کامل `ISCC.exe` را در متغیر `ISCC` قرار دهید. بعد از خروج از برنامه، `.\build.bat` را اجرا کنید. فایل‌های انتشار در `dist\release` و نسخهٔ پوشه‌ای در `dist\PersianTypoFixer` ساخته می‌شوند.

پیش از اجرای این دو آزمون، برنامه را ببندید. `tests/native_hotkey_smoke.py` میان‌بر سراسری را آزمایش می‌کند و `tools/smoke_release.py` فایل‌های Standalone EXE، Portable ZIP و SHA-256 را بررسی می‌کند.

</details>

<details>
<summary><strong>Linux X11</strong></summary>

ابتدا وابستگی‌های سیستمی را از روی [Linux workflow][linux-workflow] نصب کنید. سپس برنامه را از روی کد منبع اجرا کنید.

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-build.txt
python main.py
```

برنامه را ببندید و با دستورهای زیر بسته را بسازید و آزمایش کنید.

```sh
python -m PyInstaller --noconfirm --clean packaging/linux.spec
python tools/package_linux.py
sudo apt install ./dist/release/PersianTypoFixer-v1.6.3-linux-amd64.deb
xvfb-run -a -s '-screen 0 1280x720x24 -noreset' \
  python tests/linux_x11_smoke.py /opt/persiantypefixer/PersianTypoFixer
```

</details>

GitHub Actions بستهٔ Windows را می‌سازد، بستهٔ Linux را نصب و در Xvfb آزمایش می‌کند و فایل‌های وب‌سایت را بررسی می‌کند. اگر workflow ساخت را دستی اجرا می‌کنید، گزینهٔ `upload_artifacts` فایل‌ها را در Artifacts همان اجرا قرار می‌دهد.

برای انتشار نسخه، شمارهٔ `app_version.py` و فایل `.github/release-notes/vX.Y.Z.md` را در شاخهٔ `main` آماده کنید و workflow **Publish release** را از بخش Actions روی `main` اجرا کنید. پس از ساخت و آزمون هر دو سیستم‌عامل، فایل‌ها همراه با SHA-256 و توضیحات همان فایل Markdown در GitHub Releases منتشر می‌شوند. انتشار با توکن داخلی GitHub Actions انجام می‌شود؛ پیش‌نویس موجود تکمیل می‌شود و نسخهٔ عمومی قبلی بازنویسی نمی‌شود.

## مجوز و مشارکت

ساختهٔ **Seyed Mohammad Saleh Ghotbani**. کد پروژه با [مجوز MIT](LICENSE) منتشر می‌شود. اطلاعات مجوز و کد منبع وابستگی‌ها در [Third-Party Notices](THIRD_PARTY_NOTICES.md) آمده است. برای ارسال تغییرات، [راهنمای مشارکت](CONTRIBUTING.md) را ببینید.

</div>

[website]: https://persiantypefixer.ghotbani.ir/
[issues]: https://github.com/salehghotbani/PersianTypeFixer/issues
[releases]: https://github.com/salehghotbani/PersianTypeFixer/releases/latest
[windows]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/PersianTypoFixer-v1.6.3-windows-x64-setup.exe
[standalone]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/PersianTypoFixer-v1.6.3-windows-x64.exe
[portable]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/PersianTypoFixer-v1.6.3-windows-x64-portable.zip
[linux]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/PersianTypoFixer-v1.6.3-linux-amd64.deb
[fedora]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/PersianTypoFixer-v1.6.3-linux-x86_64.rpm
[fedora-indicator]: https://packages.fedoraproject.org/pkgs/gnome-shell-extension-appindicator/gnome-shell-extension-appindicator/
[checksums]: https://github.com/salehghotbani/PersianTypeFixer/releases/download/v1.6.3/SHA256SUMS.txt
[release-badge]: https://img.shields.io/github/v/release/salehghotbani/PersianTypeFixer?label=Release&color=2454e6
[windows-badge]: https://img.shields.io/badge/Windows-x64-2563eb
[linux-badge]: https://img.shields.io/badge/Ubuntu-DEB-16836b?logo=ubuntu&logoColor=white
[fedora-badge]: https://img.shields.io/badge/Fedora-RPM-294172?logo=fedora&logoColor=white
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
