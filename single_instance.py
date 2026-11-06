"""Keep logon and manual launches from creating duplicate tray icons."""

import ctypes
from ctypes import wintypes


class SingleInstance:
    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.CreateMutexW.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.CreateMutexW(None, False, r"Local\PersianTypoFixer.Singleton")
        error = ctypes.get_last_error()
        if not self.handle:
            raise ctypes.WinError(error)
        self.already_running = error == 183

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
