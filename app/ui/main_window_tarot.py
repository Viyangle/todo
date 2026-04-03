from __future__ import annotations

import os

from PySide6.QtCore import QObject, QPoint, QThread, Signal, Qt
from PySide6.QtWidgets import QListWidgetItem, QMenu, QMessageBox

from app.core.tarot_interpreter import TarotAIConfig
from app.ui.controllers import TarotController

TAROT_NAME_EN = {
    "The Fool": "The Fool",
    "The Magician": "The Magician",
    "The High Priestess": "The High Priestess",
    "The Empress": "The Empress",
    "The Emperor": "The Emperor",
    "The Lovers": "The Lovers",
    "The Chariot": "The Chariot",
    "Strength": "Strength",
    "The Hermit": "The Hermit",
    "Wheel of Fortune": "Wheel of Fortune",
    "Justice": "Justice",
    "The Hanged Man": "The Hanged Man",
    "Death": "Death",
    "Temperance": "Temperance",
    "The Devil": "The Devil",
    "The Tower": "The Tower",
    "The Star": "The Star",
    "The Moon": "The Moon",
    "The Sun": "The Sun",
    "Judgement": "Judgement",
    "The World": "The World",
}

TAROT_NAME_ZH = {
    "The Fool": "\u611a\u8005",
    "The Magician": "\u9b54\u672f\u5e08",
    "The High Priestess": "\u5973\u796d\u53f8",
    "The Empress": "\u5973\u7687",
    "The Emperor": "\u7687\u5e1d",
    "The Lovers": "\u604b\u4eba",
    "The Chariot": "\u6218\u8f66",
    "Strength": "\u529b\u91cf",
    "The Hermit": "\u9690\u8005",
    "Wheel of Fortune": "\u547d\u8fd0\u4e4b\u8f6e",
    "Justice": "\u6b63\u4e49",
    "The Hanged Man": "\u5012\u540a\u4eba",
    "Death": "\u6b7b\u795e",
    "Temperance": "\u8282\u5236",
    "The Devil": "\u6076\u9b54",
    "The Tower": "\u9ad8\u5854",
    "The Star": "\u661f\u661f",
    "The Moon": "\u6708\u4eae",
    "The Sun": "\u592a\u9633",
    "Judgement": "\u5ba1\u5224",
    "The World": "\u4e16\u754c",
}


def _safe_tarot_name_map() -> dict[str, str]:
    try:
        if set(TAROT_NAME_ZH.keys()) != set(TAROT_NAME_EN.keys()):
            return dict(TAROT_NAME_EN)
        for key, value in TAROT_NAME_ZH.items():
            if not key or not value:
                return dict(TAROT_NAME_EN)
            if "\ufffd" in key or "\ufffd" in value:
                return dict(TAROT_NAME_EN)
        return dict(TAROT_NAME_ZH)
    except Exception:
        return dict(TAROT_NAME_EN)


class TarotDrawWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, controller: TarotController, question: str, spread_type: str) -> None:
        super().__init__()
        self._controller = controller
        self._question = question
        self._spread_type = spread_type

    def run(self) -> None:
        try:
            reading = self._controller.draw_spread(self._question, self._spread_type)
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(reading)


class TarotWindowMixin:
    LOADING_GAME_DIFFICULTIES = {
        "memory": [("Easy", "easy"), ("Normal", "normal"), ("Hard", "hard"), ("Hell", "hell")],
        "runner": [("Easy", "easy"), ("Hard", "hard")],
    }

    def draw_tarot_spread(self) -> None:
        if not self._tarot_controller.has_cards():
            QMessageBox.warning(self, "Tarot", "Tarot deck is unavailable.")
            return
        if self._tarot_loading:
            return

        question = self.tarot_question_edit.text().strip()
        spread_type = str(self.tarot_spread_combo.currentData() or "past_present_future")
        self._start_tarot_loading(question, spread_type)

    def _start_tarot_loading(self, question: str, spread_type: str) -> None:
        self._tarot_loading = True
        self._tarot_result_ready = False
        self.tarot_page.draw_button.setEnabled(False)
        self.tarot_question_edit.setEnabled(False)
        self.tarot_spread_combo.setEnabled(False)
        self.tarot_loading_status_label.setText("Reading your spread. Pick a quick round.")
        self.tarot_summary_body.setText("Interpreting...")
        self.tarot_loading_result_label.setText(self._default_loading_hint())
        self._show_tarot_loading_overlay()

        self._tarot_thread = QThread(self)
        self._tarot_worker = TarotDrawWorker(self._tarot_controller, question, spread_type)
        self._tarot_worker.moveToThread(self._tarot_thread)
        self._tarot_thread.started.connect(self._tarot_worker.run)
        self._tarot_worker.finished.connect(self._on_tarot_draw_finished)
        self._tarot_worker.failed.connect(self._on_tarot_draw_failed)
        self._tarot_worker.finished.connect(self._cleanup_tarot_worker)
        self._tarot_worker.failed.connect(self._cleanup_tarot_worker)
        self._tarot_thread.start()

    def _cleanup_tarot_worker(self, *_args) -> None:
        if self._tarot_thread is not None:
            self._tarot_thread.quit()
            self._tarot_thread.wait()
            self._tarot_thread.deleteLater()
            self._tarot_thread = None
        if self._tarot_worker is not None:
            self._tarot_worker.deleteLater()
            self._tarot_worker = None

    def _on_tarot_draw_finished(self, reading) -> None:
        self._tarot_loading = False
        self._tarot_result_ready = True
        self.tarot_page.draw_button.setEnabled(True)
        self.tarot_question_edit.setEnabled(True)
        self.tarot_spread_combo.setEnabled(True)
        self._show_tarot_reading(reading.question, reading.spread_type, reading.cards, reading.summary)
        self._refresh_tarot_history()
        self.tarot_loading_status_label.setText("The reading is ready. You can keep playing and open it when you want.")
        self.tarot_loading_result_label.setText("Reading finished. Click 'view reading' whenever you're done.")
        self.tarot_loading_close_button.setEnabled(True)

    def _on_tarot_draw_failed(self, error_message: str) -> None:
        self._tarot_loading = False
        self._tarot_result_ready = True
        self.tarot_page.draw_button.setEnabled(True)
        self.tarot_question_edit.setEnabled(True)
        self.tarot_spread_combo.setEnabled(True)
        self.tarot_summary_body.setText("Unable to finish the reading.")
        self.tarot_loading_status_label.setText("The reading failed. You can close this panel whenever you want.")
        self.tarot_loading_result_label.setText(error_message or "Tarot reading failed.")
        self.tarot_loading_close_button.setEnabled(True)

    def _load_ai_config(self) -> TarotAIConfig:
        return TarotAIConfig(
            api_key=self.settings.value("ai/api_key", os.getenv("OPENAI_API_KEY", ""), type=str).strip(),
            base_url=self.settings.value(
                "ai/base_url",
                os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                type=str,
            ).strip(),
            model_name=self.settings.value(
                "ai/model_name",
                os.getenv("OPENAI_MODEL_NAME", "qwen-max"),
                type=str,
            ).strip(),
        )

    def _build_ai_config_from_inputs(self) -> TarotAIConfig:
        return TarotAIConfig(
            api_key=self.ai_api_key_edit.text().strip(),
            base_url=self.ai_base_url_edit.text().strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name=self.ai_model_edit.text().strip() or "qwen-max",
        )

    def _apply_ai_config(self, config: TarotAIConfig) -> None:
        self._tarot_interpreter.set_config(config)

    def test_ai_connection(self) -> None:
        config = self._build_ai_config_from_inputs()
        try:
            reply = self._tarot_interpreter.test_connection(config)
        except Exception as error:
            QMessageBox.warning(self, "AI Test", f"Connection failed.\n\n{error}")
            return
        QMessageBox.information(self, "AI Test", f"Connection succeeded.\n\nModel reply: {reply}")

    def _prompt_for_ai_setup_if_needed(self) -> None:
        if self._tarot_interpreter.has_ai_config():
            return
        QMessageBox.information(
            self,
            "AI Setup",
            "AI is not configured yet. Go to Settings to fill in API Key, Base URL, and Model.",
        )
        self._window_manager.show_settings_page()

    def _show_tarot_loading_overlay(self) -> None:
        self.tarot_loading_overlay.show()
        self.tarot_loading_overlay.raise_()
        self.tarot_loading_close_button.setEnabled(False)
        self._refresh_loading_game_preview()

    def _hide_tarot_loading_overlay(self) -> None:
        self._stop_all_loading_games()
        self.tarot_loading_overlay.hide()
        self.tarot_loading_close_button.setEnabled(False)

    def _close_tarot_loading_overlay(self) -> None:
        if not self._tarot_result_ready:
            return
        self._hide_tarot_loading_overlay()

    def _current_loading_game_key(self) -> str:
        return str(self.tarot_loading_game_combo.currentData() or "memory")

    def _current_loading_game_widget(self):
        if self._current_loading_game_key() == "runner":
            return self.tarot_loading_runner_game_widget
        return self.tarot_loading_memory_game_widget

    def _current_loading_difficulty(self) -> str:
        return str(self.tarot_loading_difficulty_combo.currentData() or "easy")

    def _configure_loading_difficulties(self, game_key: str) -> None:
        current_difficulty = self._current_loading_difficulty()
        options = self.LOADING_GAME_DIFFICULTIES.get(game_key, self.LOADING_GAME_DIFFICULTIES["memory"])

        self.tarot_loading_difficulty_combo.blockSignals(True)
        self.tarot_loading_difficulty_combo.clear()
        selected_index = 0
        for index, (label, value) in enumerate(options):
            self.tarot_loading_difficulty_combo.addItem(label, value)
            if value == current_difficulty:
                selected_index = index
        self.tarot_loading_difficulty_combo.setCurrentIndex(selected_index)
        self.tarot_loading_difficulty_combo.blockSignals(False)

    def _loading_game_best_key(self, game_key: str, difficulty: str) -> str:
        return f"games/{game_key}_best_ms/{difficulty}"

    def _load_loading_game_best(self, game_key: str, difficulty: str) -> int | None:
        raw_value = self.settings.value(self._loading_game_best_key(game_key, difficulty))
        try:
            best_ms = int(raw_value)
        except (TypeError, ValueError):
            return None
        return best_ms if best_ms > 0 else None

    def _save_loading_game_best(self, game_key: str, difficulty: str, elapsed_ms: int) -> None:
        self.settings.setValue(self._loading_game_best_key(game_key, difficulty), elapsed_ms)

    def _is_lower_better(self, game_key: str) -> bool:
        return game_key == "memory"

    def _update_loading_game_best_label(self) -> None:
        game_key = self._current_loading_game_key()
        difficulty = self._current_loading_difficulty()
        best_ms = self._load_loading_game_best(game_key, difficulty)
        difficulty_text = self.tarot_loading_difficulty_combo.currentText()
        game_label = self.tarot_loading_game_combo.currentText()
        if best_ms is None:
            self.tarot_loading_best_label.setText(f"Best {game_label} ({difficulty_text}): --")
            return
        widget = self._current_loading_game_widget()
        self.tarot_loading_best_label.setText(
            f"Best {game_label} ({difficulty_text}): {widget.format_elapsed(best_ms)}"
        )

    def _update_loading_game_timer(self, value: str) -> None:
        if self._current_loading_game_key() == "runner":
            self.tarot_loading_timer_label.setText(f"Score: {value}")
            return
        self.tarot_loading_timer_label.setText(f"Timer: {value}")

    def _refresh_loading_game_preview(self) -> None:
        game_key = self._current_loading_game_key()
        difficulty = self._current_loading_difficulty()
        self._stop_all_loading_games()
        if game_key == "runner":
            self.tarot_loading_runner_game_widget.preview_difficulty(difficulty)
        else:
            self.tarot_loading_memory_game_widget.preview_difficulty(difficulty)
        self._update_loading_game_timer("0")
        self._update_loading_game_best_label()
        if not self._tarot_result_ready:
            self.tarot_loading_result_label.setText(self._default_loading_hint())

    def _on_loading_difficulty_changed(self, _index: int) -> None:
        self._refresh_loading_game_preview()

    def _default_loading_hint(self) -> str:
        if self._current_loading_game_key() == "runner":
            return "Score points over time, dodge meteors, catch hearts, and grab the rare diamond for 500."
        if self._current_loading_difficulty() == "hell":
            return "Hell mode deals 40 cards, so expect a long board and a fast memory workout."
        return "Match all pairs before the reading is ready."

    def _start_loading_game(self) -> None:
        difficulty = self._current_loading_difficulty()
        self._stop_all_loading_games()
        self._update_loading_game_timer("0")
        widget = self._current_loading_game_widget()
        widget.start_new_game(difficulty)
        if self._current_loading_game_key() == "runner":
            self.tarot_loading_result_label.setText("Build score over time. Hearts heal, diamonds are worth 500.")
        elif difficulty == "hell":
            self.tarot_loading_result_label.setText("Hell mode started: 40 cards, 20 pairs.")
        else:
            self.tarot_loading_result_label.setText("Find all pairs before the reading completes.")

    def _finish_loading_game(self, game_key: str, elapsed_ms: int) -> None:
        widget = (
            self.tarot_loading_runner_game_widget
            if game_key == "runner"
            else self.tarot_loading_memory_game_widget
        )
        difficulty = widget.current_difficulty()
        best_ms = self._load_loading_game_best(game_key, difficulty)
        if self._is_lower_better(game_key):
            is_best = best_ms is None or elapsed_ms < best_ms
        else:
            is_best = best_ms is None or elapsed_ms > best_ms
        if is_best:
            self._save_loading_game_best(game_key, difficulty, elapsed_ms)
        if difficulty == self._current_loading_difficulty() and game_key == self._current_loading_game_key():
            self._update_loading_game_best_label()
        suffix = " New best!" if is_best else ""
        if game_key == "runner":
            self.tarot_loading_result_label.setText(f"Final score: {widget.format_elapsed(elapsed_ms)}.{suffix}")
            return
        self.tarot_loading_result_label.setText(f"Finished in {widget.format_elapsed(elapsed_ms)}.{suffix}")

    def _stop_all_loading_games(self) -> None:
        self.tarot_loading_memory_game_widget.stop()
        self.tarot_loading_runner_game_widget.stop()

    def _on_loading_game_changed(self) -> None:
        game_key = self._current_loading_game_key()
        self._configure_loading_difficulties(game_key)
        if game_key == "runner":
            self.tarot_loading_game_stack.setCurrentWidget(self.tarot_loading_runner_game_widget)
        else:
            self.tarot_loading_game_stack.setCurrentWidget(self.tarot_loading_memory_game_widget)
        self._refresh_loading_game_preview()

    def _configure_tarot_spreads(self) -> None:
        self.tarot_spread_combo.blockSignals(True)
        self.tarot_spread_combo.clear()
        for label, spread_key in self._tarot_controller.spread_choices():
            self.tarot_spread_combo.addItem(label, spread_key)
        default_index = max(0, self.tarot_spread_combo.findData("past_present_future"))
        self.tarot_spread_combo.setCurrentIndex(default_index)
        self.tarot_spread_combo.blockSignals(False)
        self._on_tarot_spread_changed()

    def _on_tarot_spread_changed(self, _index: int | None = None) -> None:
        spread_type = str(self.tarot_spread_combo.currentData() or "past_present_future")
        self._apply_spread_preview(spread_type)

    def _group_cards_for_display(self, cards: list[dict[str, str]]) -> list[list[dict[str, str]]]:
        if len(cards) <= 3:
            groups = [[card] for card in cards]
            while len(groups) < 3:
                groups.append([])
            return groups
        return [cards[:4], cards[4:7], cards[7:]]

    def _format_tarot_group_body(self, group: list[dict[str, str]]) -> str:
        if not group:
            return "No card."
        lines = []
        for card in group:
            lines.append(
                f"{card.get('position', '-')}: {card.get('name', '-')}"
                f"\n{card.get('orientation', '-')}"
                f"\nKeywords: {card.get('keywords', '-')}"
            )
        return "\n\n".join(lines)

    def _format_group_names(self, group: list[dict[str, str]]) -> str:
        if not group:
            return "-"
        names = [str(card.get("name", "-")) for card in group]
        if len(names) == 1:
            return names[0]
        if len(names) <= 3:
            return " | ".join(names)
        return " | ".join(names[:3]) + f" +{len(names) - 3}"

    def _apply_spread_preview(self, spread_type: str) -> None:
        spread_label = self._tarot_controller.spread_label(spread_type)
        self.tarot_spread_label.setText(f"Spread: {spread_label}")
        self.tarot_summary_body.setText("Draw a spread to see the interpretation.")

        if spread_type == "single_card":
            self.tarot_past_box.show()
            self.tarot_present_box.hide()
            self.tarot_future_box.hide()
            self.tarot_past_title.setText("Card")
            self.tarot_past_name.setText("-")
            self.tarot_past_body.setText("No card yet.")
            return

        self.tarot_past_box.show()
        self.tarot_present_box.show()
        self.tarot_future_box.show()
        if spread_type == "celtic_cross":
            self.tarot_past_title.setText("Cards 1-4")
            self.tarot_present_title.setText("Cards 5-7")
            self.tarot_future_title.setText("Cards 8-10")
        else:
            self.tarot_past_title.setText("Past")
            self.tarot_present_title.setText("Present")
            self.tarot_future_title.setText("Future")

        self.tarot_past_name.setText("-")
        self.tarot_present_name.setText("-")
        self.tarot_future_name.setText("-")
        self.tarot_past_body.setText("No card yet.")
        self.tarot_present_body.setText("No card yet.")
        self.tarot_future_body.setText("No card yet.")

    def _show_tarot_reading(
        self,
        question: str,
        spread_type: str,
        cards: list[dict[str, str]],
        summary: str,
    ) -> None:
        spread_index = self.tarot_spread_combo.findData(spread_type)
        if spread_index >= 0 and self.tarot_spread_combo.currentIndex() != spread_index:
            self.tarot_spread_combo.blockSignals(True)
            self.tarot_spread_combo.setCurrentIndex(spread_index)
            self.tarot_spread_combo.blockSignals(False)

        self._apply_spread_preview(spread_type)
        spread_label = self._tarot_controller.spread_label(spread_type)
        question_text = question.strip() if question else "No question"
        self.tarot_spread_label.setText(f"Spread: {spread_label} | Question: {question_text}")

        groups = self._group_cards_for_display(cards)
        name_labels = (self.tarot_past_name, self.tarot_present_name, self.tarot_future_name)
        title_labels = (self.tarot_past_title, self.tarot_present_title, self.tarot_future_title)
        body_labels = (self.tarot_past_body, self.tarot_present_body, self.tarot_future_body)

        if len(cards) <= 3:
            titles = [str(card.get("position", f"Card {index + 1}")) for index, card in enumerate(cards)]
            while len(titles) < 3:
                titles.append(f"Card {len(titles) + 1}")
        else:
            titles = ["Card Group A", "Card Group B", "Card Group C"]

        for index in range(3):
            group = groups[index]
            title_labels[index].setText(titles[index])
            name_labels[index].setText(self._format_group_names(group))
            body_labels[index].setText(self._format_tarot_group_body(group))
        self.tarot_summary_body.setText(summary)

    def _refresh_tarot_history(self, *_args) -> None:
        if not hasattr(self, "tarot_history_list"):
            return

        favorites_only = self.tarot_history_favorites_only_checkbox.isChecked()
        self.tarot_history_list.clear()
        for reading in self._tarot_controller.list_history(limit=50, favorites_only=favorites_only):
            question = reading.question if reading.question else "No question"
            star = "[*]" if reading.is_favorite else "[ ]"
            spread_label = self._tarot_controller.spread_label(reading.spread_type)
            preview = f"{star} {reading.created_at} | {spread_label} | {question}"
            item = QListWidgetItem(preview)
            item.setData(Qt.UserRole, reading.id)
            item.setData(Qt.UserRole + 1, reading.is_favorite)
            self.tarot_history_list.addItem(item)

    def show_tarot_history_item(self, item: QListWidgetItem) -> None:
        reading_id = item.data(Qt.UserRole)
        if reading_id is None:
            return

        reading = self._tarot_controller.get_history_item(int(reading_id), limit=200)
        if reading is None:
            return

        self._show_tarot_reading(reading.question, reading.spread_type, reading.cards, reading.summary)
        self._window_manager.set_current_page(self.tarot_page)

    def _show_tarot_history_context_menu(self, position: QPoint) -> None:
        item = self.tarot_history_list.itemAt(position)
        if item is None:
            return

        self.tarot_history_list.setCurrentItem(item)
        reading_id = item.data(Qt.UserRole)
        if reading_id is None:
            return

        is_favorite = bool(item.data(Qt.UserRole + 1))
        menu = QMenu(self)
        toggle_text = "Unfavorite" if is_favorite else "Favorite"
        toggle_action = menu.addAction(toggle_text)
        open_action = menu.addAction("Open")

        selected_action = menu.exec(self.tarot_history_list.viewport().mapToGlobal(position))
        if selected_action is toggle_action:
            self._tarot_controller.set_history_favorite(int(reading_id), not is_favorite)
            self._refresh_tarot_history()
            return
        if selected_action is open_action:
            self.show_tarot_history_item(item)
