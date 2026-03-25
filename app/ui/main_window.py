import json

from PySide6.QtCore import QDate, QSettings, QSize, Qt, QTime, QTimer
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.core.content_service import ContentService
from app.core.tarot_interpreter import TarotInterpreter
from app.data.storage import TodoStorage
from app.ui.controllers import TarotController, TodoController
from app.ui.pages import MainPageView, SettingsPageView, TarotHistoryPageView, TarotPageView
from app.ui.window_manager import WindowManager
from app.ui.widgets import TitleBar, TodoRowWidget

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


class MainWindow(QMainWindow):
    def __init__(self, storage: TodoStorage) -> None:
        super().__init__()
        self.storage = storage
        self.settings = QSettings("TodoDesktop", "Todo")
        self._is_quitting = False
        self._snap_margin = 24
        self._corner_radius = 22
        self._minimum_size = QSize(470, 480)
        self._fallback_default_size = QSize(470, 520)
        self._window_manager = WindowManager(self)
        self._default_size = self._window_manager.load_default_size()
        self._due_soon_minutes = self._window_manager.load_due_warning_minutes()
        self._geometry_adjusting = False
        self._visible_corner_margin = 44
        self._content_service = ContentService()
        self._tarot_cards = self._content_service.load_tarot_cards()
        self._philosopher_quotes = self._content_service.load_philosopher_quotes()
        self._tarot_interpreter = TarotInterpreter()
        self._todo_controller = TodoController(storage)
        self._tarot_controller = TarotController(
            storage=storage,
            interpreter=self._tarot_interpreter,
            tarot_cards=self._tarot_cards,
            tarot_name_map=TAROT_NAME_ZH,
        )
        self._current_quote = ""

        self.setWindowTitle("Todo")
        self.setMinimumSize(self._minimum_size)
        self.resize(self._default_size)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._window_manager.restore_window_geometry()

        self._setup_ui()
        self._window_manager.setup_tray()
        self.refresh_main_page()
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

        self.page_stack = QFrame(self.panel)
        page_stack_layout = QVBoxLayout(self.page_stack)
        page_stack_layout.setContentsMargins(0, 0, 0, 0)

        self.main_page = MainPageView(self, self.panel, self.page_stack)
        self.settings_page = SettingsPageView(self.page_stack)
        self.tarot_page = TarotPageView(self.page_stack)
        self.tarot_history_page = TarotHistoryPageView(self.page_stack)

        self._alias_main_page_widgets()
        self._alias_settings_page_widgets()
        self._alias_tarot_page_widgets()
        self._alias_tarot_history_widgets()
        self._configure_page_widgets()

        self._pages = [
            self.main_page,
            self.settings_page,
            self.tarot_page,
            self.tarot_history_page,
        ]
        for page in self._pages:
            page.hide()
            page_stack_layout.addWidget(page)

        self._current_page = self.main_page
        self._current_page.show()
        panel_layout.addWidget(self.page_stack)

        main_layout.addWidget(self.panel)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(46)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(12, 18, 28, 110))
        self.panel.setGraphicsEffect(shadow)

        self._apply_styles()

    def _alias_main_page_widgets(self) -> None:
        self.input_edit = self.main_page.input_edit
        self.enable_due_checkbox = self.main_page.enable_due_checkbox
        self.due_popup = self.main_page.due_popup
        self.due_calendar = self.main_page.due_calendar
        self.due_hour_combo = self.main_page.due_hour_combo
        self.due_minute_combo = self.main_page.due_minute_combo
        self.todo_list = self.main_page.todo_list
        self.quote_box = self.main_page.quote_box
        self.resize_handle = self.main_page.resize_handle

    def _alias_settings_page_widgets(self) -> None:
        self.default_width_spin = self.settings_page.default_width_spin
        self.default_height_spin = self.settings_page.default_height_spin
        self.warn_minutes_spin = self.settings_page.warn_minutes_spin

    def _alias_tarot_page_widgets(self) -> None:
        self.tarot_question_edit = self.tarot_page.tarot_question_edit
        self.tarot_card_panel = self.tarot_page.tarot_card_panel
        self.tarot_question_label = self.tarot_page.tarot_question_label
        self.tarot_spread_label = self.tarot_page.tarot_spread_label
        self.tarot_past_box = self.tarot_page.tarot_past_box
        self.tarot_past_name = self.tarot_page.tarot_past_name
        self.tarot_past_body = self.tarot_page.tarot_past_body
        self.tarot_present_box = self.tarot_page.tarot_present_box
        self.tarot_present_name = self.tarot_page.tarot_present_name
        self.tarot_present_body = self.tarot_page.tarot_present_body
        self.tarot_future_box = self.tarot_page.tarot_future_box
        self.tarot_future_name = self.tarot_page.tarot_future_name
        self.tarot_future_body = self.tarot_page.tarot_future_body
        self.tarot_summary_box = self.tarot_page.tarot_summary_box
        self.tarot_summary_body = self.tarot_page.tarot_summary_body

    def _alias_tarot_history_widgets(self) -> None:
        self.tarot_history_list = self.tarot_history_page.tarot_history_list

    def _configure_page_widgets(self) -> None:
        self.input_edit.returnPressed.connect(self.add_todo)
        self.enable_due_checkbox.toggled.connect(self._toggle_due_edit_enabled)
        self.enable_due_checkbox.installEventFilter(self)
        self.due_popup.installEventFilter(self)
        self.due_calendar.clicked.connect(self._on_due_date_changed)
        self.due_hour_combo.currentTextChanged.connect(self._on_due_time_changed)
        self.due_minute_combo.currentTextChanged.connect(self._on_due_time_changed)
        self.main_page.add_button.clicked.connect(self.add_todo)
        self.todo_list.order_changed.connect(self.persist_current_order)
        self.main_page.reset_button.clicked.connect(self._window_manager.restore_default_size)
        self.main_page.config_button.clicked.connect(self._window_manager.show_settings_page)
        self.main_page.tarot_button.clicked.connect(self._window_manager.show_tarot_page)
        self.main_page.delete_button.clicked.connect(self.delete_completed)
        self.main_page.refresh_button.clicked.connect(self.refresh_main_page)

        self.default_width_spin.setRange(self._minimum_size.width(), 1200)
        self.default_width_spin.setSingleStep(20)
        self.default_height_spin.setRange(self._minimum_size.height(), 1400)
        self.default_height_spin.setSingleStep(20)
        self.warn_minutes_spin.setRange(10, 1440)
        self.warn_minutes_spin.setSingleStep(10)
        self.warn_minutes_spin.setSuffix(" min")
        self.settings_page.back_button.clicked.connect(self._window_manager.show_main_page)
        self.settings_page.use_current_size_button.clicked.connect(self._window_manager.save_current_size_as_default)
        self.settings_page.save_button.clicked.connect(self._window_manager.save_settings)

        self.tarot_page.draw_button.clicked.connect(self.draw_tarot_spread)
        self.tarot_page.history_button.clicked.connect(self._window_manager.show_tarot_history_page)
        self.tarot_page.back_button.clicked.connect(self._window_manager.show_main_page)

        self.tarot_history_list.itemClicked.connect(self.show_tarot_history_item)
        self.tarot_history_page.back_button.clicked.connect(self._window_manager.show_tarot_page)

        self._due_date = self.due_calendar.selectedDate()
        hour = int(self.due_hour_combo.currentText())
        minute = int(self.due_minute_combo.currentText())
        self._due_time = QTime(hour, minute, 0)

        self._due_popup_hide_timer = QTimer(self)
        self._due_popup_hide_timer.setSingleShot(True)
        self._due_popup_hide_timer.setInterval(150)
        self._due_popup_hide_timer.timeout.connect(self._hide_due_popup_if_outside)

        self._due_popup_show_timer = QTimer(self)
        self._due_popup_show_timer.setSingleShot(True)
        self._due_popup_show_timer.setInterval(180)
        self._due_popup_show_timer.timeout.connect(self._show_due_popup)

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
            #quoteBox {{
                background-color: rgba(255, 248, 240, 128);
                border: 1px solid rgba(236, 149, 92, 140);
                border-radius: 16px;
                color: rgb(68, 50, 36);
                padding: 10px 12px;
                font-size: 13px;
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

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._window_manager.handle_resize()

    def moveEvent(self, event) -> None:  # type: ignore[override]
        super().moveEvent(event)
        self._window_manager.handle_move()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._window_manager.handle_close(event)

    def changeEvent(self, event) -> None:  # type: ignore[override]
        if self._window_manager.handle_change(event):
            return
        super().changeEvent(event)

    def hide_to_tray(self) -> None:
        self._window_manager.hide_to_tray()

    def toggle_visibility(self) -> None:
        self._window_manager.toggle_visibility()

    def quit_application(self) -> None:
        self._window_manager.quit_application()

    def snap_to_edge(self) -> None:
        self._window_manager.snap_to_edge()

    def show_tarot_page(self) -> None:
        self._window_manager.show_tarot_page()

    def add_todo(self) -> None:
        text = self.input_edit.text()
        if not text.strip():
            return

        try:
            self._todo_controller.add_todo(
                title=text,
                due_enabled=self.enable_due_checkbox.isChecked(),
                due_date=self._due_date,
                due_time=self._due_time,
            )
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
        return self._todo_controller.is_due_soon(due_at, done, self._due_soon_minutes)

    def refresh_main_page(self) -> None:
        self._refresh_list()
        self._refresh_quote()

    def _refresh_quote(self) -> None:
        self._current_quote = self._content_service.pick_quote_html(
            self._philosopher_quotes,
            current_html=self._current_quote,
        )
        self.quote_box.setHtml(self._current_quote)

    def _refresh_list(self, keep_scroll: bool = False, scroll_to_bottom: bool = False) -> None:
        scroll_bar = self.todo_list.verticalScrollBar()
        previous_scroll = scroll_bar.value()

        self.todo_list.clear()
        for todo in self._todo_controller.list_todos():
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

        self._todo_controller.update_order(todo_ids)
        self._refresh_list(keep_scroll=True)

    def toggle_todo(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        if todo_id is None:
            return

        self._todo_controller.toggle_done(int(todo_id))
        self._refresh_list(keep_scroll=True)

    def delete_completed(self) -> None:
        self._todo_controller.delete_completed()
        self._refresh_list(keep_scroll=True)

    def draw_tarot_spread(self) -> None:
        if not self._tarot_controller.has_cards():
            QMessageBox.warning(self, "Tarot", "Tarot deck is unavailable.")
            return

        question = self.tarot_question_edit.text().strip()
        reading = self._tarot_controller.draw_spread(question)
        self._show_tarot_reading(reading.question, reading.cards, reading.summary)
        self._refresh_tarot_history()

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
            f"Keywords: {past.get('keywords', '-')}"
        )
        self.tarot_present_body.setText(
            f"{present.get('orientation', '-')}\n"
            f"Keywords: {present.get('keywords', '-')}"
        )
        self.tarot_future_body.setText(
            f"{future.get('orientation', '-')}\n"
            f"Keywords: {future.get('keywords', '-')}"
        )
        self.tarot_summary_body.setText(summary)

    def _refresh_tarot_history(self) -> None:
        if not hasattr(self, "tarot_history_list"):
            return

        self.tarot_history_list.clear()
        for reading in self._tarot_controller.list_history(limit=50):
            question = reading.question if reading.question else "No question"
            preview = f"{reading.created_at} | {question}"
            item = QListWidgetItem(preview)
            item.setData(Qt.UserRole, reading.id)
            self.tarot_history_list.addItem(item)

    def show_tarot_history_item(self, item: QListWidgetItem) -> None:
        reading_id = item.data(Qt.UserRole)
        if reading_id is None:
            return

        reading = self._tarot_controller.get_history_item(int(reading_id), limit=200)
        if reading is None:
            return

        self._show_tarot_reading(reading.question, reading.cards, reading.summary)
        self._window_manager.set_current_page(self.tarot_page)
