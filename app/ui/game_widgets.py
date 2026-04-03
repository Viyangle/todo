from __future__ import annotations

import random

from PySide6.QtCore import QElapsedTimer, QPoint, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGridLayout, QPushButton, QSizePolicy, QWidget


class MemoryCardButton(QPushButton):
    def __init__(self, value: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.value = value
        self.revealed = False
        self.matched = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(40, 40)
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
            font.setPointSize(max(10, min(15, int(rect.height() * 0.34))))
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
        return QSize(48, 48)


class MemoryGameWidget(QWidget):
    completed = Signal(int)
    time_changed = Signal(str)

    DIFFICULTIES: dict[str, tuple[int, int]] = {
        "easy": (3, 4),
        "normal": (4, 4),
        "hard": (4, 5),
        "hell": (5, 8),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._difficulty = "easy"
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

    def preview_difficulty(self, difficulty: str) -> None:
        self.stop()
        self._difficulty = difficulty if difficulty in self.DIFFICULTIES else "normal"
        self._open_cards = []
        self._matched_pairs = 0
        self._started = False
        self._busy = False
        self._rebuild_board()
        self._emit_time()

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
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        self._buttons.clear()

        max_rows = max(rows for rows, _columns in self.DIFFICULTIES.values())
        max_columns = max(columns for _rows, columns in self.DIFFICULTIES.values())
        for row in range(max_rows):
            self._layout.setRowStretch(row, 0)
            self._layout.setRowMinimumHeight(row, 0)
        for column in range(max_columns):
            self._layout.setColumnStretch(column, 0)
            self._layout.setColumnMinimumWidth(column, 0)

        rows, columns = self.DIFFICULTIES[self._difficulty]
        if self._difficulty == "hell":
            self._layout.setHorizontalSpacing(6)
            self._layout.setVerticalSpacing(6)
        else:
            self._layout.setHorizontalSpacing(8)
            self._layout.setVerticalSpacing(8)
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
        self.updateGeometry()
        self.update()

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


class PlaneRunnerGameWidget(QWidget):
    completed = Signal(int)
    time_changed = Signal(str)

    DIFFICULTY_LIVES = {
        "easy": 3,
        "hard": 3,
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._difficulty = "easy"
        self._lane = 1
        self._column = 0
        self._lives = 3
        self._max_lives = 3
        self._running = False
        self._elapsed = QElapsedTimer()
        self._obstacles: list[dict[str, float | int | bool]] = []
        self._spawn_timer = 0.0
        self._heart_spawn_timer = 0.0
        self._diamond_spawn_timer = 0.0
        self._speed = 210.0
        self._max_speed = 700.0
        self._acceleration = 8.0
        self._plane_flash_ms = 0
        self._last_hard_safe_lane: int | None = None
        self._score = 0.0

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(210)

        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(30)
        self._frame_timer.timeout.connect(self._tick)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(100)
        self._clock_timer.timeout.connect(self._emit_time)
        self._emit_time()

    def current_difficulty(self) -> str:
        return self._difficulty

    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        self._running = False
        self._frame_timer.stop()
        self._clock_timer.stop()
        self.update()

    def preview_difficulty(self, difficulty: str) -> None:
        self.stop()
        self._difficulty = difficulty if difficulty in self.DIFFICULTY_LIVES else "easy"
        self._lane = 1
        self._column = 0
        self._max_lives = self.DIFFICULTY_LIVES[self._difficulty]
        self._lives = self._max_lives
        self._obstacles = []
        self._spawn_timer = 0.0
        self._heart_spawn_timer = 0.0
        self._diamond_spawn_timer = 0.0
        self._speed = 210.0
        self._plane_flash_ms = 0
        self._last_hard_safe_lane = None
        self._score = 0.0
        self._emit_time()
        self.update()

    def start_new_game(self, difficulty: str) -> None:
        self._difficulty = difficulty if difficulty in self.DIFFICULTY_LIVES else "easy"
        self._lane = 1
        self._column = 0
        self._max_lives = self.DIFFICULTY_LIVES[self._difficulty]
        self._lives = self._max_lives
        self._obstacles = []
        self._spawn_timer = 0.4
        self._heart_spawn_timer = random.uniform(17.0, 23.0)
        self._diamond_spawn_timer = random.uniform(55.0, 65.0)
        self._speed = 210.0
        self._plane_flash_ms = 0
        self._last_hard_safe_lane = None
        self._score = 0.0
        self._running = True
        self._elapsed.restart()
        self._frame_timer.start()
        self._clock_timer.start()
        self._emit_time()
        self.setFocus(Qt.OtherFocusReason)
        self.update()

    def elapsed_ms(self) -> int:
        if not self._elapsed.isValid():
            return 0
        return max(0, self._elapsed.elapsed())

    def score(self) -> int:
        return max(0, int(self._score))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        if key == Qt.Key_A:
            self._column = max(0, self._column - 1)
            self.update()
            return
        if key == Qt.Key_D:
            self._column = min(2, self._column + 1)
            self.update()
            return
        if key == Qt.Key_W:
            self._lane = max(0, self._lane - 1)
            self.update()
            return
        if key == Qt.Key_S:
            self._lane = min(2, self._lane + 1)
            self.update()
            return
        super().keyPressEvent(event)

    def _tick(self) -> None:
        if not self._running:
            return

        dt = self._frame_timer.interval() / 1000.0
        self._speed = min(self._max_speed, self._speed + self._acceleration * dt)
        speed_ratio = max(0.0, (self._speed - 210.0) / max(1.0, self._max_speed - 210.0))
        points_per_second = 10.0 + speed_ratio * 14.0
        self._score += points_per_second * dt
        self._spawn_timer -= dt
        if self._spawn_timer <= 0:
            self._spawn_meteor_pattern()
            self._spawn_timer = max(0.28, 1.0 - (self._speed - 210.0) / 210.0)

        self._heart_spawn_timer -= dt
        if self._heart_spawn_timer <= 0:
            self._spawn_heart()
            self._heart_spawn_timer = random.uniform(18.0, 24.0)

        self._diamond_spawn_timer -= dt
        if self._diamond_spawn_timer <= 0:
            self._spawn_diamond()
            self._diamond_spawn_timer = random.uniform(55.0, 65.0)

        if self._plane_flash_ms > 0:
            self._plane_flash_ms = max(0, self._plane_flash_ms - self._frame_timer.interval())

        for obstacle in self._obstacles:
            obstacle["x"] = float(obstacle["x"]) - self._speed * dt

        plane_rect = self._plane_rect()
        for obstacle in self._obstacles:
            if obstacle["lane"] != self._lane or bool(obstacle["hit"]):
                continue
            if plane_rect.intersects(self._obstacle_rect(obstacle)):
                obstacle["hit"] = True
                if obstacle["kind"] == "heart":
                    self._lives = min(self._max_lives, self._lives + 1)
                    continue
                if obstacle["kind"] == "diamond":
                    self._score += 500
                    continue

                self._lives -= 1
                self._plane_flash_ms = 220
                if self._lives <= 0:
                    final_score = self.score()
                    self.stop()
                    self.completed.emit(final_score)
                    break

        self._obstacles = [
            obstacle for obstacle in self._obstacles
            if float(obstacle["x"]) + self._obstacle_size() > -10 and not bool(obstacle["hit"])
        ]
        self.update()

    def _spawn_meteor_pattern(self) -> None:
        spawn_x = self._next_spawn_x()
        if self._difficulty == "hard" and random.random() < 0.34:
            safe_lane_candidates = [0, 1, 2]
            if self._last_hard_safe_lane is not None:
                safe_lane_candidates = [
                    lane for lane in safe_lane_candidates
                    if abs(lane - self._last_hard_safe_lane) <= 1
                ]
            safe_lane = random.choice(safe_lane_candidates)
            lanes = [lane for lane in range(3) if lane != safe_lane]
            for lane in lanes:
                self._spawn_meteor(lane, spawn_x)
            self._last_hard_safe_lane = safe_lane
            return

        lane = random.randint(0, 2)
        self._spawn_meteor(lane, spawn_x)
        self._last_hard_safe_lane = None

    def _spawn_meteor(self, lane: int, spawn_x: float | None = None) -> None:
        self._obstacles.append(
            {"kind": "meteor", "lane": lane, "x": spawn_x if spawn_x is not None else self._next_spawn_x(), "hit": False}
        )

    def _spawn_heart(self) -> None:
        self._obstacles.append({"kind": "heart", "lane": random.randint(0, 2), "x": self._next_spawn_x(), "hit": False})

    def _spawn_diamond(self) -> None:
        self._obstacles.append(
            {"kind": "diamond", "lane": random.randint(0, 2), "x": self._next_spawn_x(), "hit": False}
        )

    def _next_spawn_x(self) -> float:
        base_x = float(self.width() + self._obstacle_size() + random.randint(12, 42))
        min_gap = float(self._plane_size() * 2 + self._obstacle_size() + 28)
        active_x = [float(obstacle["x"]) for obstacle in self._obstacles if not bool(obstacle["hit"])]
        if not active_x:
            return base_x
        return max(base_x, max(active_x) + min_gap)

    def _track_top(self, lane: int) -> int:
        header = 34
        playable_height = max(120, self.height() - header - 20)
        lane_gap = playable_height / 3
        return int(header + lane * lane_gap)

    def _track_height(self) -> int:
        return max(42, (self.height() - 54) // 3)

    def _plane_size(self) -> int:
        return max(26, min(38, self.width() // 13))

    def _obstacle_size(self) -> int:
        return max(24, min(34, self.width() // 15))

    def _plane_rect(self) -> QRectF:
        size = self._plane_size()
        positions = self._plane_x_positions(size)
        lane_top = self._track_top(self._lane)
        lane_height = self._track_height()
        return QRectF(positions[self._column], lane_top + (lane_height - size) / 2, size, size)

    def _plane_x_positions(self, size: int) -> list[float]:
        base = 42.0
        spacing = max(44.0, size + 18.0)
        return [base + spacing * index for index in range(3)]

    def _obstacle_rect(self, obstacle: dict[str, float | int | bool]) -> QRectF:
        size = self._obstacle_size()
        lane = int(obstacle["lane"])
        lane_top = self._track_top(lane)
        lane_height = self._track_height()
        return QRectF(float(obstacle["x"]), lane_top + (lane_height - size) / 2, size, size)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(225, 238, 250, 160))

        self._paint_tracks(painter)
        self._paint_obstacles(painter)
        self._paint_plane(painter)
        self._paint_hud(painter)

    def _paint_tracks(self, painter: QPainter) -> None:
        for lane in range(3):
            track_top = self._track_top(lane)
            track_rect = QRectF(18, track_top, self.width() - 36, self._track_height())
            painter.setPen(QPen(QColor(172, 196, 220), 1.2))
            painter.setBrush(QColor(241, 247, 255, 190))
            painter.drawRoundedRect(track_rect, 18, 18)

            dash_pen = QPen(QColor(156, 180, 205), 1.4)
            dash_pen.setDashPattern([5, 7])
            painter.setPen(dash_pen)
            mid_y = track_rect.center().y()
            painter.drawLine(int(track_rect.left() + 10), int(mid_y), int(track_rect.right() - 10), int(mid_y))

    def _paint_plane(self, painter: QPainter) -> None:
        rect = self._plane_rect()
        painter.save()
        if self._plane_flash_ms and (self._plane_flash_ms // 60) % 2 == 0:
            painter.setOpacity(0.35)

        body = QPainterPath()
        body.moveTo(rect.left() + rect.width() * 0.05, rect.center().y())
        body.lineTo(rect.left() + rect.width() * 0.45, rect.top() + rect.height() * 0.2)
        body.lineTo(rect.right() - rect.width() * 0.06, rect.center().y())
        body.lineTo(rect.left() + rect.width() * 0.45, rect.bottom() - rect.height() * 0.2)
        body.closeSubpath()

        wing = QPainterPath()
        wing.moveTo(rect.left() + rect.width() * 0.3, rect.center().y())
        wing.lineTo(rect.left() + rect.width() * 0.58, rect.top() + rect.height() * 0.08)
        wing.lineTo(rect.left() + rect.width() * 0.55, rect.center().y())
        wing.lineTo(rect.left() + rect.width() * 0.58, rect.bottom() - rect.height() * 0.08)
        wing.closeSubpath()

        painter.setPen(QPen(QColor(62, 106, 156), 1.4))
        painter.setBrush(QColor(94, 153, 220))
        painter.drawPath(body)
        painter.setBrush(QColor(245, 250, 255))
        painter.drawPath(wing)
        painter.setBrush(QColor(255, 204, 118))
        painter.drawEllipse(
            QRectF(rect.left() + rect.width() * 0.15, rect.top() + rect.height() * 0.34, rect.width() * 0.18, rect.height() * 0.18)
        )
        painter.restore()

    def _paint_obstacles(self, painter: QPainter) -> None:
        for obstacle in self._obstacles:
            rect = self._obstacle_rect(obstacle)
            hit = bool(obstacle["hit"])
            if obstacle["kind"] == "heart":
                self._draw_heart(painter, QPoint(int(rect.left()), int(rect.top())), int(rect.width()), QColor(234, 90, 111) if not hit else QColor(246, 170, 181))
                continue
            if obstacle["kind"] == "diamond":
                self._draw_diamond(painter, rect, QColor(90, 200, 235) if not hit else QColor(178, 229, 245))
                continue

            fill = QColor(231, 139, 94) if hit else QColor(92, 103, 124)
            border = QColor(201, 112, 70) if hit else QColor(61, 71, 87)
            painter.setPen(QPen(border, 1.2))
            painter.setBrush(fill)
            painter.drawEllipse(rect)

            painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
            painter.drawLine(int(rect.left() + rect.width() * 0.28), int(rect.top() + rect.height() * 0.24), int(rect.left() + rect.width() * 0.62), int(rect.top() + rect.height() * 0.6))
            painter.drawLine(int(rect.left() + rect.width() * 0.52), int(rect.top() + rect.height() * 0.16), int(rect.left() + rect.width() * 0.75), int(rect.top() + rect.height() * 0.46))

    def _paint_hud(self, painter: QPainter) -> None:
        heart_size = 16
        heart_gap = 5
        for index in range(self._lives):
            x = self.width() - 22 - (index + 1) * heart_size - index * heart_gap
            self._draw_heart(painter, QPoint(x, 10), heart_size, QColor(234, 90, 111))

        if not self._running and self._elapsed.isValid() and self.elapsed_ms() > 0:
            painter.setPen(QColor(77, 89, 108))
            painter.drawText(self.rect().adjusted(0, 0, 0, -8), Qt.AlignBottom | Qt.AlignHCenter, "Crashed. Press restart to fly again.")

    def _draw_heart(self, painter: QPainter, top_left: QPoint, size: int, color: QColor) -> None:
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        path = QPainterPath()
        path.moveTo(top_left.x() + size / 2, top_left.y() + size)
        path.cubicTo(top_left.x() - size * 0.15, top_left.y() + size * 0.62, top_left.x(), top_left.y() + size * 0.05, top_left.x() + size * 0.28, top_left.y() + size * 0.05)
        path.cubicTo(top_left.x() + size * 0.48, top_left.y() + size * 0.05, top_left.x() + size / 2, top_left.y() + size * 0.28, top_left.x() + size / 2, top_left.y() + size * 0.32)
        path.cubicTo(top_left.x() + size / 2, top_left.y() + size * 0.28, top_left.x() + size * 0.52, top_left.y() + size * 0.05, top_left.x() + size * 0.72, top_left.y() + size * 0.05)
        path.cubicTo(top_left.x() + size, top_left.y() + size * 0.05, top_left.x() + size * 1.15, top_left.y() + size * 0.62, top_left.x() + size / 2, top_left.y() + size)
        painter.drawPath(path)
        painter.restore()

    def _draw_diamond(self, painter: QPainter, rect: QRectF, color: QColor) -> None:
        painter.save()
        painter.setPen(QPen(QColor(56, 132, 164), 1.2))
        painter.setBrush(color)
        path = QPainterPath()
        path.moveTo(rect.center().x(), rect.top())
        path.lineTo(rect.right(), rect.center().y())
        path.lineTo(rect.center().x(), rect.bottom())
        path.lineTo(rect.left(), rect.center().y())
        path.closeSubpath()
        painter.drawPath(path)
        painter.setPen(QPen(QColor(236, 250, 255, 170), 1))
        painter.drawLine(int(rect.center().x()), int(rect.top() + 3), int(rect.center().x()), int(rect.bottom() - 3))
        painter.drawLine(int(rect.left() + 3), int(rect.center().y()), int(rect.right() - 3), int(rect.center().y()))
        painter.restore()

    def _emit_time(self) -> None:
        self.time_changed.emit(self.format_elapsed(self.score()))

    @staticmethod
    def format_elapsed(score: int) -> str:
        return f"{max(0, int(score)):,}"
