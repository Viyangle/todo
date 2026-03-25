from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import ActionIconButton, ReorderableTodoListWidget, ResizeHandle

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow


class MainPageView(QWidget):
    def __init__(self, window: MainWindow, panel_parent: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter a task and press Enter")
        self.input_edit.setMinimumWidth(230)

        self.enable_due_checkbox = QCheckBox("due")

        self.due_popup = QFrame(panel_parent)
        self.due_popup.setObjectName("duePopup")
        self.due_popup.setFrameShape(QFrame.StyledPanel)
        self.due_popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.due_popup.setAttribute(Qt.WA_ShowWithoutActivating, True)

        popup_layout = QVBoxLayout(self.due_popup)
        popup_layout.setContentsMargins(10, 10, 10, 10)
        popup_layout.setSpacing(8)

        tomorrow = QDate.currentDate().addDays(1)
        current_time = QTime.currentTime()

        self.due_calendar = QCalendarWidget(self.due_popup)
        self.due_calendar.setSelectedDate(tomorrow)
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

        rounded_minute = (current_time.minute() // 5) * 5
        self.due_hour_combo.setCurrentText(f"{current_time.hour():02d}")
        self.due_minute_combo.setCurrentText(f"{rounded_minute:02d}")

        time_row.addWidget(time_label)
        time_row.addWidget(self.due_hour_combo)
        time_row.addWidget(self.due_minute_combo)
        popup_layout.addLayout(time_row)

        self.add_button = ActionIconButton("add")

        input_layout.addWidget(self.input_edit, 1)
        input_layout.addWidget(self.enable_due_checkbox)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        self.todo_list = ReorderableTodoListWidget()
        layout.addWidget(self.todo_list)

        self.quote_box = QTextEdit(self)
        self.quote_box.setReadOnly(True)
        self.quote_box.setObjectName("quoteBox")
        self.quote_box.setFixedHeight(108)
        self.quote_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.quote_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.quote_box)

        action_layout = QHBoxLayout()
        self.reset_button = QPushButton("default")
        self.config_button = QPushButton("config")
        self.tarot_button = QPushButton("tarot")
        self.delete_button = QPushButton("clear")
        self.refresh_button = QPushButton("refresh")
        self.resize_handle = ResizeHandle(window, panel_parent)

        action_layout.addWidget(self.reset_button)
        action_layout.addWidget(self.config_button)
        action_layout.addWidget(self.tarot_button)
        action_layout.addStretch()
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.resize_handle, 0, Qt.AlignRight | Qt.AlignBottom)
        layout.addLayout(action_layout)


class SettingsPageView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)

        self.default_width_spin = QSpinBox(self)
        self.default_height_spin = QSpinBox(self)
        self.warn_minutes_spin = QSpinBox(self)
        self.back_button = QPushButton("back")
        self.use_current_size_button = QPushButton("use current size")
        self.save_button = QPushButton("save")

        form_layout.addRow("Default Width", self.default_width_spin)
        form_layout.addRow("Default Height", self.default_height_spin)
        form_layout.addRow("Warning", self.warn_minutes_spin)
        layout.addLayout(form_layout)

        layout.addStretch()

        actions = QHBoxLayout()
        actions.addWidget(self.back_button)
        actions.addWidget(self.use_current_size_button)
        actions.addStretch()
        actions.addWidget(self.save_button)
        layout.addLayout(actions)


class TarotPageView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Tarot")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        hint = QLabel("Three-card spread: Past / Present / Future")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgba(28, 37, 48, 170);")
        layout.addWidget(hint)

        self.tarot_question_edit = QLineEdit(self)
        self.tarot_question_edit.setPlaceholderText("e.g. What should I focus on this afternoon?")
        layout.addWidget(self.tarot_question_edit)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.draw_button = QPushButton("draw three cards")
        self.history_button = QPushButton("history")
        controls.addWidget(self.draw_button)
        controls.addStretch()
        controls.addWidget(self.history_button)
        layout.addLayout(controls)

        self.tarot_card_panel = QFrame(self)
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

        self.tarot_past_box, self.tarot_past_name, self.tarot_past_body = self._build_card_box("Past")
        self.tarot_present_box, self.tarot_present_name, self.tarot_present_body = self._build_card_box("Present")
        self.tarot_future_box, self.tarot_future_name, self.tarot_future_body = self._build_card_box("Future")

        self.tarot_summary_box = QFrame(self.tarot_card_panel)
        self.tarot_summary_box.setObjectName("tarotSummaryBox")
        summary_layout = QVBoxLayout(self.tarot_summary_box)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        tarot_summary_title = QLabel("Interpretation")
        tarot_summary_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.tarot_summary_body = QLabel("Draw a spread to see the interpretation.")
        self.tarot_summary_body.setWordWrap(True)
        self.tarot_summary_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.tarot_summary_body.setStyleSheet("font-size: 15px;")
        summary_layout.addWidget(tarot_summary_title)
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

        layout.addWidget(self.tarot_card_panel)
        layout.addStretch()

        actions = QHBoxLayout()
        self.back_button = QPushButton("back")
        actions.addWidget(self.back_button)
        actions.addStretch()
        layout.addLayout(actions)

    def _build_card_box(self, title: str) -> tuple[QFrame, QLabel, QLabel]:
        box = QFrame(self.tarot_card_panel)
        box.setObjectName("tarotCardBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: 700;")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setMinimumHeight(22)

        name_label = QLabel("-")
        name_label.setObjectName("tarotCardName")
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_label.setMinimumHeight(30)

        body_label = QLabel("No card yet.")
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        box_layout.addWidget(title_label)
        box_layout.addWidget(name_label)
        box_layout.addWidget(body_label)
        box_layout.addStretch()
        return box, name_label, body_label


class TarotHistoryPageView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Tarot History")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        self.tarot_history_list = QListWidget(self)
        layout.addWidget(self.tarot_history_list)

        actions = QHBoxLayout()
        self.back_button = QPushButton("back")
        actions.addWidget(self.back_button)
        actions.addStretch()
        layout.addLayout(actions)
