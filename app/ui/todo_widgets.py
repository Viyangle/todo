from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.window_widgets import CheckIndicator


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
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._stop_auto_scroll()
        self._drop_indicator_y = None
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        self._stop_auto_scroll()
        self._drag_row = None
        self._drop_indicator_y = None
        self.viewport().update()
        before_order = [self.item(index).data(Qt.UserRole) for index in range(self.count())]
        super().dropEvent(event)
        after_order = [self.item(index).data(Qt.UserRole) for index in range(self.count())]
        if before_order != after_order:
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

    def update_content(self, title: str, due_at: str | None, done: bool, is_due_soon: bool) -> None:
        self.label.setText(title)
        self.deadline_label.setText(self._format_deadline(due_at))
        self._done = done
        self._is_due_soon = is_due_soon
        self.indicator.set_done(done)
        self.updateGeometry()
        self._apply_state()

    def _format_deadline(self, due_at: str | None) -> str:
        if not due_at:
            return "长期事务"

        from PySide6.QtCore import QDateTime

        due = QDateTime.fromString(due_at, Qt.ISODate)
        if not due.isValid():
            return f"Due: {due_at}"
        return f"Due: {due.toString('yyyy-MM-dd HH:mm')}"

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
        title_width = max(180, self.width() - 90 if self.width() > 0 else 240)
        title_rect = title_metrics.boundingRect(
            0,
            0,
            title_width,
            1000,
            Qt.TextWordWrap,
            self.label.text(),
        )

        deadline_metrics = QFontMetrics(self.deadline_label.font())
        deadline_height = deadline_metrics.height()
        total_height = title_rect.height() + deadline_height + 34
        return QSize(max(260, title_rect.width() + 56), max(62, total_height))
