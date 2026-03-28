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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import (
    ActionIconButton,
    MemoryGameWidget,
    PlaneRunnerGameWidget,
    QuoteBoxWidget,
    ReorderableTodoListWidget,
    ResizeHandle,
)

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

        self.quote_box = QuoteBoxWidget(self)
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
        self.ai_api_key_edit = QLineEdit(self)
        self.ai_base_url_edit = QLineEdit(self)
        self.ai_model_edit = QLineEdit(self)
        self.ai_api_key_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.ai_base_url_edit.setPlaceholderText("https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.ai_model_edit.setPlaceholderText("qwen-max")
        self.test_ai_button = QPushButton("test AI")
        self.back_button = QPushButton("back")
        self.use_current_size_button = QPushButton("use current size")
        self.save_button = QPushButton("save")

        form_layout.addRow("Default Width", self.default_width_spin)
        form_layout.addRow("Default Height", self.default_height_spin)
        form_layout.addRow("Warning", self.warn_minutes_spin)
        form_layout.addRow("API Key", self.ai_api_key_edit)
        form_layout.addRow("Base URL", self.ai_base_url_edit)
        form_layout.addRow("Model", self.ai_model_edit)
        form_layout.addRow("", self.test_ai_button)
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

        self.tarot_question_edit = QLineEdit(self)
        self.tarot_question_edit.setPlaceholderText("Ask a question")
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

        self.loading_overlay = QFrame(self)
        self.loading_overlay.setObjectName("tarotLoadingOverlay")
        self.loading_overlay.hide()

        self.loading_panel = QFrame(self.loading_overlay)
        self.loading_panel.setObjectName("tarotLoadingPanel")

        overlay_layout = QVBoxLayout(self.loading_panel)
        overlay_layout.setContentsMargins(18, 18, 18, 18)
        overlay_layout.setSpacing(12)

        overlay_title = QLabel("AI is reading the cards")
        overlay_title.setStyleSheet("font-size: 17px; font-weight: 800;")
        overlay_layout.addWidget(overlay_title)

        self.loading_status_label = QLabel("Pick a tiny game while you wait.")
        self.loading_status_label.setWordWrap(True)
        self.loading_status_label.setStyleSheet("color: rgba(28, 37, 48, 170);")
        self.loading_status_label.setFixedHeight(38)
        overlay_layout.addWidget(self.loading_status_label)

        overlay_controls = QHBoxLayout()
        overlay_controls.setSpacing(8)

        self.loading_game_combo = QComboBox(self.loading_panel)
        self.loading_game_combo.addItem("Memory", "memory")
        self.loading_game_combo.addItem("Runner", "runner")

        self.loading_difficulty_combo = QComboBox(self.loading_panel)

        self.loading_start_button = QPushButton("start")
        self.loading_close_button = QPushButton("view reading")
        self.loading_close_button.setEnabled(False)

        overlay_controls.addWidget(self.loading_game_combo, 1)
        overlay_controls.addWidget(self.loading_difficulty_combo, 1)
        overlay_controls.addWidget(self.loading_start_button)
        overlay_controls.addWidget(self.loading_close_button)
        overlay_layout.addLayout(overlay_controls)

        info_row = QHBoxLayout()
        info_row.setSpacing(10)
        self.loading_timer_label = QLabel("Timer: 00:00.0")
        self.loading_timer_label.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.loading_best_label = QLabel("Best: --")
        self.loading_best_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.loading_best_label.setStyleSheet("color: rgba(28, 37, 48, 170);")
        info_row.addWidget(self.loading_timer_label)
        info_row.addStretch()
        info_row.addWidget(self.loading_best_label)
        overlay_layout.addLayout(info_row)

        self.loading_game_stack = QStackedWidget(self.loading_panel)
        self.loading_memory_game_widget = MemoryGameWidget(self.loading_game_stack)
        self.loading_runner_game_widget = PlaneRunnerGameWidget(self.loading_game_stack)
        self.loading_game_stack.addWidget(self.loading_memory_game_widget)
        self.loading_game_stack.addWidget(self.loading_runner_game_widget)
        self.loading_game_stack.setFixedHeight(360)
        overlay_layout.addWidget(self.loading_game_stack, 1)

        self.loading_result_label = QLabel("Match all pairs before the reading is ready.")
        self.loading_result_label.setWordWrap(True)
        self.loading_result_label.setStyleSheet("color: rgba(28, 37, 48, 170);")
        self.loading_result_label.setFixedHeight(38)
        overlay_layout.addWidget(self.loading_result_label)

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

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.loading_overlay.setGeometry(self.rect())

        panel_width = min(max(360, self.width() - 44), 560)
        panel_height = min(max(430, self.height() - 54), 620)
        x = max(22, (self.width() - panel_width) // 2)
        y = max(18, (self.height() - panel_height) // 2)
        self.loading_panel.setGeometry(x, y, panel_width, panel_height)


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
