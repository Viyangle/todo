from __future__ import annotations

import json
import random
from dataclasses import dataclass

from PySide6.QtCore import QDate, QDateTime, QTime, Qt

from app.core.tarot_interpreter import TarotInterpreter
from app.data.storage import TodoStorage
from app.core.models import TarotReading, TodoItem


@dataclass
class DrawnTarotReading:
    reading_id: int
    question: str
    spread_type: str
    cards: list[dict[str, str]]
    summary: str
    is_favorite: bool = False


class TodoController:
    def __init__(self, storage: TodoStorage) -> None:
        self.storage = storage

    def add_todo(
        self,
        title: str,
        due_enabled: bool,
        due_date: QDate,
        due_time: QTime,
    ) -> None:
        due_at = None
        if due_enabled:
            due_at = QDateTime(due_date, due_time).toString(Qt.ISODate)
        self.storage.add_todo(title, due_at=due_at)

    def list_todos(self) -> list[TodoItem]:
        return self.storage.list_todos()

    def toggle_done(self, todo_id: int) -> None:
        self.storage.toggle_done(todo_id)

    def update_todo_title(self, todo_id: int, title: str) -> None:
        self.storage.update_todo_title(todo_id, title)

    def update_todo_due_at(
        self,
        todo_id: int,
        due_enabled: bool,
        due_date: QDate,
        due_time: QTime,
    ) -> None:
        due_at = None
        if due_enabled:
            due_at = QDateTime(due_date, due_time).toString(Qt.ISODate)
        self.storage.update_todo_due_at(todo_id, due_at)

    def delete_completed(self) -> None:
        self.storage.delete_completed()

    def delete_todo(self, todo_id: int) -> None:
        self.storage.delete_todo(todo_id)

    def update_order(self, todo_ids: list[int]) -> None:
        self.storage.update_order(todo_ids)

    def is_due_soon(self, due_at: str | None, done: bool, warn_minutes: int) -> bool:
        if done or not due_at:
            return False

        due_time = QDateTime.fromString(due_at, Qt.ISODate)
        if not due_time.isValid():
            return False

        now = QDateTime.currentDateTime()
        soon_limit = now.addSecs(warn_minutes * 60)
        return now <= due_time <= soon_limit


class TarotController:
    SPREAD_POSITIONS: dict[str, list[str]] = {
        "single_card": ["Card"],
        "past_present_future": ["Past", "Present", "Future"],
        "celtic_cross": [
            "Present",
            "Challenge",
            "Past",
            "Future",
            "Above",
            "Below",
            "Advice",
            "Environment",
            "Hopes/Fears",
            "Outcome",
        ],
    }

    def __init__(
        self,
        storage: TodoStorage,
        interpreter: TarotInterpreter,
        tarot_cards: list[dict[str, object]],
        tarot_name_map: dict[str, str],
    ) -> None:
        self.storage = storage
        self.interpreter = interpreter
        self.tarot_cards = tarot_cards
        self.tarot_name_map = tarot_name_map

    def has_cards(self) -> bool:
        return bool(self.tarot_cards)

    def spread_choices(self) -> list[tuple[str, str]]:
        return [
            ("Single Card", "single_card"),
            ("Past / Present / Future", "past_present_future"),
            ("Celtic Cross", "celtic_cross"),
        ]

    def spread_label(self, spread_type: str) -> str:
        labels = {value: label for label, value in self.spread_choices()}
        return labels.get(spread_type, "Past / Present / Future")

    def draw_spread(self, question: str, spread_type: str) -> DrawnTarotReading:
        positions = self.SPREAD_POSITIONS.get(spread_type, self.SPREAD_POSITIONS["past_present_future"])
        card_count = len(positions)
        if len(self.tarot_cards) >= card_count:
            selected_cards = random.sample(self.tarot_cards, card_count)
        else:
            selected_cards = [random.choice(self.tarot_cards) for _ in range(card_count)]

        spread_cards = [
            self._draw_one_tarot_card(card_data, position)
            for card_data, position in zip(selected_cards, positions)
        ]
        summary = self.interpreter.build_summary(question=question, cards=spread_cards)
        stored_reading = self.storage.add_tarot_reading(
            spread_type=spread_type,
            cards=spread_cards,
            summary=summary,
            question=question or None,
        )
        return DrawnTarotReading(
            reading_id=stored_reading.id,
            question=question,
            spread_type=spread_type,
            cards=spread_cards,
            summary=summary,
            is_favorite=stored_reading.is_favorite,
        )

    def list_history(self, limit: int = 50, favorites_only: bool = False) -> list[TarotReading]:
        return self.storage.list_tarot_readings(limit=limit, favorites_only=favorites_only)

    def get_history_item(self, reading_id: int, limit: int = 200) -> DrawnTarotReading | None:
        del limit
        selected = self.storage.get_tarot_reading(reading_id)
        if selected is None:
            return None

        cards = self._deserialize_cards(selected.cards_json)
        return DrawnTarotReading(
            reading_id=selected.id,
            question=selected.question or "",
            spread_type=selected.spread_type,
            cards=cards,
            summary=selected.summary,
            is_favorite=selected.is_favorite,
        )

    def set_history_favorite(self, reading_id: int, is_favorite: bool) -> None:
        self.storage.set_tarot_reading_favorite(reading_id, is_favorite)

    def _draw_one_tarot_card(self, card_data: dict[str, object], position: str) -> dict[str, str]:
        orientation = random.choice(("upright", "reversed"))
        raw_name = str(card_data.get("name", "Unknown Card"))
        name = self.tarot_name_map.get(raw_name, raw_name)
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

    def _deserialize_cards(self, cards_json: str) -> list[dict[str, str]]:
        try:
            cards_raw = json.loads(cards_json)
        except json.JSONDecodeError:
            return []

        cards: list[dict[str, str]] = []
        if isinstance(cards_raw, list):
            for entry in cards_raw:
                if not isinstance(entry, dict):
                    continue
                raw_name = str(entry.get("name", ""))
                cards.append(
                    {
                        "position": str(entry.get("position", "")),
                        "name": self.tarot_name_map.get(raw_name, raw_name),
                        "orientation": str(entry.get("orientation", "")),
                        "keywords": str(entry.get("keywords", "")),
                        "meaning": str(entry.get("meaning", "")),
                    }
                )
        return cards
