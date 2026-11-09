"""Wayland shortcuts and clipboard conversion through XDG Desktop Portal."""

import asyncio
import os
import uuid

from dbus_next import Message, MessageType, Variant
from dbus_next.aio import MessageBus

from layout_conversion import convert_text
from linux_layouts import standard_mapping
from linux_session import DESKTOP_ID
from shortcut import MODIFIERS

SERVICE = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"
PREFIX = "org.freedesktop.portal."
KEYBOARD = 1
TEXT_TYPES = ("text/plain;charset=utf-8", "UTF8_STRING", "text/plain")
MAX_CLIPBOARD = 16 * 1024 * 1024


class PortalError(OSError):
    pass


def option(options, name, default=None):
    return options[name].value if name in options else default


async def wait_fd(fd, write=False):
    loop = asyncio.get_running_loop()
    ready = asyncio.Event()
    add = loop.add_writer if write else loop.add_reader
    remove = loop.remove_writer if write else loop.remove_reader
    add(fd, ready.set)
    try:
        await ready.wait()
    finally:
        remove(fd)


async def read_fd(fd, limit):
    data = bytearray()
    try:
        os.set_blocking(fd, False)
        async with asyncio.timeout(2):
            while True:
                try:
                    chunk = os.read(fd, min(65536, limit - len(data) + 1))
                except BlockingIOError:
                    await wait_fd(fd)
                    continue
                if not chunk:
                    return bytes(data)
                data.extend(chunk)
                if len(data) > limit:
                    raise PortalError("محتوای Clipboard برای پشتیبان‌گیری بیش از حد بزرگ است.")
    finally:
        os.close(fd)


async def write_fd(fd, data):
    try:
        os.set_blocking(fd, False)
        pending = memoryview(data)
        async with asyncio.timeout(2):
            while pending:
                try:
                    pending = pending[os.write(fd, pending):]
                except BlockingIOError:
                    await wait_fd(fd, write=True)
    finally:
        os.close(fd)


class WaylandPortal:
    def __init__(self, events):
        self.events = events
        self.bus = None
        self.owner = None
        self.requests = {}
        self.shortcut_session = None
        self.input_session = None
        self.enabled = False
        self.armed = False
        self.conversion = None
        self.formats = None
        self.generation = 0
        self.owned = False
        self.payload = {}
        self.clipboard_changed = asyncio.Event()
        self.selection_served = asyncio.Event()
        self.setup_lock = asyncio.Lock()
        self.mapping, keys = standard_mapping()
        self.keys = {letter: key[2] - 8 for letter, key in keys.items()}

    async def call(self, interface, method, signature="", body=(), *, path=PATH, destination=SERVICE):
        reply = await asyncio.wait_for(self.bus.call(Message(
            destination=destination, path=path, interface=interface, member=method,
            signature=signature, body=list(body),
        )), 5)
        if reply.message_type == MessageType.ERROR:
            raise PortalError(f"{method}: {reply.error_name}")
        return reply

    async def connect(self):
        if self.owner:
            return
        self.bus = await MessageBus(negotiate_unix_fd=True).connect()
        self.bus.add_message_handler(self.on_signal)
        try:
            try:
                await self.call("org.freedesktop.host.portal.Registry", "Register", "sa{sv}", [DESKTOP_ID, {}])
            except PortalError as error:
                if str(error) != "Register: org.freedesktop.DBus.Error.UnknownMethod":
                    raise
            dbus = "org.freedesktop.DBus"
            params = {"path": "/org/freedesktop/DBus", "destination": dbus}
            self.owner = (await self.call(dbus, "GetNameOwner", "s", [SERVICE], **params)).body[0]
            await self.call(dbus, "AddMatch", "s", [
                f"type='signal',sender='{SERVICE}',path_namespace='{PATH}'",
            ], **params)
        except BaseException:
            self.owner = None
            self.bus.disconnect()
            self.bus = None
            raise

    async def request(self, interface, method, signature, args, options=None):
        token = "ptf_" + uuid.uuid4().hex
        sender = self.bus.unique_name[1:].replace(".", "_")
        path = f"{PATH}/request/{sender}/{token}"
        result = self.requests[path] = asyncio.get_running_loop().create_future()
        try:
            reply = await self.call(PREFIX + interface, method, signature,
                                    [*args, {**(options or {}), "handle_token": Variant("s", token)}])
            if reply.body != [path]:
                raise PortalError("Portal request path did not match")
            code, data = await asyncio.wait_for(result, 120)
            if code != 0:
                raise PortalError("درخواست دسترسی در محیط دسکتاپ تأیید نشد.")
            return data
        except (asyncio.CancelledError, TimeoutError):
            try:
                await self.call(PREFIX + "Request", "Close", path=path)
            except (OSError, TimeoutError):
                pass
            raise
        finally:
            self.requests.pop(path, None)

    async def create_session(self, interface):
        result = await self.request(interface, "CreateSession", "a{sv}", [], {
            "session_handle_token": Variant("s", "ptf_" + uuid.uuid4().hex),
        })
        return result["session_handle"].value

    async def enable(self, shortcut):
        async with self.setup_lock:
            if self.enabled:
                return
            await self.connect()
            if not self.shortcut_session:
                session = await self.create_session("GlobalShortcuts")
                trigger = "+".join([*(key.upper() for key in MODIFIERS if key in shortcut.modifiers),
                                    shortcut.letter.lower()])
                try:
                    result = await self.request("GlobalShortcuts", "BindShortcuts", "oa(sa{sv})sa{sv}", [
                        session, [["correct", {"description": Variant("s", "اصلاح متن انتخاب‌شده"),
                                               "preferred_trigger": Variant("s", trigger)}]], "",
                    ])
                    if not any(item[0] == "correct" for item in option(result, "shortcuts", [])):
                        raise PortalError("میان‌بر در تنظیمات محیط دسکتاپ ثبت نشد.")
                except BaseException:
                    await self.close_session(session)
                    raise
                self.shortcut_session = session
                self.report_trigger(option(result, "shortcuts", []))
            self.enabled = True
            self.events.ready_changed.emit(True, "وضعیت: فعال")

    async def configure(self):
        if not self.shortcut_session:
            raise PortalError("ابتدا میان‌بر را از منوی برنامه فعال کنید.")
        await self.call(PREFIX + "GlobalShortcuts", "ConfigureShortcuts", "osa{sv}",
                        [self.shortcut_session, "", {}])

    async def disable(self):
        self.enabled = self.armed = False
        session, self.shortcut_session = self.shortcut_session, None
        if session:
            await self.close_session(session)
        self.events.ready_changed.emit(False, "وضعیت: غیرفعال")

    async def authorize_input(self, token):
        session = await self.create_session("RemoteDesktop")
        options = {"types": Variant("u", KEYBOARD), "persist_mode": Variant("u", 2)}
        if token:
            options["restore_token"] = Variant("s", token)
        self.input_session = session
        self.formats = None
        try:
            await self.request("RemoteDesktop", "SelectDevices", "oa{sv}", [session], options)
            await self.call(PREFIX + "Clipboard", "RequestClipboard", "oa{sv}", [session, {}])
            result = await self.request("RemoteDesktop", "Start", "osa{sv}", [session, ""])
            if not (option(result, "devices", 0) & KEYBOARD and option(result, "clipboard_enabled", False)):
                raise PortalError("دسترسی صفحه‌کلید و Clipboard لازم است.")
            if self.formats is None:
                self.formats = []
            self.events.token_changed.emit(option(result, "restore_token", ""))
        except BaseException:
            self.input_session = None
            await self.close_session(session)
            raise

    async def close_session(self, session):
        try:
            await self.call(PREFIX + "Session", "Close", path=session)
        except (OSError, TimeoutError):
            pass

    def report_trigger(self, shortcuts):
        for identifier, props in shortcuts:
            if identifier == "correct":
                self.events.trigger_changed.emit(option(props, "trigger_description", ""))

    def on_signal(self, msg):
        if msg.message_type != MessageType.SIGNAL or msg.sender != self.owner:
            return
        if msg.interface == PREFIX + "Request" and msg.member == "Response":
            future = self.requests.get(msg.path)
            if future and not future.done():
                future.set_result(msg.body)
        if msg.interface == PREFIX + "Session" and msg.member == "Closed":
            if msg.path == self.shortcut_session:
                self.shortcut_session = None
                self.enabled = self.armed = False
                self.events.ready_changed.emit(False, "دسترسی میان‌بر بسته شد.")
            if msg.path == self.input_session:
                self.input_session = None
                self.formats = None
                self.payload = {}
        if not msg.body:
            return
        if msg.interface == PREFIX + "GlobalShortcuts" and msg.body[0] == self.shortcut_session:
            if msg.member == "ShortcutsChanged":
                self.report_trigger(msg.body[1])
            elif self.enabled and msg.body[1] == "correct":
                if msg.member == "Activated" and not self.conversion:
                    self.armed = True
                elif msg.member == "Deactivated" and self.armed:
                    self.armed = False
                    self.events.activated.emit()
        if msg.interface == PREFIX + "Clipboard" and msg.body[0] == self.input_session:
            if msg.member == "SelectionOwnerChanged":
                options = msg.body[1]
                self.formats = option(options, "mime_types", [])
                self.owned = option(options, "session_is_owner", False)
                self.generation += 1
                self.clipboard_changed.set()
                if not self.owned:
                    self.payload = {}
            elif msg.member == "SelectionTransfer":
                asyncio.create_task(self.transfer(msg.body[0], msg.body[1], msg.body[2]))

    async def transfer(self, session, mime, serial):
        success = False
        try:
            data = self.payload.get(mime)
            if data is not None:
                reply = await self.call(PREFIX + "Clipboard", "SelectionWrite", "ou", [session, serial])
                await write_fd(reply.unix_fds[reply.body[0]], data)
                success = True
                self.selection_served.set()
        except (OSError, TimeoutError):
            pass
        try:
            await self.call(PREFIX + "Clipboard", "SelectionWriteDone", "oub", [session, serial, success])
        except (OSError, TimeoutError):
            pass

    async def read(self, mime, limit):
        if self.owned:
            return self.payload[mime]
        reply = await self.call(PREFIX + "Clipboard", "SelectionRead", "os", [self.input_session, mime])
        return await read_fd(reply.unix_fds[reply.body[0]], limit)

    async def set_clipboard(self, data):
        generation = self.generation
        self.payload = data
        await self.call(PREFIX + "Clipboard", "SetSelection", "oa{sv}", [
            self.input_session, {"mime_types": Variant("as", list(data))},
        ])
        await self.wait_clipboard(generation)
        if data and not self.owned:
            raise PortalError("محتوای Clipboard تغییر کرد.")

    async def wait_clipboard(self, generation):
        async with asyncio.timeout(2):
            while self.generation == generation:
                self.clipboard_changed.clear()
                await self.clipboard_changed.wait()

    async def send_keys(self, modifier, key):
        session = self.input_session
        pressed = []
        try:
            for code in (modifier, key):
                pressed.append(code)
                await self.call(PREFIX + "RemoteDesktop", "NotifyKeyboardKeycode", "oa{sv}iu",
                                [session, {}, code, 1])
        finally:
            for code in reversed(pressed):
                try:
                    await self.call(PREFIX + "RemoteDesktop", "NotifyKeyboardKeycode", "oa{sv}iu",
                                    [session, {}, code, 0])
                except (OSError, TimeoutError):
                    await self.close_session(session)
                    raise

    async def convert(self, token):
        if self.conversion or not self.enabled:
            return
        self.conversion = asyncio.current_task()
        try:
            if not self.input_session:
                await self.authorize_input(token)
                self.events.status_changed.emit("دسترسی فعال شد. متن را انتخاب کنید و دوباره میان‌بر را بزنید.")
                return
            await self.correct_selection()
        finally:
            self.conversion = None

    async def correct_selection(self):
        if self.formats is None:
            raise PortalError("وضعیت Clipboard مشخص نیست. یک بار چیزی کپی کنید و دوباره تلاش کنید.")
        if len(self.formats) > 32:
            raise PortalError("Clipboard قالب‌های بیش از حد زیادی دارد.")
        original = {}
        remaining = MAX_CLIPBOARD
        generation = self.generation
        async with asyncio.timeout(3):
            for mime in self.formats:
                original[mime] = await self.read(mime, remaining)
                remaining -= len(original[mime])
                if self.generation != generation:
                    raise PortalError("محتوای Clipboard تغییر کرد.")
        restore_generation = None
        try:
            # The portal reports release of the shortcut key before the user
            # necessarily releases its modifiers.
            await asyncio.sleep(0.15)
            if not self.enabled or self.generation != generation:
                return
            await self.send_keys(29, self.keys["c"])
            await self.wait_clipboard(generation)
            restore_generation = self.generation
            mime = next((item for item in TEXT_TYPES if item in self.formats), None)
            if not mime or self.owned:
                raise PortalError("متن انتخاب‌شده دریافت نشد.")
            text = (await self.read(mime, MAX_CLIPBOARD)).decode("utf-8")
            corrected = convert_text(text, self.mapping)
            if self.generation != restore_generation or not self.enabled or corrected == text:
                return
            await self.set_clipboard({mime: corrected.encode("utf-8") for mime in TEXT_TYPES})
            restore_generation = self.generation
            if self.enabled:
                self.selection_served.clear()
                await self.send_keys(29, self.keys["v"])
                await asyncio.wait_for(self.selection_served.wait(), 1.5)
                await asyncio.sleep(0.25)
                self.events.status_changed.emit("متن اصلاح شد.")
        finally:
            if self.input_session and self.generation == restore_generation:
                await self.set_clipboard(original)

    async def close(self):
        self.enabled = False
        if self.conversion:
            self.conversion.cancel()
            await asyncio.gather(self.conversion, return_exceptions=True)
        if self.bus:
            self.bus.disconnect()
