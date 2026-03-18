from PySide6.QtCore import QDate, QDateTime, QPoint, QRectF, QSettings, QSize, Qt, QTime, Signal, QTimer
from PySide6.QtGui import QCursor, QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
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
    QSpinBox,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

import json
import random
from pathlib import Path

from app.data.storage import TodoStorage

TAROT_NAME_ZH = {
    "The Fool": "愚者",
    "The Magician": "魔术师",
    "The High Priestess": "女祭司",
    "The Empress": "女皇",
    "The Emperor": "皇帝",
    "The Lovers": "恋人",
    "The Chariot": "战车",
    "Strength": "力量",
    "The Hermit": "隐者",
    "Wheel of Fortune": "命运之轮",
    "Justice": "正义",
    "The Hanged Man": "倒吊人",
    "Death": "死神",
    "Temperance": "节制",
    "The Devil": "恶魔",
    "The Tower": "高塔",
    "The Star": "星星",
    "The Moon": "月亮",
    "The Sun": "太阳",
    "Judgement": "审判",
    "The World": "世界",
}


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
    def __init__(
        self,
        title: str,
        due_at: str | None,
        done: bool,
        is_due_soon: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._done = done
        self._is_due_soon = is_due_soon
        self._hovered = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.indicator = CheckIndicator(done, self)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.label = QLabel(title)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.deadline_label = QLabel(self._format_deadline(due_at))
        self.deadline_label.setWordWrap(False)
        self.deadline_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        text_layout.addWidget(self.label)
        text_layout.addWidget(self.deadline_label)

        layout.addWidget(self.indicator, 0, Qt.AlignTop)
        layout.addLayout(text_layout, 1)

        self._apply_state()

    def _format_deadline(self, due_at: str | None) -> str:
        if not due_at:
            return "长期事务"

        due = QDateTime.fromString(due_at, Qt.ISODate)
        if not due.isValid():
            return f"截止时间: {due_at}"
        return f"截止时间: {due.toString('yyyy-MM-dd HH:mm')}"

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
        title_font = QFont(self.label.font())
        title_font.setPointSize(12)
        title_font.setStrikeOut(self._done)
        title_font.setBold(not self._done)
        self.label.setFont(title_font)

        deadline_font = QFont(self.deadline_label.font())
        deadline_font.setPointSize(9)
        deadline_font.setStrikeOut(False)
        deadline_font.setBold(False)
        self.deadline_label.setFont(deadline_font)

        if self._done:
            text_color = "rgba(74, 88, 102, 150)"
            deadline_color = "rgba(74, 88, 102, 130)"
            background = "rgba(255, 255, 255, 48)"
            border = "rgba(255, 255, 255, 50)"
        else:
            text_color = "rgb(28, 37, 48)"
            deadline_color = "rgba(28, 37, 48, 170)"
            background = "rgba(255, 255, 255, 68)"
            border = "rgba(255, 255, 255, 64)"

        if self._is_due_soon and not self._done:
            deadline_color = "rgb(152, 54, 30)"
            background = "rgba(255, 210, 182, 120)"
            border = "rgba(245, 148, 102, 180)"

        if self._hovered and self._done:
            background = "rgba(196, 230, 210, 78)"
            border = "rgba(222, 245, 230, 124)"
        elif self._hovered and self._is_due_soon and not self._done:
            background = "rgba(255, 196, 156, 152)"
            border = "rgba(238, 129, 71, 210)"
        elif self._hovered:
            background = "rgba(158, 208, 255, 82)"
            border = "rgba(214, 238, 255, 128)"

        self.label.setStyleSheet(f"background: transparent; color: {text_color};")
        self.deadline_label.setStyleSheet(f"background: transparent; color: {deadline_color};")
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
        title_metrics = QFontMetrics(self.label.font())
        deadline_metrics = QFontMetrics(self.deadline_label.font())
        text_height = title_metrics.height() + deadline_metrics.height() + 10
        content_height = max(text_height, self.indicator.sizeHint().height())
        vertical_padding = 24
        return QSize(0, max(62, content_height + vertical_padding))


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
        self._minimum_size = QSize(400, 480)
        self._fallback_default_size = QSize(400, 520)
        self._default_size = self._load_default_size()
        self._due_soon_minutes = self._load_due_warning_minutes()
        self._geometry_adjusting = False
        self._visible_corner_margin = 44
        self._tarot_cards = self._load_tarot_cards()

        self.setWindowTitle("Todo")
        self.setMinimumSize(self._minimum_size)
        self.resize(self._default_size)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._restore_window_geometry()

        self._setup_ui()
        self._setup_tray()
        self._refresh_list()
        self._refresh_tarot_history()

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

        self.page_stack = QStackedWidget(self.panel)
        self.page_stack.setFrameShape(QFrame.NoFrame)
        self.page_stack.setLineWidth(0)

        self.main_page = QWidget(self.page_stack)
        main_page_layout = QVBoxLayout(self.main_page)
        main_page_layout.setContentsMargins(0, 0, 0, 0)
        main_page_layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter a task and press Enter")
        self.input_edit.setMinimumWidth(230)
        self.input_edit.returnPressed.connect(self.add_todo)

        self.enable_due_checkbox = QCheckBox("due")
        self.enable_due_checkbox.toggled.connect(self._toggle_due_edit_enabled)
        self.enable_due_checkbox.installEventFilter(self)

        tomorrow = QDate.currentDate().addDays(1)
        self._due_date = tomorrow
        self._due_time = QTime.currentTime()

        self.due_popup = QFrame(self.panel)
        self.due_popup.setObjectName("duePopup")
        self.due_popup.setFrameShape(QFrame.StyledPanel)
        self.due_popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.due_popup.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.due_popup.installEventFilter(self)

        popup_layout = QVBoxLayout(self.due_popup)
        popup_layout.setContentsMargins(10, 10, 10, 10)
        popup_layout.setSpacing(8)

        self.due_calendar = QCalendarWidget(self.due_popup)
        self.due_calendar.setSelectedDate(self._due_date)
        self.due_calendar.clicked.connect(self._on_due_date_changed)
        popup_layout.addWidget(self.due_calendar)

        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        time_label = QLabel("time")
        self.due_hour_combo = QComboBox(self.due_popup)
        self.due_minute_combo = QComboBox(self.due_popup)

        for hour in range(24):
            self.due_hour_combo.addItem(f"{hour:02d}")
        for minute in range(0, 60, 5):
            self.due_minute_combo.addItem(f"{minute:02d}")

        rounded_minute = (self._due_time.minute() // 5) * 5
        self.due_hour_combo.setCurrentText(f"{self._due_time.hour():02d}")
        self.due_minute_combo.setCurrentText(f"{rounded_minute:02d}")
        self.due_hour_combo.currentTextChanged.connect(self._on_due_time_changed)
        self.due_minute_combo.currentTextChanged.connect(self._on_due_time_changed)

        time_row.addWidget(time_label)
        time_row.addWidget(self.due_hour_combo)
        time_row.addWidget(self.due_minute_combo)
        popup_layout.addLayout(time_row)

        self._due_popup_hide_timer = QTimer(self)
        self._due_popup_hide_timer.setSingleShot(True)
        self._due_popup_hide_timer.setInterval(150)
        self._due_popup_hide_timer.timeout.connect(self._hide_due_popup_if_outside)

        self._due_popup_show_timer = QTimer(self)
        self._due_popup_show_timer.setSingleShot(True)
        self._due_popup_show_timer.setInterval(180)
        self._due_popup_show_timer.timeout.connect(self._show_due_popup)

        add_button = ActionIconButton("add")
        add_button.clicked.connect(self.add_todo)

        input_layout.addWidget(self.input_edit, 1)
        input_layout.addWidget(self.enable_due_checkbox)
        input_layout.addWidget(add_button)
        main_page_layout.addLayout(input_layout)

        self.todo_list = ReorderableTodoListWidget()
        self.todo_list.order_changed.connect(self.persist_current_order)
        main_page_layout.addWidget(self.todo_list)

        action_layout = QHBoxLayout()
        reset_button = QPushButton("default")
        reset_button.clicked.connect(self.restore_default_size)

        config_button = QPushButton("config")
        config_button.clicked.connect(self.show_settings_page)

        tarot_button = QPushButton("tarot")
        tarot_button.clicked.connect(self.show_tarot_page)

        delete_button = QPushButton("clear")
        delete_button.clicked.connect(self.delete_completed)

        refresh_button = QPushButton("refresh")
        refresh_button.clicked.connect(self._refresh_list)

        self.resize_handle = ResizeHandle(self, self.panel)

        action_layout.addWidget(reset_button)
        action_layout.addWidget(config_button)
        action_layout.addWidget(tarot_button)
        action_layout.addStretch()
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_button)
        action_layout.addWidget(self.resize_handle, 0, Qt.AlignRight | Qt.AlignBottom)
        main_page_layout.addLayout(action_layout)

        self.settings_page = QWidget(self.page_stack)
        settings_layout = QVBoxLayout(self.settings_page)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        settings_layout.addWidget(settings_title)

        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)

        self.default_width_spin = QSpinBox(self.settings_page)
        self.default_width_spin.setRange(self._minimum_size.width(), 1200)
        self.default_width_spin.setSingleStep(20)

        self.default_height_spin = QSpinBox(self.settings_page)
        self.default_height_spin.setRange(self._minimum_size.height(), 1400)
        self.default_height_spin.setSingleStep(20)

        self.warn_minutes_spin = QSpinBox(self.settings_page)
        self.warn_minutes_spin.setRange(10, 1440)
        self.warn_minutes_spin.setSingleStep(10)
        self.warn_minutes_spin.setSuffix(" min")

        form_layout.addRow("Default Width", self.default_width_spin)
        form_layout.addRow("Default Height", self.default_height_spin)
        form_layout.addRow("Warning", self.warn_minutes_spin)
        settings_layout.addLayout(form_layout)

        settings_layout.addStretch()

        settings_action_layout = QHBoxLayout()
        back_button = QPushButton("back")
        back_button.clicked.connect(self.show_main_page)

        use_current_size_button = QPushButton("use current size")
        use_current_size_button.clicked.connect(self.save_current_size_as_default)

        save_button = QPushButton("save")
        save_button.clicked.connect(self.save_settings)

        settings_action_layout.addWidget(back_button)
        settings_action_layout.addWidget(use_current_size_button)
        settings_action_layout.addStretch()
        settings_action_layout.addWidget(save_button)
        settings_layout.addLayout(settings_action_layout)

        self.tarot_page = QWidget(self.page_stack)
        tarot_layout = QVBoxLayout(self.tarot_page)
        tarot_layout.setContentsMargins(0, 0, 0, 0)
        tarot_layout.setSpacing(10)

        tarot_title = QLabel("Tarot")
        tarot_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        tarot_layout.addWidget(tarot_title)

        tarot_hint = QLabel("Three-card spread: Past / Present / Future")
        tarot_hint.setWordWrap(True)
        tarot_hint.setStyleSheet("color: rgba(28, 37, 48, 170);")
        tarot_layout.addWidget(tarot_hint)

        self.tarot_question_edit = QLineEdit(self.tarot_page)
        self.tarot_question_edit.setPlaceholderText("e.g. What should I focus on this afternoon?")
        tarot_layout.addWidget(self.tarot_question_edit)

        tarot_control_layout = QHBoxLayout()
        tarot_control_layout.setSpacing(8)

        draw_button = QPushButton("draw three cards")
        draw_button.clicked.connect(self.draw_tarot_spread)
        tarot_control_layout.addWidget(draw_button)

        history_button = QPushButton("history")
        history_button.clicked.connect(self.show_tarot_history_page)
        tarot_control_layout.addWidget(history_button)
        tarot_control_layout.addStretch()
        tarot_layout.addLayout(tarot_control_layout)

        self.tarot_card_panel = QFrame(self.tarot_page)
        self.tarot_card_panel.setObjectName("tarotCardPanel")
        tarot_card_layout = QVBoxLayout(self.tarot_card_panel)
        tarot_card_layout.setContentsMargins(14, 14, 14, 14)
        tarot_card_layout.setSpacing(8)

        self.tarot_question_label = QLabel("Question: -")
        self.tarot_question_label.setWordWrap(True)
        self.tarot_question_label.setStyleSheet("color: rgba(28, 37, 48, 170);")
        tarot_card_layout.addWidget(self.tarot_question_label)

        self.tarot_spread_label = QLabel("Spread: Past / Present / Future")
        self.tarot_spread_label.setStyleSheet("font-size: 15px; font-weight: 700;")
        tarot_card_layout.addWidget(self.tarot_spread_label)

        cards_grid = QGridLayout()
        cards_grid.setHorizontalSpacing(10)
        cards_grid.setVerticalSpacing(10)

        self.tarot_past_box = QFrame(self.tarot_card_panel)
        self.tarot_past_box.setObjectName("tarotCardBox")
        past_layout = QVBoxLayout(self.tarot_past_box)
        past_layout.setContentsMargins(10, 10, 10, 10)
        self.tarot_past_title = QLabel("Past")
        self.tarot_past_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.tarot_past_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_past_title.setMinimumHeight(22)
        self.tarot_past_name = QLabel("-")
        self.tarot_past_name.setObjectName("tarotCardName")
        self.tarot_past_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_past_name.setMinimumHeight(30)
        self.tarot_past_body = QLabel("No card yet.")
        self.tarot_past_body.setWordWrap(True)
        self.tarot_past_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        past_layout.addWidget(self.tarot_past_title)
        past_layout.addWidget(self.tarot_past_name)
        past_layout.addWidget(self.tarot_past_body)
        past_layout.addStretch()

        self.tarot_present_box = QFrame(self.tarot_card_panel)
        self.tarot_present_box.setObjectName("tarotCardBox")
        present_layout = QVBoxLayout(self.tarot_present_box)
        present_layout.setContentsMargins(10, 10, 10, 10)
        self.tarot_present_title = QLabel("Present")
        self.tarot_present_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.tarot_present_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_present_title.setMinimumHeight(22)
        self.tarot_present_name = QLabel("-")
        self.tarot_present_name.setObjectName("tarotCardName")
        self.tarot_present_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_present_name.setMinimumHeight(30)
        self.tarot_present_body = QLabel("No card yet.")
        self.tarot_present_body.setWordWrap(True)
        self.tarot_present_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        present_layout.addWidget(self.tarot_present_title)
        present_layout.addWidget(self.tarot_present_name)
        present_layout.addWidget(self.tarot_present_body)
        present_layout.addStretch()

        self.tarot_future_box = QFrame(self.tarot_card_panel)
        self.tarot_future_box.setObjectName("tarotCardBox")
        future_layout = QVBoxLayout(self.tarot_future_box)
        future_layout.setContentsMargins(10, 10, 10, 10)
        self.tarot_future_title = QLabel("Future")
        self.tarot_future_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.tarot_future_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_future_title.setMinimumHeight(22)
        self.tarot_future_name = QLabel("-")
        self.tarot_future_name.setObjectName("tarotCardName")
        self.tarot_future_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tarot_future_name.setMinimumHeight(30)
        self.tarot_future_body = QLabel("No card yet.")
        self.tarot_future_body.setWordWrap(True)
        self.tarot_future_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        future_layout.addWidget(self.tarot_future_title)
        future_layout.addWidget(self.tarot_future_name)
        future_layout.addWidget(self.tarot_future_body)
        future_layout.addStretch()

        self.tarot_summary_box = QFrame(self.tarot_card_panel)
        self.tarot_summary_box.setObjectName("tarotSummaryBox")
        summary_layout = QVBoxLayout(self.tarot_summary_box)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        self.tarot_summary_title = QLabel("Interpretation")
        self.tarot_summary_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.tarot_summary_body = QLabel("Draw a spread to see the interpretation.")
        self.tarot_summary_body.setWordWrap(True)
        self.tarot_summary_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        summary_layout.addWidget(self.tarot_summary_title)
        summary_layout.addWidget(self.tarot_summary_body)
        summary_layout.addStretch()

        cards_grid.addWidget(self.tarot_past_box, 0, 0, Qt.AlignTop)
        cards_grid.addWidget(self.tarot_present_box, 0, 1, Qt.AlignTop)
        cards_grid.addWidget(self.tarot_future_box, 0, 2, Qt.AlignTop)
        cards_grid.addWidget(self.tarot_summary_box, 1, 0, 1, 3)
        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)
        cards_grid.setColumnStretch(2, 1)
        tarot_card_layout.addLayout(cards_grid)

        tarot_layout.addWidget(self.tarot_card_panel)
        tarot_layout.addStretch()

        tarot_action_layout = QHBoxLayout()
        tarot_back_button = QPushButton("back")
        tarot_back_button.clicked.connect(self.show_main_page)
        tarot_action_layout.addWidget(tarot_back_button)
        tarot_action_layout.addStretch()
        tarot_layout.addLayout(tarot_action_layout)

        self.tarot_history_page = QWidget(self.page_stack)
        tarot_history_layout = QVBoxLayout(self.tarot_history_page)
        tarot_history_layout.setContentsMargins(0, 0, 0, 0)
        tarot_history_layout.setSpacing(10)

        tarot_history_title = QLabel("Tarot History")
        tarot_history_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        tarot_history_layout.addWidget(tarot_history_title)

        self.tarot_history_list = QListWidget(self.tarot_history_page)
        self.tarot_history_list.itemClicked.connect(self.show_tarot_history_item)
        tarot_history_layout.addWidget(self.tarot_history_list)

        tarot_history_action_layout = QHBoxLayout()
        tarot_history_back_button = QPushButton("back")
        tarot_history_back_button.clicked.connect(self.show_tarot_page)
        tarot_history_action_layout.addWidget(tarot_history_back_button)
        tarot_history_action_layout.addStretch()
        tarot_history_layout.addLayout(tarot_history_action_layout)

        self.page_stack.addWidget(self.main_page)
        self.page_stack.addWidget(self.settings_page)
        self.page_stack.addWidget(self.tarot_page)
        self.page_stack.addWidget(self.tarot_history_page)
        self.page_stack.setCurrentWidget(self.main_page)
        panel_layout.addWidget(self.page_stack)

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
            QStackedWidget {{
                background: transparent;
                border: none;
            }}
            QStackedWidget::pane {{
                border: 0px;
                background: transparent;
            }}
            QLabel {{
                color: rgb(28, 37, 48);
            }}
            QLineEdit, QSpinBox, QComboBox, QListWidget {{
                background-color: rgba(255, 255, 255, 92);
                border: 1px solid rgba(255, 255, 255, 140);
                border-radius: 16px;
                color: rgb(31, 39, 51);
                padding: 10px 12px;
                outline: none;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid rgba(164, 214, 255, 180);
                background-color: rgba(255, 255, 255, 118);
            }}
            #duePopup {{
                background-color: rgba(230, 240, 252, 244);
                border: 1px solid rgba(255, 255, 255, 170);
                border-radius: 14px;
            }}
            #tarotCardPanel {{
                background-color: rgba(255, 255, 255, 92);
                border: 1px solid rgba(255, 255, 255, 140);
                border-radius: 14px;
            }}
            #tarotCardBox {{
                background-color: rgba(236, 245, 255, 205);
                border: 1px solid rgba(120, 170, 220, 210);
                border-radius: 12px;
            }}
            #tarotCardName {{
                color: rgb(24, 67, 112);
                font-size: 18px;
                font-weight: 800;
            }}
            #tarotSummaryBox {{
                background-color: rgba(255, 231, 209, 208);
                border: 1px solid rgba(236, 149, 92, 214);
                border-radius: 12px;
            }}
            QCalendarWidget QWidget {{
                alternate-background-color: rgba(200, 220, 242, 140);
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                selection-background-color: rgba(61, 96, 146, 235);
                selection-color: rgb(245, 248, 252);
            }}
            QCalendarWidget QTableView::item:selected {{
                background-color: rgb(0, 0, 0);
                color: rgb(255, 255, 255);
            }}
            QCheckBox {{
                color: rgb(31, 39, 51);
                font-size: 12px;
                font-weight: 600;
                padding: 0 4px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
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

    def _load_default_size(self) -> QSize:
        saved_size = self.settings.value("prefs/default_size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            width = max(self._minimum_size.width(), saved_size.width())
            height = max(self._minimum_size.height(), saved_size.height())
            return QSize(width, height)
        return QSize(self._fallback_default_size)

    def _load_due_warning_minutes(self) -> int:
        saved_value = self.settings.value("prefs/warn_minutes", 120)
        try:
            minutes = int(saved_value)
        except (TypeError, ValueError):
            minutes = 120
        return max(10, minutes)

    def restore_default_size(self) -> None:
        self.resize(self._default_size)

    def show_settings_page(self) -> None:
        self.default_width_spin.setValue(self._default_size.width())
        self.default_height_spin.setValue(self._default_size.height())
        self.warn_minutes_spin.setValue(self._due_soon_minutes)
        self.page_stack.setCurrentWidget(self.settings_page)

    def show_tarot_page(self) -> None:
        self.page_stack.setCurrentWidget(self.tarot_page)
        self._refresh_tarot_history()

    def show_tarot_history_page(self) -> None:
        self._refresh_tarot_history()
        self.page_stack.setCurrentWidget(self.tarot_history_page)

    def show_main_page(self) -> None:
        self.page_stack.setCurrentWidget(self.main_page)

    def save_settings(self) -> None:
        self._default_size = QSize(self.default_width_spin.value(), self.default_height_spin.value())
        self._due_soon_minutes = self.warn_minutes_spin.value()
        self.settings.setValue("prefs/default_size", self._default_size)
        self.settings.setValue("prefs/warn_minutes", self._due_soon_minutes)
        self.show_main_page()
        self._refresh_list(keep_scroll=True)

    def save_current_size_as_default(self) -> None:
        self._default_size = QSize(self.width(), self.height())
        self.settings.setValue("prefs/default_size", self._default_size)
        self.default_width_spin.setValue(self._default_size.width())
        self.default_height_spin.setValue(self._default_size.height())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._ensure_window_accessible()
        self._save_window_size()

    def moveEvent(self, event) -> None:  # type: ignore[override]
        super().moveEvent(event)
        self._ensure_window_accessible()
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
        self._ensure_window_accessible()

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

    def _ensure_window_accessible(self) -> None:
        if self._geometry_adjusting:
            return

        frame = self.frameGeometry()
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

        min_x = geometry.left() - target_width + self._visible_corner_margin
        max_x = geometry.right() - self._visible_corner_margin
        min_y = geometry.top() - target_height + self._visible_corner_margin
        max_y = geometry.bottom() - self._visible_corner_margin

        target_x = max(min_x, min(frame.x(), max_x))
        target_y = max(min_y, min(frame.y(), max_y))

        needs_resize = target_width != frame.width() or target_height != frame.height()
        needs_move = target_x != frame.x() or target_y != frame.y()
        if not needs_resize and not needs_move:
            return

        self._geometry_adjusting = True
        try:
            if needs_resize:
                self.resize(target_width, target_height)
            if needs_move:
                self.move(target_x, target_y)
        finally:
            self._geometry_adjusting = False

    def add_todo(self) -> None:
        text = self.input_edit.text()
        if not text.strip():
            return

        due_at = None
        if self.enable_due_checkbox.isChecked():
            due_value = QDateTime(self._due_date, self._due_time)
            due_at = due_value.toString(Qt.ISODate)

        try:
            self.storage.add_todo(text, due_at=due_at)
        except ValueError as error:
            QMessageBox.warning(self, "Warning", str(error))
            return

        self.input_edit.clear()
        self._refresh_list(scroll_to_bottom=True)

    def _toggle_due_edit_enabled(self, checked: bool) -> None:
        if not checked:
            self._due_popup_show_timer.stop()
            self._due_popup_hide_timer.stop()
            self.due_popup.hide()
            return

        if self.enable_due_checkbox.underMouse():
            self._due_popup_show_timer.start()

    def eventFilter(self, watched, event):  # type: ignore[override]
        if watched is self.enable_due_checkbox:
            if event.type() == event.Type.Enter and self.enable_due_checkbox.isChecked():
                self._due_popup_show_timer.start()
            elif event.type() == event.Type.Leave:
                self._due_popup_show_timer.stop()
                self._due_popup_hide_timer.start()
            elif event.type() == event.Type.MouseButtonPress:
                self._due_popup_show_timer.stop()
        elif watched is self.due_popup:
            if event.type() == event.Type.Enter:
                self._due_popup_hide_timer.stop()
            elif event.type() == event.Type.Leave:
                self._due_popup_hide_timer.start()

        return super().eventFilter(watched, event)

    def _show_due_popup(self) -> None:
        if not self.enable_due_checkbox.isChecked():
            return

        anchor = self.enable_due_checkbox.mapToGlobal(QPoint(0, self.enable_due_checkbox.height() + 6))
        popup_width = 280
        popup_height = 260
        screen = QApplication.screenAt(anchor)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return

        bounds = screen.availableGeometry()
        x = max(bounds.left(), min(anchor.x(), bounds.right() - popup_width))
        y = max(bounds.top(), min(anchor.y(), bounds.bottom() - popup_height))
        self.due_popup.setGeometry(x, y, popup_width, popup_height)
        self.due_popup.show()
        self.due_popup.raise_()

    def _hide_due_popup_if_outside(self) -> None:
        if not self.due_popup.isVisible():
            return

        # QComboBox dropdown is a separate popup window; keep due popup alive while it is open.
        if self.due_hour_combo.view().isVisible() or self.due_minute_combo.view().isVisible():
            return

        cursor_global = QCursor.pos()
        due_local = self.enable_due_checkbox.mapFromGlobal(cursor_global)
        over_due = self.enable_due_checkbox.rect().contains(due_local)
        over_popup = self.due_popup.geometry().contains(cursor_global)
        if over_due or over_popup:
            return
        self.due_popup.hide()

    def _on_due_date_changed(self, selected_date: QDate) -> None:
        self._due_date = selected_date

    def _on_due_time_changed(self, _value: str) -> None:
        hour = int(self.due_hour_combo.currentText())
        minute = int(self.due_minute_combo.currentText())
        self._due_time = QTime(hour, minute, 0)

    def _is_due_soon(self, due_at: str | None, done: bool) -> bool:
        if done or not due_at:
            return False

        due_time = QDateTime.fromString(due_at, Qt.ISODate)
        if not due_time.isValid():
            return False

        now = QDateTime.currentDateTime()
        soon_limit = now.addSecs(self._due_soon_minutes * 60)
        return now <= due_time <= soon_limit

    def _refresh_list(self, keep_scroll: bool = False, scroll_to_bottom: bool = False) -> None:
        scroll_bar = self.todo_list.verticalScrollBar()
        previous_scroll = scroll_bar.value()

        self.todo_list.clear()
        for todo in self.storage.list_todos():
            item = QListWidgetItem("")
            item.setData(Qt.UserRole, todo.id)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable)

            row_widget = TodoRowWidget(
                todo.title,
                todo.due_at,
                todo.done,
                self._is_due_soon(todo.due_at, todo.done),
                self.todo_list,
            )
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

    def _load_tarot_cards(self) -> list[dict[str, object]]:
        cards_path = Path(__file__).resolve().parent.parent / "data" / "tarot_cards.json"
        try:
            raw_text = cards_path.read_text(encoding="utf-8")
            cards = json.loads(raw_text)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return []

        if not isinstance(cards, list):
            return []

        valid_cards: list[dict[str, object]] = []
        for entry in cards:
            if not isinstance(entry, dict):
                continue
            if not entry.get("name"):
                continue
            if not entry.get("upright_meaning"):
                continue
            if not entry.get("reversed_meaning"):
                continue
            valid_cards.append(entry)
        return valid_cards

    def _draw_one_tarot_card(self, card_data: dict[str, object], position: str) -> dict[str, str]:
        orientation = random.choice(("upright", "reversed"))
        raw_name = str(card_data.get("name", "Unknown Card"))
        name = TAROT_NAME_ZH.get(raw_name, raw_name)
        upright_meaning = str(card_data.get("upright_meaning", ""))
        reversed_meaning = str(card_data.get("reversed_meaning", ""))
        upright_keywords = card_data.get("upright_keywords", [])
        reversed_keywords = card_data.get("reversed_keywords", [])

        if orientation == "upright":
            orientation_text = "Upright (正位)"
            meaning = upright_meaning
            keywords_raw = upright_keywords
        else:
            orientation_text = "Reversed (逆位)"
            meaning = reversed_meaning
            keywords_raw = reversed_keywords

        if isinstance(keywords_raw, list):
            keywords = [str(keyword).strip() for keyword in keywords_raw if str(keyword).strip()]
            keywords_text = " / ".join(keywords)
        else:
            keywords_text = str(keywords_raw)

        return {
            "position": position,
            "name": name,
            "orientation": orientation_text,
            "keywords": keywords_text,
            "meaning": meaning,
        }

    def draw_tarot_spread(self) -> None:
        if not self._tarot_cards:
            QMessageBox.warning(self, "Tarot", "Tarot deck is unavailable.")
            return

        question = self.tarot_question_edit.text().strip()
        if len(self._tarot_cards) >= 3:
            selected_cards = random.sample(self._tarot_cards, 3)
        else:
            selected_cards = [random.choice(self._tarot_cards) for _ in range(3)]

        spread_cards = [
            self._draw_one_tarot_card(selected_cards[0], "Past"),
            self._draw_one_tarot_card(selected_cards[1], "Present"),
            self._draw_one_tarot_card(selected_cards[2], "Future"),
        ]

        summary = self._build_tarot_summary(spread_cards)
        self.storage.add_tarot_reading(
            spread_type="past_present_future",
            cards=spread_cards,
            summary=summary,
            question=question or None,
        )
        self._show_tarot_reading(question, spread_cards, summary)
        self._refresh_tarot_history()

    def _build_tarot_summary(self, cards: list[dict[str, str]]) -> str:
        present_meaning = cards[1]["meaning"] if len(cards) > 1 else ""
        future_meaning = cards[2]["meaning"] if len(cards) > 2 else ""
        return f"Current focus: {present_meaning} Next trend: {future_meaning}"

    def _show_tarot_reading(self, question: str, cards: list[dict[str, str]], summary: str) -> None:
        question_text = question if question else "-"
        self.tarot_question_label.setText(f"Question: {question_text}")
        self.tarot_spread_label.setText("Spread: Past / Present / Future")

        by_position = {card.get("position", ""): card for card in cards}
        past = by_position.get("Past", {})
        present = by_position.get("Present", {})
        future = by_position.get("Future", {})

        self.tarot_past_name.setText(str(past.get("name", "-")))
        self.tarot_present_name.setText(str(present.get("name", "-")))
        self.tarot_future_name.setText(str(future.get("name", "-")))

        self.tarot_past_body.setText(
            f"{past.get('orientation', '-')}\n"
            f"Keywords: {past.get('keywords', '-')}\n"
            f"{past.get('meaning', '-')}"
        )
        self.tarot_present_body.setText(
            f"{present.get('orientation', '-')}\n"
            f"Keywords: {present.get('keywords', '-')}\n"
            f"{present.get('meaning', '-')}"
        )
        self.tarot_future_body.setText(
            f"{future.get('orientation', '-')}\n"
            f"Keywords: {future.get('keywords', '-')}\n"
            f"{future.get('meaning', '-')}"
        )
        self.tarot_summary_body.setText(summary)

    def _refresh_tarot_history(self) -> None:
        if not hasattr(self, "tarot_history_list"):
            return

        self.tarot_history_list.clear()
        for reading in self.storage.list_tarot_readings(limit=50):
            question = reading.question if reading.question else "No question"
            preview = f"{reading.created_at} | {question}"
            item = QListWidgetItem(preview)
            item.setData(Qt.UserRole, reading.id)
            self.tarot_history_list.addItem(item)

    def show_tarot_history_item(self, item: QListWidgetItem) -> None:
        reading_id = item.data(Qt.UserRole)
        if reading_id is None:
            return

        readings = self.storage.list_tarot_readings(limit=200)
        selected = next((reading for reading in readings if reading.id == int(reading_id)), None)
        if selected is None:
            return

        try:
            cards_raw = json.loads(selected.cards_json)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Tarot", "History record data is corrupted.")
            return

        cards: list[dict[str, str]] = []
        if isinstance(cards_raw, list):
            for entry in cards_raw:
                if not isinstance(entry, dict):
                    continue
                cards.append(
                    {
                        "position": str(entry.get("position", "")),
                        "name": TAROT_NAME_ZH.get(str(entry.get("name", "")), str(entry.get("name", ""))),
                        "orientation": str(entry.get("orientation", "")),
                        "keywords": str(entry.get("keywords", "")),
                        "meaning": str(entry.get("meaning", "")),
                    }
                )

        question = selected.question if selected.question else ""
        self._show_tarot_reading(question, cards, selected.summary)
        self.page_stack.setCurrentWidget(self.tarot_page)




