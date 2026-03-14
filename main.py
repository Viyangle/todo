import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

from app.data.storage import TodoStorage
from app.ui.main_window import MainWindow

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_SPACE = 0x20
HOTKEY_ID = 1


class WinHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):  # type: ignore[override]
        if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return False, 0


class GlobalHotkey:
    def __init__(self, window: MainWindow) -> None:
        self.window = window
        self._registered = False
        self._filter = WinHotkeyFilter(self.window.toggle_visibility)

    def install(self, app: QApplication) -> None:
        app.installNativeEventFilter(self._filter)
        hwnd = int(self.window.winId())
        user32 = ctypes.windll.user32
        self._registered = bool(user32.RegisterHotKey(hwnd, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_SPACE))

    def uninstall(self, app: QApplication) -> None:
        if self._registered:
            ctypes.windll.user32.UnregisterHotKey(int(self.window.winId()), HOTKEY_ID)
        app.removeNativeEventFilter(self._filter)



def main() -> int:
    app = QApplication(sys.argv)
    storage = TodoStorage()
    window = MainWindow(storage)
    window.show()

    hotkey = GlobalHotkey(window)
    hotkey.install(app)
    app.aboutToQuit.connect(lambda: hotkey.uninstall(app))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())


