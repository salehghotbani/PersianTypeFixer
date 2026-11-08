import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest

from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QNetworkProxy

from update_download import REPO, Release, UpdateClient, parse_release


INSTALLER = b"test installer bytes" * 8000
DIGEST = hashlib.sha256(INSTALLER).hexdigest()


class ReleaseTests(unittest.TestCase):
    def test_selects_newer_stable_release_and_verifiable_setup(self):
        filename = "PersianTypoFixer-v1.10.0-windows-x64-setup.exe"
        url = f"https://github.com/{REPO}/releases/download/v1.10.0/{filename}"
        asset = {
            "name": filename, "browser_download_url": url, "state": "uploaded",
            "size": len(INSTALLER), "digest": f"sha256:{DIGEST}",
        }
        metadata = {"tag_name": "v1.10.0", "body": "Release notes", "assets": [asset]}
        self.assertEqual(parse_release(metadata, "1.9.0"),
                         Release("1.10.0", "Release notes", url, len(INSTALLER), DIGEST))
        self.assertIsNone(parse_release(metadata, "1.10.0"))
        self.assertIsNone(parse_release(dict(metadata, prerelease=True), "1.9.0"))
        for invalid in (dict(asset, browser_download_url="https://example.com/setup.exe"),
                        dict(asset, digest=None), dict(asset, size=0)):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_release(dict(metadata, assets=[invalid]), "1.9.0")


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/setup.exe")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(INSTALLER)))
        self.end_headers()
        if self.path == "/slow":
            self.wfile.write(INSTALLER[:65536])
            self.server.release_slow.wait(5)
        else:
            self.wfile.write(INSTALLER)

    def log_message(self, *_):
        pass


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.server.release_slow = threading.Event()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.release_slow.set()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.client = UpdateClient("1.1.1")
        self.client.manager.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        self.completed = []
        self.errors = []
        self.progress = []
        self.client.downloaded.connect(self.completed.append)
        self.client.failed.connect(self.errors.append)
        self.client.progress.connect(lambda received, total: self.progress.append(received))

    def tearDown(self):
        self.client.cancel()
        for download in self.completed:
            download.remove()

    def release(self, path, digest=DIGEST):
        url = f"http://127.0.0.1:{self.server.server_port}{path}"
        return Release("1.2.0", "", url, len(INSTALLER), digest)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 5
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertTrue(predicate(), self.errors)

    def test_cancel_removes_partial_download_and_allows_retry(self):
        self.client.start_download(self.release("/slow"))
        directory = self.client.download.path.parent
        self.wait_for(lambda: any(self.progress))
        self.assertTrue(directory.exists())
        self.client.cancel()
        self.assertFalse(directory.exists())
        self.assertIsNone(self.client.reply)
        self.server.release_slow.set()
        self.client.start_download(self.release("/setup.exe"))
        self.wait_for(lambda: self.completed or self.errors)
        self.assertEqual(len(self.completed), 1, self.errors)
        self.assertEqual(self.completed[0].path.read_bytes(), INSTALLER)
        self.assertEqual(self.errors, [])

    def test_bad_digest_and_untrusted_redirect_never_reach_installer(self):
        for release in (self.release("/setup.exe", "0" * 64), self.release("/redirect")):
            with self.subTest(release=release):
                self.errors.clear()
                self.client.start_download(release)
                directory = self.client.download.path.parent
                self.wait_for(lambda: self.errors)
                self.assertEqual(self.completed, [])
                self.assertFalse(directory.exists())
