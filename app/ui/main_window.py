from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPen
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

        layout.addWidget(self.indicator, 0, Qt.AlignTop)
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
        return QSize(0, 44)


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
        title.setStyleSheet("font-size: 14px; font-weight: 600;")

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
        self._is_quitting = False
        self._snap_margin = 24
        self._corner_radius = 22

        self.setWindowTitle("Todo")
        self.setMinimumSize(360, 480)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

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

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_todo)

        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(add_button)
        panel_layout.addLayout(input_layout)

        self.todo_list = QListWidget()
        self.todo_list.setFocusPolicy(Qt.NoFocus)
        self.todo_list.setSelectionMode(QAbstractItemView.NoSelection)
        panel_layout.addWidget(self.todo_list)

        action_layout = QHBoxLayout()
        action_layout.addStretch()

        delete_button = QPushButton("Clear Done")
        delete_button.clicked.connect(self.delete_completed)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_list)

        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_button)
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

    def toggle_todo(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        if todo_id is None:
            return

        self.storage.toggle_done(int(todo_id))
        self._refresh_list(keep_scroll=True)

    def delete_completed(self) -> None:
        self.storage.delete_completed()
        self._refresh_list(keep_scroll=True)
