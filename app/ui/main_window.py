from __future__ import annotations

from PySide6.QtCore import QDate, QSettings, QSize, Qt, QTime, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.core.bangumi_service import BangumiService
from app.core.content_service import ContentService
from app.core.tarot_interpreter import TarotInterpreter
from app.data.storage import TodoStorage
from app.ui.controllers import BangumiController, TarotController, TodoController
from app.ui.main_window_bangumi import BangumiWindowMixin
from app.ui.main_window_tarot import TarotWindowMixin, _safe_tarot_name_map
from app.ui.main_window_todo import TodoWindowMixin
from app.ui.pages import BangumiPageView, MainPageView, SettingsPageView, TarotHistoryPageView, TarotPageView
from app.ui.window_manager import WindowManager
from app.ui.window_widgets import TitleBar


class MainWindow(TodoWindowMixin, TarotWindowMixin, BangumiWindowMixin, QMainWindow):
    def __init__(self, storage: TodoStorage) -> None:
        super().__init__()
        self.storage = storage
        self.settings = QSettings("TodoDesktop", "Todo")
        self._reset_runner_scores_once()
        self._is_quitting = False
        self._snap_margin = 24
        self._corner_radius = 22
        self._minimum_size = QSize(665, 720)
        self._fallback_default_size = QSize(665, 720)
        self._window_manager = WindowManager(self)
        self._default_size = self._window_manager.load_default_size()
        self._due_soon_minutes = self._window_manager.load_due_warning_minutes()
        self._bangumi_min_votes = self._window_manager.load_bangumi_min_votes()
        self._geometry_adjusting = False
        self._visible_corner_margin = 44
        self._content_service = ContentService()
        self._bangumi_service = BangumiService(cache_dir=storage.db_path.parent / "bangumi_cache")
        self._tarot_cards = self._content_service.load_tarot_cards()
        self._philosopher_quotes = self._content_service.load_philosopher_quotes()
        self._tarot_interpreter = TarotInterpreter(self._load_ai_config())
        self._todo_controller = TodoController(storage)
        self._bangumi_controller = BangumiController(self._bangumi_service)
        self._tarot_controller = TarotController(
            storage=storage,
            interpreter=self._tarot_interpreter,
            tarot_cards=self._tarot_cards,
            tarot_name_map=_safe_tarot_name_map(),
        )
        self._current_quote: dict[str, str] | None = None
        self._tarot_thread = None
        self._tarot_worker = None
        self._tarot_loading = False
        self._tarot_result_ready = False
        self._todo_filter = "all"

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
        QTimer.singleShot(0, self._prompt_for_ai_setup_if_needed)

    def _reset_runner_scores_once(self) -> None:
        migration_key = "games/runner_score_reset_v2"
        if self.settings.value(migration_key, False, type=bool):
            return
        self.settings.remove("games/runner_best_ms")
        self.settings.setValue(migration_key, True)

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
        self.bangumi_page = BangumiPageView(self.page_stack)

        self._alias_main_page_widgets()
        self._alias_settings_page_widgets()
        self._alias_tarot_page_widgets()
        self._alias_tarot_history_widgets()
        self._alias_bangumi_page_widgets()
        self._configure_page_widgets()

        self._pages = [self.main_page, self.settings_page, self.tarot_page, self.tarot_history_page, self.bangumi_page]
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
        self.filter_all_button = self.main_page.filter_all_button
        self.filter_today_button = self.main_page.filter_today_button
        self.filter_future_button = self.main_page.filter_future_button
        self.filter_overdue_button = self.main_page.filter_overdue_button
        self.filter_longterm_button = self.main_page.filter_longterm_button

    def _alias_settings_page_widgets(self) -> None:
        self.default_width_spin = self.settings_page.default_width_spin
        self.default_height_spin = self.settings_page.default_height_spin
        self.warn_minutes_spin = self.settings_page.warn_minutes_spin
        self.bangumi_min_votes_spin = self.settings_page.bangumi_min_votes_spin
        self.ai_api_key_edit = self.settings_page.ai_api_key_edit
        self.ai_base_url_edit = self.settings_page.ai_base_url_edit
        self.ai_model_edit = self.settings_page.ai_model_edit
        self.test_ai_button = self.settings_page.test_ai_button
        self.export_data_button = self.settings_page.export_data_button
        self.import_data_button = self.settings_page.import_data_button

    def _alias_tarot_page_widgets(self) -> None:
        self.tarot_question_edit = self.tarot_page.tarot_question_edit
        self.tarot_spread_combo = self.tarot_page.spread_combo
        self.tarot_card_panel = self.tarot_page.tarot_card_panel
        self.tarot_spread_label = self.tarot_page.tarot_spread_label
        self.tarot_past_box = self.tarot_page.tarot_past_box
        self.tarot_past_title = self.tarot_page.tarot_past_title
        self.tarot_past_name = self.tarot_page.tarot_past_name
        self.tarot_past_body = self.tarot_page.tarot_past_body
        self.tarot_present_box = self.tarot_page.tarot_present_box
        self.tarot_present_title = self.tarot_page.tarot_present_title
        self.tarot_present_name = self.tarot_page.tarot_present_name
        self.tarot_present_body = self.tarot_page.tarot_present_body
        self.tarot_future_box = self.tarot_page.tarot_future_box
        self.tarot_future_title = self.tarot_page.tarot_future_title
        self.tarot_future_name = self.tarot_page.tarot_future_name
        self.tarot_future_body = self.tarot_page.tarot_future_body
        self.tarot_summary_box = self.tarot_page.tarot_summary_box
        self.tarot_summary_body = self.tarot_page.tarot_summary_body
        self.tarot_loading_overlay = self.tarot_page.loading_overlay
        self.tarot_loading_status_label = self.tarot_page.loading_status_label
        self.tarot_loading_game_combo = self.tarot_page.loading_game_combo
        self.tarot_loading_difficulty_combo = self.tarot_page.loading_difficulty_combo
        self.tarot_loading_start_button = self.tarot_page.loading_start_button
        self.tarot_loading_close_button = self.tarot_page.loading_close_button
        self.tarot_loading_timer_label = self.tarot_page.loading_timer_label
        self.tarot_loading_best_label = self.tarot_page.loading_best_label
        self.tarot_loading_game_stack = self.tarot_page.loading_game_stack
        self.tarot_loading_memory_game_widget = self.tarot_page.loading_memory_game_widget
        self.tarot_loading_runner_game_widget = self.tarot_page.loading_runner_game_widget
        self.tarot_loading_result_label = self.tarot_page.loading_result_label

    def _alias_tarot_history_widgets(self) -> None:
        self.tarot_history_list = self.tarot_history_page.tarot_history_list
        self.tarot_history_favorites_only_checkbox = self.tarot_history_page.favorites_only_checkbox

    def _alias_bangumi_page_widgets(self) -> None:
        self.bangumi_year_spin = self.bangumi_page.year_spin
        self.bangumi_ranking_combo = self.bangumi_page.ranking_combo
        self.bangumi_limit_combo = self.bangumi_page.limit_combo
        self.bangumi_min_heat_checkbox = self.bangumi_page.min_heat_checkbox
        self.bangumi_fetch_button = self.bangumi_page.fetch_button
        self.bangumi_recommend_button = self.bangumi_page.recommend_button
        self.bangumi_progress_bar = self.bangumi_page.progress_bar
        self.bangumi_recommendation_label = self.bangumi_page.recommendation_label
        self.bangumi_results_list = self.bangumi_page.results_list

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
        self.todo_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.todo_list.customContextMenuRequested.connect(self._show_todo_context_menu)
        self.main_page.reset_button.clicked.connect(self._window_manager.restore_default_size)
        self.main_page.config_button.clicked.connect(self._window_manager.show_settings_page)
        self.main_page.tarot_button.clicked.connect(self._window_manager.show_tarot_page)
        self.main_page.bangumi_button.clicked.connect(self._window_manager.show_bangumi_page)
        self.main_page.delete_button.clicked.connect(self.delete_completed)
        self.main_page.refresh_button.clicked.connect(self.refresh_main_page)
        self.filter_all_button.clicked.connect(lambda: self.set_todo_filter("all"))
        self.filter_today_button.clicked.connect(lambda: self.set_todo_filter("today"))
        self.filter_future_button.clicked.connect(lambda: self.set_todo_filter("future_3_days"))
        self.filter_overdue_button.clicked.connect(lambda: self.set_todo_filter("overdue"))
        self.filter_longterm_button.clicked.connect(lambda: self.set_todo_filter("long_term"))

        self.default_width_spin.setRange(self._minimum_size.width(), 1200)
        self.default_width_spin.setSingleStep(20)
        self.default_height_spin.setRange(self._minimum_size.height(), 1400)
        self.default_height_spin.setSingleStep(20)
        self.warn_minutes_spin.setRange(10, 1440)
        self.warn_minutes_spin.setSingleStep(10)
        self.warn_minutes_spin.setSuffix(" min")
        self.bangumi_min_votes_spin.setRange(0, 100000)
        self.bangumi_min_votes_spin.setSingleStep(100)
        self.settings_page.back_button.clicked.connect(self._window_manager.show_main_page)
        self.settings_page.use_current_size_button.clicked.connect(self._window_manager.save_current_size_as_default)
        self.settings_page.save_button.clicked.connect(self._window_manager.save_settings)
        self.test_ai_button.clicked.connect(self.test_ai_connection)
        self.export_data_button.clicked.connect(self.export_data_to_file)
        self.import_data_button.clicked.connect(self.import_data_from_file)

        self.tarot_page.draw_button.clicked.connect(self.draw_tarot_spread)
        self.tarot_page.history_button.clicked.connect(self._window_manager.show_tarot_history_page)
        self.tarot_page.back_button.clicked.connect(self._window_manager.show_main_page)
        self.tarot_spread_combo.currentIndexChanged.connect(self._on_tarot_spread_changed)
        self.tarot_loading_game_combo.currentIndexChanged.connect(self._on_loading_game_changed)
        self.tarot_loading_difficulty_combo.currentIndexChanged.connect(self._on_loading_difficulty_changed)
        self.tarot_loading_start_button.clicked.connect(self._start_loading_game)
        self.tarot_loading_close_button.clicked.connect(self._close_tarot_loading_overlay)
        self.tarot_loading_memory_game_widget.time_changed.connect(self._update_loading_game_timer)
        self.tarot_loading_memory_game_widget.completed.connect(
            lambda elapsed_ms: self._finish_loading_game("memory", elapsed_ms)
        )
        self.tarot_loading_runner_game_widget.time_changed.connect(self._update_loading_game_timer)
        self.tarot_loading_runner_game_widget.completed.connect(
            lambda elapsed_ms: self._finish_loading_game("runner", elapsed_ms)
        )

        self.tarot_history_list.itemClicked.connect(self.show_tarot_history_item)
        self.tarot_history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tarot_history_list.customContextMenuRequested.connect(self._show_tarot_history_context_menu)
        self.tarot_history_favorites_only_checkbox.toggled.connect(self._refresh_tarot_history)
        self.tarot_history_page.back_button.clicked.connect(self._window_manager.show_tarot_page)
        self._configure_tarot_spreads()
        self._configure_bangumi_page()
        self.bangumi_min_heat_checkbox.toggled.connect(self._on_bangumi_min_heat_toggled)
        self.bangumi_fetch_button.clicked.connect(self.load_bangumi_rankings)
        self.bangumi_recommend_button.clicked.connect(self.recommend_bangumi)
        self.bangumi_page.back_button.clicked.connect(self._window_manager.show_main_page)

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
        self._on_loading_game_changed()
        self._update_loading_game_timer("00:00.0")
        self._update_todo_filter_buttons()

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
                color: rgb(14, 53, 94);
                font-size: 22px;
                font-weight: 900;
            }}
            #tarotSummaryBox {{
                background-color: rgba(255, 231, 209, 208);
                border: 1px solid rgba(236, 149, 92, 214);
                border-radius: 12px;
            }}
            #tarotLoadingOverlay {{
                background-color: rgba(14, 24, 38, 116);
                border-radius: 16px;
            }}
            #tarotLoadingPanel {{
                background-color: rgba(241, 247, 252, 245);
                border: 1px solid rgba(255, 255, 255, 170);
                border-radius: 20px;
            }}
            #bangumiRecommendationLabel {{
                background-color: rgba(255, 246, 220, 210);
                border: 1px solid rgba(228, 176, 94, 190);
                border-radius: 14px;
                color: rgb(92, 61, 20);
                padding: 12px 14px;
                font-size: 13px;
                font-weight: 600;
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
            #todoFilterButton {{
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 14px;
                background-color: rgba(255, 255, 255, 76);
                color: rgb(31, 39, 51);
            }}
            #todoFilterButton:checked {{
                background-color: rgba(61, 96, 146, 214);
                border: 1px solid rgba(255, 255, 255, 90);
                color: rgb(245, 248, 252);
            }}
            #todoFilterButton:hover {{
                background-color: rgba(171, 211, 247, 146);
            }}
            #todoFilterButton:checked:hover {{
                background-color: rgba(69, 108, 163, 224);
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

    def export_data_to_file(self) -> None:
        default_path = self.storage.db_path.parent / "todo-backup.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            stats = self.storage.export_data(file_path)
        except Exception as error:
            QMessageBox.warning(self, "Export Data", f"Export failed.\n\n{error}")
            return

        QMessageBox.information(
            self,
            "Export Data",
            (
                "Export completed.\n\n"
                f"Todos: {stats['todos']}\n"
                f"Tarot readings: {stats['tarot_readings']}"
            ),
        )

    def import_data_from_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            str(self.storage.db_path.parent),
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            preview = self.storage.preview_import_data(file_path)
        except Exception as error:
            QMessageBox.warning(self, "Import Data", f"Preview failed.\n\n{error}")
            return

        version = preview.get("version", "-")
        exported_at = str(preview.get("exported_at", "") or "-")
        todos = int(preview.get("todos", 0))
        tarot_readings = int(preview.get("tarot_readings", 0))
        reply = QMessageBox.question(
            self,
            "Import Data",
            (
                "Import Preview\n\n"
                f"File: {file_path}\n"
                f"Version: {version}\n"
                f"Exported At: {exported_at}\n"
                f"Todos: {todos}\n"
                f"Tarot readings: {tarot_readings}\n\n"
                "Importing will replace current local data. Continue?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            stats = self.storage.import_data(file_path)
        except Exception as error:
            QMessageBox.warning(self, "Import Data", f"Import failed.\n\n{error}")
            return

        self._refresh_list()
        self._refresh_tarot_history()
        QMessageBox.information(
            self,
            "Import Data",
            (
                "Import completed.\n\n"
                f"Todos: {stats['todos']}\n"
                f"Tarot readings: {stats['tarot_readings']}"
            ),
        )
