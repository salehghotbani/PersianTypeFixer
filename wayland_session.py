"""Run the Wayland portal connection without blocking the Qt event loop."""

import asyncio
from threading import Thread

from PySide6.QtCore import QObject, QSettings, Signal, Slot

from wayland_portal import WaylandPortal


class WaylandSession(QObject):
    ready_changed = Signal(bool, str)
    status_changed = Signal(str)
    trigger_changed = Signal(str)
    token_changed = Signal(str)
    activated = Signal()
    finished = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings: QSettings = settings
        self.busy = False
        self.closed = False
        self.loop = asyncio.new_event_loop()
        self.portal = WaylandPortal(self)
        self.thread = Thread(target=self.run, name="desktop-portal", daemon=True)
        self.thread.start()
        self.token_changed.connect(self.store_token)
        self.activated.connect(self.convert_selection)
        self.finished.connect(self.conversion_finished)

    def run(self):
        self.loop.run_forever()
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
        if pending:
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.close()

    def submit(self, operation):
        asyncio.run_coroutine_threadsafe(operation, self.loop)

    def set_enabled(self, enabled, shortcut):
        if enabled:
            self.submit(self.enable(shortcut))
        else:
            self.submit(self.portal.disable())

    async def enable(self, shortcut):
        try:
            await self.portal.enable(shortcut)
        except Exception as error:
            self.ready_changed.emit(False, f"فعال کردن میان‌بر Wayland ممکن نشد: {error}")

    def configure_shortcuts(self):
        self.submit(self.configure())

    async def configure(self):
        try:
            await self.portal.configure()
        except Exception as error:
            self.status_changed.emit(f"باز کردن تنظیمات میان‌بر ممکن نشد: {error}")

    @Slot()
    def convert_selection(self):
        if self.busy or self.closed:
            return
        self.busy = True
        self.submit(self.convert(self.settings.value("waylandRestoreToken", "", type=str)))

    async def convert(self, token):
        try:
            await self.portal.convert(token)
        except Exception as error:
            self.status_changed.emit(f"اصلاح متن ممکن نشد: {error or 'پاسخ Wayland در مهلت مقرر نرسید.'}")
        finally:
            self.finished.emit()

    @Slot(str)
    def store_token(self, token):
        self.settings.setValue("waylandRestoreToken", token)

    @Slot()
    def conversion_finished(self):
        self.busy = False

    def close(self):
        self.closed = True
        future = asyncio.run_coroutine_threadsafe(self.portal.close(), self.loop)
        try:
            future.result(timeout=2)
        except TimeoutError:
            future.cancel()
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=2)
