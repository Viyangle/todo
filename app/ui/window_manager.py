from __future__ import annotations

from PySide6.QtCore import QPoint, QSize
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget


class WindowManager:
    def __init__(self, window) -> None:
        self.window = window

    def load_default_size(self) -> QSize:
        saved_size = self.window.settings.value("prefs/default_size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            width = max(self.window._minimum_size.width(), saved_size.width())
            height = max(self.window._minimum_size.height(), saved_size.height())
            return QSize(width, height)
        return QSize(self.window._fallback_default_size)

    def load_due_warning_minutes(self) -> int:
        saved_value = self.window.settings.value("prefs/warn_minutes", 120)
        try:
            minutes = int(saved_value)
        except (TypeError, ValueError):
            minutes = 120
        return max(10, minutes)

    def setup_tray(self) -> None:
        self.window.tray_icon = QSystemTrayIcon(self.window)
        icon = self.window.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self.window.tray_icon.setIcon(icon)
        self.window.setWindowIcon(icon)

        tray_menu = QMenu(self.window)
        show_action = tray_menu.addAction("Show / Hide")
        show_action.triggered.connect(self.toggle_visibility)

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.window.tray_icon.setContextMenu(tray_menu)
        self.window.tray_icon.activated.connect(self.on_tray_activated)
        self.window.tray_icon.show()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
            QSystemTrayIcon.MiddleClick,
        ):
            self.toggle_visibility()

    def hide_to_tray(self) -> None:
        self.window.hide()

    def toggle_visibility(self) -> None:
        if self.window.isVisible():
            self.window.hide()
            return

        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def restore_default_size(self) -> None:
        self.window.resize(self.window._default_size)

    def set_current_page(self, page: QWidget) -> None:
        if self.window._current_page is page:
            return

        self.window._current_page.hide()
        page.show()
        self.window._current_page = page

    def show_settings_page(self) -> None:
        self.window.default_width_spin.setValue(self.window._default_size.width())
        self.window.default_height_spin.setValue(self.window._default_size.height())
        self.window.warn_minutes_spin.setValue(self.window._due_soon_minutes)
        ai_config = self.window._load_ai_config()
        self.window.ai_api_key_edit.setText(ai_config.api_key)
        self.window.ai_base_url_edit.setText(ai_config.base_url)
        self.window.ai_model_edit.setText(ai_config.model_name)
        self.set_current_page(self.window.settings_page)

    def show_tarot_page(self) -> None:
        self.set_current_page(self.window.tarot_page)
        self.window._refresh_tarot_history()

    def show_tarot_history_page(self) -> None:
        self.window._refresh_tarot_history()
        self.set_current_page(self.window.tarot_history_page)

    def show_main_page(self) -> None:
        self.set_current_page(self.window.main_page)

    def save_settings(self) -> None:
        self.window._default_size = QSize(
            self.window.default_width_spin.value(),
            self.window.default_height_spin.value(),
        )
        self.window._due_soon_minutes = self.window.warn_minutes_spin.value()
        ai_config = self.window._build_ai_config_from_inputs()
        self.window.settings.setValue("prefs/default_size", self.window._default_size)
        self.window.settings.setValue("prefs/warn_minutes", self.window._due_soon_minutes)
        self.window.settings.setValue("ai/api_key", ai_config.api_key)
        self.window.settings.setValue("ai/base_url", ai_config.base_url)
        self.window.settings.setValue("ai/model_name", ai_config.model_name)
        self.window._apply_ai_config(ai_config)
        self.show_main_page()
        self.window._refresh_list(keep_scroll=True)

    def save_current_size_as_default(self) -> None:
        self.window._default_size = QSize(self.window.width(), self.window.height())
        self.window.settings.setValue("prefs/default_size", self.window._default_size)
        self.window.default_width_spin.setValue(self.window._default_size.width())
        self.window.default_height_spin.setValue(self.window._default_size.height())

    def handle_resize(self) -> None:
        self.ensure_window_accessible()
        self.save_window_size()

    def handle_move(self) -> None:
        self.ensure_window_accessible()
        self.save_window_position()

    def quit_application(self) -> None:
        self.window._is_quitting = True
        QApplication.instance().quit()

    def handle_close(self, event) -> None:
        if self.window._is_quitting:
            self.window.tray_icon.hide()
            event.accept()
            return

        self.hide_to_tray()
        event.ignore()

    def handle_change(self, event) -> bool:
        if event.type() == event.Type.WindowStateChange and self.window.isMinimized():
            self.hide_to_tray()
            event.accept()
            return True
        return False

    def snap_to_edge(self) -> None:
        screen = QApplication.screenAt(self.window.frameGeometry().center())
        if screen is None:
            return

        geometry = screen.availableGeometry()
        frame = self.window.frameGeometry()

        x = frame.x()
        y = frame.y()

        if abs(frame.left() - geometry.left()) <= self.window._snap_margin:
            x = geometry.left()
        elif abs(frame.right() - geometry.right()) <= self.window._snap_margin:
            x = geometry.right() - frame.width()

        if abs(frame.top() - geometry.top()) <= self.window._snap_margin:
            y = geometry.top()
        elif abs(frame.bottom() - geometry.bottom()) <= self.window._snap_margin:
            y = geometry.bottom() - frame.height()

        x = max(geometry.left(), min(x, geometry.right() - frame.width()))
        y = max(geometry.top(), min(y, geometry.bottom() - frame.height()))
        self.window.move(x, y)

    def restore_window_geometry(self) -> None:
        saved_size = self.window.settings.value("window/size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            restored_width = max(self.window.minimumWidth(), saved_size.width())
            restored_height = max(self.window.minimumHeight(), saved_size.height())
            self.window.resize(restored_width, restored_height)

        saved_position = self.window.settings.value("window/position")
        if not isinstance(saved_position, QPoint):
            return

        target_position = self.clamp_position_to_screen(saved_position)
        self.window.move(target_position)
        self.ensure_window_accessible()

    def save_window_size(self) -> None:
        self.window.settings.setValue("window/size", self.window.size())

    def save_window_position(self) -> None:
        self.window.settings.setValue("window/position", self.window.pos())

    def clamp_position_to_screen(self, position: QPoint) -> QPoint:
        frame_width = self.window.frameGeometry().width()
        frame_height = self.window.frameGeometry().height()
        probe_point = QPoint(
            position.x() + max(1, frame_width // 2),
            position.y() + max(1, frame_height // 2),
        )
        screen = QApplication.screenAt(probe_point)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return position

        geometry = screen.availableGeometry()
        clamped_x = max(geometry.left(), min(position.x(), geometry.right() - frame_width))
        clamped_y = max(geometry.top(), min(position.y(), geometry.bottom() - frame_height))
        return QPoint(clamped_x, clamped_y)

    def ensure_window_accessible(self) -> None:
        if self.window._geometry_adjusting:
            return

        frame = self.window.frameGeometry()
        screen = QApplication.screenAt(frame.center())
        if screen is None:
            screen = QApplication.screenAt(frame.bottomRight())
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        target_width = min(frame.width(), geometry.width())
        target_height = min(frame.height(), geometry.height())

        min_x = geometry.left() - target_width + self.window._visible_corner_margin
        max_x = geometry.right() - self.window._visible_corner_margin
        min_y = geometry.top() - target_height + self.window._visible_corner_margin
        max_y = geometry.bottom() - self.window._visible_corner_margin

        target_x = max(min_x, min(frame.x(), max_x))
        target_y = max(min_y, min(frame.y(), max_y))

        needs_resize = target_width != frame.width() or target_height != frame.height()
        needs_move = target_x != frame.x() or target_y != frame.y()
        if not needs_resize and not needs_move:
            return

        self.window._geometry_adjusting = True
        try:
            if needs_resize:
                self.window.resize(target_width, target_height)
            if needs_move:
                self.window.move(target_x, target_y)
        finally:
            self.window._geometry_adjusting = False
