"""Exercise the Wayland client on an isolated D-Bus with a simulated portal."""

import asyncio
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

if not sys.platform.startswith("linux") or not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
    raise unittest.SkipTest("Requires an isolated Linux session bus")

from dbus_next import Message, MessageType, Variant
from dbus_next.aio import MessageBus

from shortcut import DEFAULT_SHORTCUT
from wayland_portal import PATH, PREFIX, SERVICE, TEXT_TYPES, WaylandPortal


class FakePortal:
    def __init__(self, bus):
        self.bus = bus
        self.sessions = {}
        self.client = None
        self.clipboard = {TEXT_TYPES[0]: b"Original", "text/html": b"<b>Original</b>"}
        self.paste = b""
        self.keep_newer = False
        self.read_pipe = None
        self.calls = []

    def signal(self, interface, member, signature, body, path=PATH):
        self.bus.send(Message(
            destination=self.client, path=path, interface=PREFIX + interface,
            message_type=MessageType.SIGNAL, member=member, signature=signature, body=body,
        ))

    def selection(self, owned, formats):
        self.signal("Clipboard", "SelectionOwnerChanged", "oa{sv}", [
            self.sessions[PREFIX + "RemoteDesktop"],
            {"session_is_owner": Variant("b", owned), "mime_types": Variant("as", list(formats))},
        ])

    def handle(self, message):
        if message.message_type != MessageType.METHOD_CALL:
            return None
        self.client = message.sender
        self.calls.append(message.member)
        member, args = message.member, message.body
        if member == "Register":
            assert message.path == PATH and args[0] == "ir.ghotbani.persiantypefixer"
        elif member in ("CreateSession", "BindShortcuts", "SelectDevices", "Start"):
            sender = self.client[1:].replace(".", "_")
            options = args[-1]
            request = f"{PATH}/request/{sender}/{options['handle_token'].value}"
            data = {}
            if member == "CreateSession":
                session = f"{PATH}/session/{sender}/{options['session_handle_token'].value}"
                self.sessions[message.interface] = session
                data["session_handle"] = Variant("s", session)
            elif member == "BindShortcuts":
                self.trigger = args[1][0][1]["preferred_trigger"].value
                data["shortcuts"] = Variant("a(sa{sv})", [
                    ["correct", {"trigger_description": Variant("s", self.trigger)}],
                ])
            elif member == "Start":
                self.selection(False, self.clipboard)
                data = {"devices": Variant("u", 1), "clipboard_enabled": Variant("b", True),
                        "restore_token": Variant("s", "fixture")}
            self.signal("Request", "Response", "ua{sv}", [0, data], request)
            return Message.new_method_return(message, "o", [request])
        elif member == "NotifyKeyboardKeycode" and args[3] == 0:
            if args[2] == 46:  # KEY_C
                self.clipboard = {TEXT_TYPES[0]: b"sghl"}
                self.selection(False, self.clipboard)
            elif args[2] == 47:  # KEY_V
                self.signal("Clipboard", "SelectionTransfer", "osu", [args[0], TEXT_TYPES[0], 1])
        elif member == "SelectionRead":
            read_end, write_end = os.pipe()
            try:
                os.write(write_end, self.clipboard[args[1]])
            finally:
                os.close(write_end)
            asyncio.get_running_loop().call_later(0.1, os.close, read_end)
            return Message.new_method_return(message, "h", [0], unix_fds=[read_end])
        elif member == "SetSelection":
            self.selection(True, args[1]["mime_types"].value)
        elif member == "SelectionWrite":
            self.read_pipe, write_end = os.pipe()
            asyncio.get_running_loop().call_later(0.1, os.close, write_end)
            return Message.new_method_return(message, "h", [0], unix_fds=[write_end])
        elif member == "SelectionWriteDone":
            assert args[2]
            self.paste = os.read(self.read_pipe, 1024)
            os.close(self.read_pipe)
            self.read_pipe = None
            if self.keep_newer:
                self.clipboard = {TEXT_TYPES[0]: b"New clipboard contents"}
                self.selection(False, self.clipboard)
        return Message.new_method_return(message)


class WaylandPortalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bus = await MessageBus(negotiate_unix_fd=True).connect()
        self.fake = FakePortal(self.bus)
        self.bus.add_message_handler(self.fake.handle)
        await self.bus.request_name(SERVICE)
        self.events = SimpleNamespace(**{name: Mock() for name in (
            "activated", "ready_changed", "status_changed", "token_changed", "trigger_changed",
        )})
        self.portal = WaylandPortal(self.events)
        await self.portal.enable(DEFAULT_SHORTCUT)

    async def asyncTearDown(self):
        await self.portal.close()
        self.bus.disconnect()
        await self.bus.wait_for_disconnect()

    async def test_release_activation_converts_and_restores_all_formats(self):
        self.assertEqual(self.fake.trigger, "CTRL+ALT+x")
        arguments = [self.portal.shortcut_session, "correct", 1, {}]
        self.fake.signal("GlobalShortcuts", "Activated", "osta{sv}", arguments)
        await asyncio.sleep(0.05)
        self.events.activated.emit.assert_not_called()
        self.fake.signal("GlobalShortcuts", "Deactivated", "osta{sv}", arguments)
        await asyncio.sleep(0.05)
        self.events.activated.emit.assert_called_once()
        original = self.fake.clipboard.copy()
        await self.portal.convert("")
        self.events.token_changed.emit.assert_called_once_with("fixture")
        self.assertNotIn("NotifyKeyboardKeycode", self.fake.calls)
        await self.portal.convert("fixture")
        self.assertEqual(self.fake.paste.decode("utf-8"), "سلام")
        self.assertEqual(self.portal.payload, original)
        await self.portal.disable()
        self.assertFalse(self.portal.enabled)
        self.assertIn("Close", self.fake.calls)

    async def test_newer_clipboard_survives_conversion(self):
        self.fake.keep_newer = True
        await self.portal.convert("")
        await self.portal.convert("fixture")
        self.assertEqual(self.fake.paste.decode("utf-8"), "سلام")
        self.assertFalse(self.portal.owned)
        self.assertEqual(self.fake.calls.count("SetSelection"), 1)
