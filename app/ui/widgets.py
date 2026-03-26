from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PySide6.QtCore import QElapsedTimer, QPoint, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow


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
    def __init__(self, window: MainWindow, parent: QWidget | None = None) -> None:
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


class QuoteBoxWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._quote = "No quotes available."
        self._author = ""
        self.setObjectName("quoteBox")
        self.setFixedHeight(56)

    def set_quote(self, quote: str, author: str = "") -> None:
        self._quote = quote.strip() or "No quotes available."
        self._author = author.strip()
        self.update()

    def _split_two_lines(
        self,
        text: str,
        first_width: int,
        second_width: int,
        metrics: QFontMetrics,
    ) -> tuple[str, str]:
        compact = " ".join(text.split())
        if not compact:
            return "", ""

        def take_prefix(source: str, max_width: int) -> tuple[str, str]:
            if max_width <= 0:
                return "", source

            buffer = ""
            index = 0
            for index, char in enumerate(source):
                candidate = buffer + char
                if buffer and metrics.horizontalAdvance(candidate) > max_width:
                    break
                buffer = candidate
            else:
                return buffer.rstrip(), ""

            remainder = source[index:].lstrip()
            return buffer.rstrip(), remainder

        first_line, remainder = take_prefix(compact, first_width)
        if not remainder:
            return first_line, ""

        second_line, overflow = take_prefix(remainder, second_width)
        if overflow:
            second_line = metrics.elidedText(remainder, Qt.ElideRight, second_width)

        return first_line, second_line

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 248, 240, 128))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 16, 16)

        border_pen = QPen(QColor(236, 149, 92, 140), 1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 16, 16)

        content_rect = rect.adjusted(12, 8, -12, -8)
        quote_font = QFont(self.font())
        quote_font.setPointSize(10)
        painter.setFont(quote_font)
        painter.setPen(QColor(68, 50, 36))

        line_height = QFontMetrics(quote_font).lineSpacing()
        author_text = f"——{self._author}" if self._author else ""

        author_font = QFont(quote_font)
        author_font.setBold(True)
        author_metrics = QFontMetrics(author_font)
        author_width = author_metrics.horizontalAdvance(author_text) if author_text else 0
        reserved_width = author_width + 6 if author_text else 0

        first_line_rect = QRect(
            content_rect.left(),
            content_rect.top(),
            content_rect.width(),
            line_height,
        )
        second_line_rect = QRect(
            content_rect.left(),
            content_rect.top() + line_height,
            max(0, content_rect.width() - reserved_width),
            line_height,
        )

        quote_metrics = QFontMetrics(quote_font)
        first_line_text, second_line_text = self._split_two_lines(
            self._quote,
            first_line_rect.width(),
            second_line_rect.width(),
            quote_metrics,
        )

        painter.drawText(first_line_rect, Qt.AlignLeft | Qt.AlignVCenter, first_line_text)
        if second_line_text:
            painter.drawText(second_line_rect, Qt.AlignLeft | Qt.AlignVCenter, second_line_text)

        if author_text:
            painter.setFont(author_font)
            painter.drawText(
                QRect(
                    content_rect.left(),
                    content_rect.top() + line_height,
                    content_rect.width(),
                    line_height,
                ),
                Qt.AlignRight | Qt.AlignVCenter,
                author_text,
            )

    def sizeHint(self) -> QSize:
        return QSize(260, 56)


class MemoryCardButton(QPushButton):
    def __init__(self, value: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.value = value
        self.revealed = False
        self.matched = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(56, 56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText("")

    def reset_state(self) -> None:
        self.revealed = False
        self.matched = False
        self.setEnabled(True)
        self.update()

    def reveal(self) -> None:
        self.revealed = True
        self.update()

    def hide_face(self) -> None:
        if self.matched:
            return
        self.revealed = False
        self.update()

    def mark_matched(self) -> None:
        self.matched = True
        self.revealed = True
        self.setEnabled(False)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        if self.matched:
            fill = QColor(195, 236, 213)
            border = QColor(111, 179, 132)
        elif self.revealed:
            fill = QColor(255, 244, 222)
            border = QColor(219, 162, 79)
        else:
            fill = QColor(231, 241, 253)
            border = QColor(116, 162, 215)

        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 12, 12)

        if self.revealed:
            font = QFont(self.font())
            font.setPointSize(15)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(47, 59, 72))
            painter.drawText(rect, Qt.AlignCenter, str(self.value))
            return

        painter.setClipRect(rect.adjusted(6, 6, -6, -6))
        grid_pen = QPen(QColor(140, 176, 217, 190), 1)
        painter.setPen(grid_pen)
        step = max(10, min(rect.width(), rect.height()) // 4)
        x = rect.left() - (rect.left() % step)
        while x <= rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += step
        y = rect.top() - (rect.top() % step)
        while y <= rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += step

    def sizeHint(self) -> QSize:
        return QSize(64, 64)


class MemoryGameWidget(QWidget):
    completed = Signal(int)
    time_changed = Signal(str)

    DIFFICULTIES: dict[str, tuple[int, int]] = {
        "easy": (3, 4),
        "normal": (4, 4),
        "hard": (4, 5),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._difficulty = "normal"
        self._buttons: list[MemoryCardButton] = []
        self._open_cards: list[MemoryCardButton] = []
        self._matched_pairs = 0
        self._started = False
        self._busy = False
        self._elapsed = QElapsedTimer()

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(8)
        self._layout.setVerticalSpacing(8)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._emit_time)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(550)
        self._hide_timer.timeout.connect(self._hide_open_cards)

        self._emit_time()

    def current_difficulty(self) -> str:
        return self._difficulty

    def is_running(self) -> bool:
        return self._started and self._timer.isActive()

    def stop(self) -> None:
        self._timer.stop()
        self._hide_timer.stop()
        self._busy = False

    def start_new_game(self, difficulty: str) -> None:
        self.stop()
        self._difficulty = difficulty if difficulty in self.DIFFICULTIES else "normal"
        self._open_cards = []
        self._matched_pairs = 0
        self._started = True
        self._busy = False
        self._rebuild_board()
        self._elapsed.restart()
        self._timer.start()
        self._emit_time()

    def _rebuild_board(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._buttons.clear()

        rows, columns = self.DIFFICULTIES[self._difficulty]
        pair_count = rows * columns // 2
        values = list(range(1, pair_count + 1)) * 2
        random.shuffle(values)

        for index, value in enumerate(values):
            button = MemoryCardButton(value, self)
            button.clicked.connect(lambda _checked=False, current=button: self._handle_card_click(current))
            row = index // columns
            column = index % columns
            self._layout.addWidget(button, row, column)
            self._buttons.append(button)

        for row in range(rows):
            self._layout.setRowStretch(row, 1)
        for column in range(columns):
            self._layout.setColumnStretch(column, 1)

    def _handle_card_click(self, button: MemoryCardButton) -> None:
        if self._busy or button.matched or button.revealed:
            return

        button.reveal()
        self._open_cards.append(button)

        if len(self._open_cards) < 2:
            return

        first, second = self._open_cards
        if first.value == second.value:
            first.mark_matched()
            second.mark_matched()
            self._open_cards = []
            self._matched_pairs += 1
            if self._matched_pairs == len(self._buttons) // 2:
                elapsed_ms = self.elapsed_ms()
                self.stop()
                self.completed.emit(elapsed_ms)
            return

        self._busy = True
        self._hide_timer.start()

    def _hide_open_cards(self) -> None:
        for button in self._open_cards:
            button.hide_face()
        self._open_cards = []
        self._busy = False

    def elapsed_ms(self) -> int:
        if not self._started or not self._elapsed.isValid():
            return 0
        return max(0, self._elapsed.elapsed())

    def _emit_time(self) -> None:
        self.time_changed.emit(self.format_elapsed(self.elapsed_ms()))

    @staticmethod
    def format_elapsed(elapsed_ms: int) -> str:
        total_tenths = max(0, elapsed_ms // 100)
        minutes = total_tenths // 600
        seconds = (total_tenths % 600) // 10
        tenths = total_tenths % 10
        return f"{minutes:02d}:{seconds:02d}.{tenths}"


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

        from PySide6.QtCore import QDateTime

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


class TitleBar(QWidget):
    def __init__(self, parent: MainWindow) -> None:
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
