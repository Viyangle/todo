from dataclasses import dataclass


@dataclass
class TodoItem:
    id: int
    title: str
    done: bool
    sort_order: int
    due_at: str | None = None


@dataclass
class TarotReading:
    id: int
    question: str | None
    spread_type: str
    cards_json: str
    summary: str
    created_at: str
