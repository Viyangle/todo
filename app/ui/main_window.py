from PySide6.QtCore import QPoint, QRectF, QSettings, QSize, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.data.storage import TodoStorage


class CheckIndicator(QWidget):
    clicked = Signal()

    def __init__(self, done: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._done = done
        self.setFixedSize(18, 18)
        self.setCursor(Qt.PointingHandCursor)

    def set_done(self, done: bool) -> None:
        self._done = done
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(1.5, 1.5, self.width() - 3, self.height() - 3)
        if self._done:
            painter.setBrush(QColor(255, 255, 255, 235))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect)

            pen = QPen(QColor(66, 96, 130), 2.0)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            path = QPainterPath()
            path.moveTo(self.width() * 0.28, self.height() * 0.55)
            path.lineTo(self.width() * 0.45, self.height() * 0.72)
            path.lineTo(self.width() * 0.74, self.height() * 0.34)
            painter.drawPath(path)
            return

        painter.setBrush(QColor(255, 255, 255, 36))
        painter.setPen(QPen(QColor(255, 255, 255, 160), 1.4))
        painter.drawEllipse(rect)

    def sizeHint(self) -> QSize:
        return QSize(18, 18)


class WindowControlButton(QPushButton):
    def __init__(self, kind: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(28, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 36);
                border-radius: 10px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 28);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 16);
            }
            """
        )

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("white"), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.kind == "minimize":
            y = self.height() / 2 + 2
            painter.drawLine(9, int(y), self.width() - 9, int(y))
            return

        if self.kind == "close":
            painter.drawLine(10, 8, self.width() - 10, self.height() - 8)
            painter.drawLine(self.width() - 10, 8, 10, self.height() - 8)


class ActionIconButton(QPushButton):
    def __init__(self, kind: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(73, 109, 153, 158);
                border: 1px solid rgba(255, 255, 255, 76);
                border-radius: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(84, 125, 173, 184);
            }
            QPushButton:pressed {
                background-color: rgba(62, 93, 129, 210);
            }
            """
        )

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 248, 252), 2.1)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if self.kind == "add":
            center_x = self.width() // 2
            center_y = self.height() // 2
            painter.drawLine(center_x, 11, center_x, self.height() - 11)
            painter.drawLine(11, center_y, self.width() - 11, center_y)
            return

        if self.kind == "reset":
            rect = QRectF(11, 11, self.width() - 22, self.height() - 22)
            painter.drawRoundedRect(rect, 4, 4)
            painter.drawLine(16, 16, 22, 16)
            painter.drawLine(16, 16, 16, 22)
            return

        if self.kind == "clear":
            painter.drawLine(12, 12, 24, 24)
            painter.drawLine(20, 20, 24, 16)

            band_pen = QPen(QColor(245, 248, 252), 1.6)
            band_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(band_pen)
            painter.drawLine(18, 23, 26, 15)

            painter.setPen(pen)
            broom_head = QPainterPath()
            broom_head.moveTo(16, 24)
            broom_head.lineTo(25, 33)
            broom_head.lineTo(31, 27)
            broom_head.lineTo(22, 18)
            broom_head.closeSubpath()
            painter.drawPath(broom_head)

            broom_lines_pen = QPen(QColor(245, 248, 252), 1.5)
            broom_lines_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(broom_lines_pen)
            painter.drawLine(20, 28, 24, 32)
            painter.drawLine(24, 24, 28, 28)
            return

        if self.kind == "refresh":
            rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
            painter.drawArc(rect, 35 * 16, 170 * 16)
            painter.drawArc(rect, 225 * 16, 170 * 16)

            arrow_pen = QPen(QColor(245, 248, 252), 1.8)
            arrow_pen.setCapStyle(Qt.RoundCap)
            arrow_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(arrow_pen)

            top_arrow = QPainterPath()
            top_arrow.moveTo(27, 10)
            top_arrow.lineTo(31, 11)
            top_arrow.lineTo(29, 15)
            painter.drawPath(top_arrow)

            bottom_arrow = QPainterPath()
            bottom_arrow.moveTo(13, 30)
            bottom_arrow.lineTo(9, 29)
            bottom_arrow.lineTo(11, 25)
            painter.drawPath(bottom_arrow)


class ResizeHandle(QWidget):
    def __init__(self, window: "MainWindow", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._start_global = QPoint()
        self._start_size = QSize()
        self.setFixedSize(18, 18)
        self.setCursor(Qt.SizeFDiagCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._start_global = event.globalPosition().toPoint()
            self._start_size = self._window.size()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._start_global
            new_width = max(self._window.minimumWidth(), self._start_size.width() + delta.x())
            new_height = max(self._window.minimumHeight(), self._start_size.height() + delta.y())
            self._window.resize(new_width, new_height)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 248, 252, 180), 1.4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        painter.drawLine(6, 12, 12, 6)
        painter.drawLine(9, 15, 15, 9)
        painter.drawLine(12, 18, 18, 12)


class ReorderableTodoListWidget(QListWidget):
    order_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_row: int | None = None
        self._drop_indicator_y: int | None = None
        self._last_drag_pos = QPoint()
        self._auto_scroll_direction = 0
        self._auto_scroll_margin = 28
        self._auto_scroll_step = 1
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(300)
        self._auto_scroll_timer.timeout.connect(self._perform_auto_scroll)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def startDrag(self, supported_actions) -> None:  # type: ignore[override]
        self._drag_row = self.currentRow()
        super().startDrag(supported_actions)
        self._stop_auto_scroll()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        self._last_drag_pos = event.position().toPoint()
        self._update_auto_scroll(self._last_drag_pos)
        self._drop_indicator_y = self._indicator_y_for_position(self._last_drag_pos)
        self.viewport().update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._stop_auto_scroll()
        self._drop_indicator_y = None
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        self._stop_auto_scroll()
        if event.source() is not self or self._drag_row is None:
            self._drop_indicator_y = None
            self.viewport().update()
            super().dropEvent(event)
            self.order_changed.emit()
            return

        source_row = self._drag_row
        self._drag_row = None
        self._drop_indicator_y = None
        self.viewport().update()

        if source_row < 0 or source_row >= self.count():
            event.ignore()
            return

        target_row = self._target_row_for_position(event.position().toPoint())
        if target_row > source_row:
            target_row -= 1

        if target_row == source_row:
            event.ignore()
            self.viewport().update()
            return

        item = self.item(source_row)
        widget = self.itemWidget(item)
        if widget is not None:
            self.removeItemWidget(item)

        item = self.takeItem(source_row)
        self.insertItem(target_row, item)
        if widget is not None:
            self.setItemWidget(item, widget)

        event.acceptProposedAction()
        self.order_changed.emit()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        if self._drop_indicator_y is None:
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 248, 252), 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        left = 16
        right = self.viewport().width() - 16
        painter.drawLine(left, self._drop_indicator_y, right, self._drop_indicator_y)

    def _indicator_y_for_position(self, position: QPoint) -> int:
        target_row = self._target_row_for_position(position)
        return self._indicator_y_for_row(target_row)

    def _indicator_y_for_row(self, row: int) -> int:
        if self.count() == 0:
            return 12

        if row <= 0:
            first_rect = self.visualItemRect(self.item(0))
            return max(8, first_rect.top() + 2)

        if row >= self.count():
            last_rect = self.visualItemRect(self.item(self.count() - 1))
            return last_rect.bottom() + 2

        previous_rect = self.visualItemRect(self.item(row - 1))
        current_rect = self.visualItemRect(self.item(row))
        return (previous_rect.bottom() + current_rect.top()) // 2

    def _target_row_for_position(self, position: QPoint) -> int:
        target_item = self.itemAt(position)
        if target_item is None:
            return self.count()

        target_row = self.row(target_item)
        target_rect = self.visualItemRect(target_item)
        if position.y() >= target_rect.center().y():
            return target_row + 1
        return target_row

    def _update_auto_scroll(self, position: QPoint) -> None:
        viewport_height = self.viewport().height()
        direction = 0
        if position.y() < self._auto_scroll_margin:
            direction = -1
        elif position.y() > viewport_height - self._auto_scroll_margin:
            direction = 1

        self._auto_scroll_direction = direction
        if direction == 0:
            self._auto_scroll_timer.stop()
            return

        if not self._auto_scroll_timer.isActive():
            self._auto_scroll_timer.start()

    def _stop_auto_scroll(self) -> None:
        self._auto_scroll_direction = 0
        self._auto_scroll_timer.stop()

    def _perform_auto_scroll(self) -> None:
        if self._auto_scroll_direction == 0:
            self._auto_scroll_timer.stop()
            return

        scroll_bar = self.verticalScrollBar()
        new_value = scroll_bar.value() + self._auto_scroll_direction * self._auto_scroll_step
        new_value = max(scroll_bar.minimum(), min(new_value, scroll_bar.maximum()))
        if new_value == scroll_bar.value():
            self._auto_scroll_timer.stop()
            return

        scroll_bar.setValue(new_value)
        self._drop_indicator_y = self._indicator_y_for_position(self._last_drag_pos)
        self.viewport().update()


class TodoRowWidget(QWidget):
    def __init__(self, title: str, done: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._done = done
        self._hovered = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.indicator = CheckIndicator(done, self)
        self.label = QLabel(title)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(self.indicator, 0, Qt.AlignVCenter)
        layout.addWidget(self.label, 1)

        self._apply_state()

    def set_done(self, done: bool) -> None:
        self._done = done
        self.indicator.set_done(done)
        self._apply_state()

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_state()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_state()
        super().leaveEvent(event)

    def _apply_state(self) -> None:
        font = QFont(self.label.font())
        font.setPointSize(12)
        font.setStrikeOut(self._done)
        font.setBold(not self._done)
        self.label.setFont(font)

        if self._done:
            text_color = "rgba(74, 88, 102, 150)"
            background = "rgba(255, 255, 255, 48)"
            border = "rgba(255, 255, 255, 50)"
        else:
            text_color = "rgb(28, 37, 48)"
            background = "rgba(255, 255, 255, 68)"
            border = "rgba(255, 255, 255, 64)"

        if self._hovered and self._done:
            background = "rgba(196, 230, 210, 78)"
            border = "rgba(222, 245, 230, 124)"
        elif self._hovered:
            background = "rgba(158, 208, 255, 82)"
            border = "rgba(214, 238, 255, 128)"

        self.label.setStyleSheet(f"background: transparent; color: {text_color};")
        self.setStyleSheet(
            f"""
            TodoRowWidget {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 14px;
            }}
            """
        )

    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(self.label.font())
        text_height = metrics.height() + 8
        content_height = max(text_height, self.indicator.sizeHint().height())
        vertical_padding = 24
        return QSize(0, max(52, content_height + vertical_padding))


class TitleBar(QWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.main_window = parent
        self._drag_start_global: QPoint | None = None
        self._drag_start_window_pos: QPoint | None = None

        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel("Todo")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")

        self.min_button = WindowControlButton("minimize", self)
        self.min_button.clicked.connect(self.main_window.hide_to_tray)

        self.close_button = WindowControlButton("close", self)
        self.close_button.clicked.connect(self.main_window.quit_application)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.min_button)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_start_window_pos = self.main_window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._drag_start_global is not None
            and self._drag_start_window_pos is not None
            and event.buttons() & Qt.LeftButton
        ):
            delta = event.globalPosition().toPoint() - self._drag_start_global
            self.main_window.move(self._drag_start_window_pos + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start_global = None
            self._drag_start_window_pos = None
            self.main_window.snap_to_edge()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, storage: TodoStorage) -> None:
        super().__init__()
        self.storage = storage
        self.settings = QSettings("TodoDesktop", "Todo")
        self._is_quitting = False
        self._snap_margin = 24
        self._corner_radius = 22
        self._default_size = QSize(360, 480)

        self.setWindowTitle("Todo")
        self.setMinimumSize(self._default_size)
        self.resize(self._default_size)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._restore_window_geometry()

        self._setup_ui()
        self._setup_tray()
        self._refresh_list()

    def _setup_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("windowRoot")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        self.panel = QWidget()
        self.panel.setObjectName("panel")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(14, 14, 14, 14)
        panel_layout.setSpacing(10)

        self.title_bar = TitleBar(self)
        panel_layout.addWidget(self.title_bar)

        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter a task and press Enter")
        self.input_edit.returnPressed.connect(self.add_todo)

        add_button = ActionIconButton("add")
        add_button.clicked.connect(self.add_todo)

        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(add_button)
        panel_layout.addLayout(input_layout)

        self.todo_list = ReorderableTodoListWidget()
        self.todo_list.order_changed.connect(self.persist_current_order)
        panel_layout.addWidget(self.todo_list)

        action_layout = QHBoxLayout()
        reset_button = QPushButton("default")
        reset_button.clicked.connect(self.restore_default_size)

        delete_button = QPushButton("clear")
        delete_button.clicked.connect(self.delete_completed)

        refresh_button = QPushButton("refresh")
        refresh_button.clicked.connect(self._refresh_list)

        self.resize_handle = ResizeHandle(self, self.panel)

        action_layout.addWidget(reset_button)
        action_layout.addStretch()
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_button)
        action_layout.addWidget(self.resize_handle, 0, Qt.AlignRight | Qt.AlignBottom)
        panel_layout.addLayout(action_layout)

        main_layout.addWidget(self.panel)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(46)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(12, 18, 28, 110))
        self.panel.setGraphicsEffect(shadow)

        self._apply_styles()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget {{
                font-family: "Segoe UI", "SimHei", "Microsoft YaHei UI", "Microsoft YaHei";
            }}
            #windowRoot {{
                background: transparent;
            }}
            #panel {{
                background-color: rgba(220, 232, 247, 166);
                border: 1px solid rgba(255, 255, 255, 110);
                border-radius: {self._corner_radius}px;
            }}
            QLabel {{
                color: rgb(28, 37, 48);
            }}
            QLineEdit, QListWidget {{
                background-color: rgba(255, 255, 255, 92);
                border: 1px solid rgba(255, 255, 255, 140);
                border-radius: 16px;
                color: rgb(31, 39, 51);
                padding: 10px 12px;
                outline: none;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(164, 214, 255, 180);
                background-color: rgba(255, 255, 255, 118);
            }}
            QListWidget {{
                padding: 8px;
            }}
            QListWidget::item {{
                border: none;
                background: transparent;
                margin: 4px 0;
                padding: 0;
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
            QPushButton {{
                background-color: rgba(73, 109, 153, 158);
                border: 1px solid rgba(255, 255, 255, 76);
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(84, 125, 173, 184);
            }}
            QPushButton:pressed {{
                background-color: rgba(62, 93, 129, 210);
            }}
            """
        )

    def _setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("Show / Hide")
        show_action.triggered.connect(self.toggle_visibility)

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
            QSystemTrayIcon.MiddleClick,
        ):
            self.toggle_visibility()

    def hide_to_tray(self) -> None:
        self.hide()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
            return

        self.showNormal()
        self.raise_()
        self.activateWindow()

    def restore_default_size(self) -> None:
        self.resize(self._default_size)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._save_window_size()

    def moveEvent(self, event) -> None:  # type: ignore[override]
        super().moveEvent(event)
        self._save_window_position()

    def quit_application(self) -> None:
        self._is_quitting = True
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._is_quitting:
            self.tray_icon.hide()
            event.accept()
            return

        self.hide_to_tray()
        event.ignore()

    def changeEvent(self, event) -> None:  # type: ignore[override]
        if event.type() == event.Type.WindowStateChange and self.isMinimized():
            self.hide_to_tray()
            event.accept()
            return
        super().changeEvent(event)

    def snap_to_edge(self) -> None:
        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            return

        geometry = screen.availableGeometry()
        frame = self.frameGeometry()

        x = frame.x()
        y = frame.y()

        if abs(frame.left() - geometry.left()) <= self._snap_margin:
            x = geometry.left()
        elif abs(frame.right() - geometry.right()) <= self._snap_margin:
            x = geometry.right() - frame.width()

        if abs(frame.top() - geometry.top()) <= self._snap_margin:
            y = geometry.top()
        elif abs(frame.bottom() - geometry.bottom()) <= self._snap_margin:
            y = geometry.bottom() - frame.height()

        x = max(geometry.left(), min(x, geometry.right() - frame.width()))
        y = max(geometry.top(), min(y, geometry.bottom() - frame.height()))
        self.move(x, y)

    def _restore_window_geometry(self) -> None:
        saved_size = self.settings.value("window/size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            restored_width = max(self.minimumWidth(), saved_size.width())
            restored_height = max(self.minimumHeight(), saved_size.height())
            self.resize(restored_width, restored_height)

        saved_position = self.settings.value("window/position")
        if not isinstance(saved_position, QPoint):
            return

        target_position = self._clamp_position_to_screen(saved_position)
        self.move(target_position)

    def _save_window_size(self) -> None:
        self.settings.setValue("window/size", self.size())

    def _save_window_position(self) -> None:
        self.settings.setValue("window/position", self.pos())

    def _clamp_position_to_screen(self, position: QPoint) -> QPoint:
        frame_width = self.frameGeometry().width()
        frame_height = self.frameGeometry().height()
        probe_point = QPoint(position.x() + max(1, frame_width // 2), position.y() + max(1, frame_height // 2))
        screen = QApplication.screenAt(probe_point)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return position

        geometry = screen.availableGeometry()
        clamped_x = max(geometry.left(), min(position.x(), geometry.right() - frame_width))
        clamped_y = max(geometry.top(), min(position.y(), geometry.bottom() - frame_height))
        return QPoint(clamped_x, clamped_y)

    def add_todo(self) -> None:
        text = self.input_edit.text()
        if not text.strip():
            return

        try:
            self.storage.add_todo(text)
        except ValueError as error:
            QMessageBox.warning(self, "Warning", str(error))
            return

        self.input_edit.clear()
        self._refresh_list(scroll_to_bottom=True)

    def _refresh_list(self, keep_scroll: bool = False, scroll_to_bottom: bool = False) -> None:
        scroll_bar = self.todo_list.verticalScrollBar()
        previous_scroll = scroll_bar.value()

        self.todo_list.clear()
        for todo in self.storage.list_todos():
            item = QListWidgetItem("")
            item.setData(Qt.UserRole, todo.id)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable)

            row_widget = TodoRowWidget(todo.title, todo.done, self.todo_list)
            row_widget.indicator.clicked.connect(
                lambda _checked=False, current_item=item: self.toggle_todo(current_item)
            )
            item.setSizeHint(row_widget.sizeHint())

            self.todo_list.addItem(item)
            self.todo_list.setItemWidget(item, row_widget)

        if scroll_to_bottom:
            self.todo_list.scrollToBottom()
        elif keep_scroll:
            scroll_bar.setValue(previous_scroll)

    def persist_current_order(self) -> None:
        todo_ids = []
        for index in range(self.todo_list.count()):
            item = self.todo_list.item(index)
            todo_id = item.data(Qt.UserRole)
            if todo_id is not None:
                todo_ids.append(int(todo_id))

        if not todo_ids:
            return

        self.storage.update_order(todo_ids)
        self._refresh_list(keep_scroll=True)

    def toggle_todo(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        if todo_id is None:
            return

        self.storage.toggle_done(int(todo_id))
        self._refresh_list(keep_scroll=True)

    def delete_completed(self) -> None:
        self.storage.delete_completed()
        self._refresh_list(keep_scroll=True)




