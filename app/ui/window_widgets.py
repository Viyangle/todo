from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

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
        author_text = f" —— {self._author}" if self._author else ""

        author_font = QFont(quote_font)
        author_font.setBold(True)
        author_metrics = QFontMetrics(author_font)
        author_width = author_metrics.horizontalAdvance(author_text) if author_text else 0
        reserved_width = author_width + 6 if author_text else 0

        first_line_rect = QRect(content_rect.left(), content_rect.top(), content_rect.width(), line_height)
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
