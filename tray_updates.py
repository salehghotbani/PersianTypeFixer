"""Tray update notifications, release notes, and cancellable download UI."""

import base64
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QDialog

from app_version import PROJECT_URL, VERSION
from update_dialogs import DownloadDialog, release_dialog, show_update_message

CHECK_INTERVAL = 24 * 60 * 60 * 1000
INITIAL_CHECK_DELAY = 2 * 60 * 1000
BUSY_RETRY_DELAY = 60 * 1000
CHECK_LABEL = "بررسی به‌روزرسانی"


def launch_installer(path, autostart):
    # Wait outside the running app so Setup can replace its EXE and Qt DLLs.
    frozen = getattr(sys, "frozen", False)
    data = {
        "owner": os.getpid(), "setup": str(path),
        "tasks": "/MERGETASKS=autostart" if autostart else "/MERGETASKS=!autostart",
        "restart": sys.executable if frozen else "",
    }
    payload = base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii")
    script_path = Path(__file__).with_name("packaging") / "install_update.ps1"
    script = (
        "$update = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"
        + payload + "')) | ConvertFrom-Json\n" + script_path.read_text(encoding="utf-8-sig")
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if frozen:
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    try:
        subprocess.Popen(
            [str(powershell), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1"),
        )
    finally:
        if frozen:
            ctypes.windll.kernel32.SetDllDirectoryW(ctypes.c_wchar_p(sys._MEIPASS))


class TrayUpdates(QObject):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.client = None
        self.release = None
        self.manual = False
        self.details_dialog = None
        self.progress_dialog = None
        self.action = QAction(CHECK_LABEL, self)
        self.action.triggered.connect(lambda: self.check(manual=True))
        self.available_action = QAction(self)
        self.available_action.setVisible(False)
        self.available_action.triggered.connect(self.show_details)
        exit_action = controller.menu.actions()[-1]
        controller.menu.insertAction(exit_action, self.action)
        controller.menu.insertAction(exit_action, self.available_action)
        controller.tray.messageClicked.connect(self.show_details)
        self.timer = QTimer(self, interval=CHECK_INTERVAL)
        self.timer.timeout.connect(self.check)
        self.timer.start()
        self.initial_check = QTimer(self, interval=INITIAL_CHECK_DELAY, singleShot=True)
        self.initial_check.timeout.connect(self.check)
        self.initial_check.start()

    def start_client(self):
        from update_download import UpdateClient

        client = self.client = UpdateClient(VERSION, self)
        client.checked.connect(self.checked)
        client.failed.connect(self.failed)
        client.progress.connect(self.progress)
        client.downloaded.connect(self.install)
        return client

    def stop_client(self):
        if self.client is not None:
            client, self.client = self.client, None
            client.cancel()
            client.deleteLater()

    def check(self, manual=False):
        if self.controller.quitting:
            return
        if self.client is not None or self.details_dialog or self.progress_dialog:
            if not manual:
                self.initial_check.start(BUSY_RETRY_DELAY)
            elif self.details_dialog:
                self.show_details()
            return
        self.initial_check.stop()
        self.manual = manual
        self.action.setEnabled(False)
        self.action.setText("در حال بررسی به‌روزرسانی…")
        self.start_client().check()

    def restore_action(self):
        self.action.setText(CHECK_LABEL)
        self.action.setEnabled(True)
        self.available_action.setVisible(self.release is not None)
        if self.release:
            self.available_action.setText(f"به‌روزرسانی به نسخهٔ {self.release.version}")

    def checked(self, release):
        self.stop_client()
        self.release = release
        self.restore_action()
        if self.manual:
            if release:
                self.show_details()
            else:
                show_update_message("نسخهٔ نصب‌شده به‌روز است.")
        elif release:
            self.controller.tray.showMessage(
                "به‌روزرسانی Persian Typo Fixer",
                f"نسخهٔ {release.version} منتشر شده است. برای دیدن تغییرات کلیک کنید.",
            )

    def show_details(self):
        if not self.release or self.client is not None or self.progress_dialog or self.controller.quitting:
            return
        if not self.details_dialog:
            dialog = self.details_dialog = release_dialog(self.release, linux=sys.platform.startswith("linux"))
            dialog.finished.connect(self.details_closed)
        self.details_dialog.show()
        self.details_dialog.raise_()
        self.details_dialog.activateWindow()

    def details_closed(self, result):
        self.details_dialog = None
        if result == QDialog.Accepted and not self.controller.quitting:
            if sys.platform.startswith("linux"):
                QDesktopServices.openUrl(QUrl(f"{PROJECT_URL}/releases/tag/v{self.release.version}"))
            else:
                self.download()

    def download(self):
        self.action.setEnabled(False)
        self.action.setText("در حال دانلود به‌روزرسانی…")
        self.available_action.setVisible(False)
        dialog = self.progress_dialog = DownloadDialog(self.release)
        dialog.rejected.connect(self.cancel_download)
        dialog.show()
        self.start_client().start_download(self.release)

    def progress(self, received, total):
        if self.progress_dialog:
            self.progress_dialog.set_progress(received, total)

    def close_progress(self):
        if self.progress_dialog:
            dialog, self.progress_dialog = self.progress_dialog, None
            dialog.hide()
            dialog.deleteLater()

    def cancel_download(self):
        self.stop_client()
        self.close_progress()
        self.restore_action()

    def failed(self, message):
        self.stop_client()
        report = self.manual or self.progress_dialog is not None
        self.close_progress()
        self.restore_action()
        if report:
            show_update_message(message, warning=True)

    def install(self, download):
        self.stop_client()
        self.close_progress()
        try:
            launch_installer(download.path, self.controller.startup.is_enabled())
        except (OSError, KeyError):
            download.remove()
            self.restore_action()
            show_update_message("اجرای نصاب ممکن نشد. دوباره امتحان کنید.", warning=True)
            return
        # The installer helper now owns this directory and removes it after Setup exits.
        download.directory.setAutoRemove(False)
        self.controller.exit_application()

    def stop(self):
        self.initial_check.stop()
        self.timer.stop()
        self.stop_client()
        self.close_progress()
        if self.details_dialog:
            self.details_dialog.reject()
