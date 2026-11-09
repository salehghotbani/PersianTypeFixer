"""Fetch stable GitHub releases and stream verified installers to temporary files."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform as host_platform
import re
import sys

from PySide6.QtCore import QDir, QObject, QTemporaryDir, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

REPO = "salehghotbani/PersianTypeFixer"
LATEST_RELEASE = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOAD_HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
MAX_METADATA = 512 * 1024
MAX_INSTALLER = 150 * 1024 * 1024
CHUNK = 128 * 1024


@dataclass(frozen=True)
class Release:
    version: str
    notes: str
    url: str
    size: int
    sha256: str


def parse_release(payload, current_version, platform="win32"):
    if not isinstance(payload, dict):
        raise ValueError("Invalid release response")
    if payload.get("draft") or payload.get("prerelease"):
        return None
    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]{1,6}(\.[0-9]{1,6}){2}", tag):
        raise ValueError("Invalid version tag")
    version = tag[1:]
    if tuple(map(int, version.split("."))) <= tuple(map(int, current_version.split("."))):
        return None

    if platform.startswith("linux"):
        distro = host_platform.freedesktop_os_release()
        rpm = distro.get("ID") == "fedora" or "fedora" in distro.get("ID_LIKE", "").split()
        suffix = "x86_64.rpm" if rpm else "amd64.deb"
        filename = f"PersianTypoFixer-{tag}-linux-{suffix}"
    else:
        filename = f"PersianTypoFixer-{tag}-windows-x64-setup.exe"
    url = f"https://github.com/{REPO}/releases/download/{tag}/{filename}"
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Invalid release assets")
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("name") != filename:
            continue
        digest = asset.get("digest")
        size = asset.get("size")
        if (asset.get("state") == "uploaded" and asset.get("browser_download_url") == url
                and type(size) is int and 0 < size <= MAX_INSTALLER
                and isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest)):
            notes = payload.get("body")
            return Release(version, notes if isinstance(notes, str) else "", url, size, digest[7:])
    raise ValueError("The release has no verifiable installer for this platform")


class InstallerDownload:
    def __init__(self, release):
        self.release = release
        self.directory = QTemporaryDir(QDir.tempPath() + "/PersianTypoFixer-update-XXXXXX")
        if not self.directory.isValid():
            raise OSError(self.directory.errorString())
        self.path = Path(self.directory.path()).resolve() / "setup.exe"
        self.file = self.path.open("xb")
        self.digest = hashlib.sha256()
        self.received = 0

    def write(self, data):
        if self.received + len(data) > self.release.size:
            raise ValueError("Installer exceeds expected size")
        self.file.write(data)
        self.digest.update(data)
        self.received += len(data)

    def verify(self):
        self.file.close()
        if self.received != self.release.size or self.digest.hexdigest() != self.release.sha256:
            raise ValueError("Installer integrity check failed")

    def remove(self):
        try:
            self.file.close()
        except OSError:
            pass
        finally:
            self.directory.remove()


class UpdateClient(QObject):
    checked = Signal(object)
    progress = Signal(int, int)
    downloaded = Signal(object)
    failed = Signal(str)

    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.version = version
        self.manager = QNetworkAccessManager(self)
        self.reply = None
        self.download = None
        self.metadata = bytearray()
        self.redirects_left = 0

    def check(self):
        self.request(LATEST_RELEASE)

    def start_download(self, release):
        try:
            self.download = InstallerDownload(release)
        except OSError:
            self.failed.emit("ساخت فایل موقت برای دانلود ممکن نشد.")
            return
        self.redirects_left = 5
        self.request(release.url)

    def request(self, url):
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", f"PersianTypoFixer/{self.version}".encode("ascii"))
        request.setRawHeader(b"Cache-Control", b"no-cache, no-store")
        request.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
        request.setTransferTimeout(20000)
        request.setMaximumRedirectsAllowed(5)
        if self.download:
            request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)
        else:
            request.setRawHeader(b"Accept", b"application/vnd.github+json")
            request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.SameOriginRedirectPolicy)
        reply = self.reply = self.manager.get(request)
        reply.setReadBufferSize(CHUNK)
        reply.readyRead.connect(self.read)
        reply.finished.connect(self.finish)

    def read(self):
        self.drain(self.sender())

    def drain(self, reply):
        if reply is not self.reply:
            return
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            reply.readAll()
            return
        try:
            while reply.bytesAvailable():
                data = bytes(reply.read(CHUNK))
                if not data:
                    break
                if self.download:
                    self.download.write(data)
                else:
                    self.metadata.extend(data)
                    if len(self.metadata) > MAX_METADATA:
                        raise ValueError("Release metadata too large")
        except (OSError, ValueError):
            self.fail("خواندن پاسخ یا ذخیرهٔ فایل به‌روزرسانی ممکن نشد.")
            return
        if self.download:
            self.progress.emit(self.download.received, self.download.release.size)

    def finish(self):
        reply = self.sender()
        if reply is not self.reply:
            return
        redirect = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
        if self.download and redirect and reply.error() == QNetworkReply.NoError:
            url = reply.url().resolved(redirect)
            if (self.redirects_left and url.scheme() == "https" and url.host() in DOWNLOAD_HOSTS
                    and url.port(443) == 443 and not url.userInfo()):
                self.redirects_left -= 1
                reply.deleteLater()
                self.request(url)
            else:
                self.fail("آدرس دانلود GitHub معتبر نیست.")
            return
        if reply.error() != QNetworkReply.NoError or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            self.fail("ارتباط با GitHub برقرار نشد. بعداً دوباره امتحان کنید.")
            return
        self.drain(reply)
        if reply is not self.reply:  # Reading or a progress callback may have cancelled the transfer.
            return
        self.reply = None
        reply.deleteLater()
        try:
            if self.download:
                self.download.verify()
                download, self.download = self.download, None
                self.downloaded.emit(download)
            else:
                release = parse_release(json.loads(self.metadata), self.version, sys.platform)
                self.metadata.clear()
                self.checked.emit(release)
        except (OSError, ValueError, RecursionError):
            self.fail("اطلاعات انتشار یا صحت فایل نصاب تأیید نشد.")

    def cancel(self):
        reply, self.reply = self.reply, None
        if reply:
            reply.abort()
            reply.deleteLater()
        if self.download:
            download, self.download = self.download, None
            download.remove()
        self.metadata.clear()

    def fail(self, message):
        self.cancel()
        self.failed.emit(message)
