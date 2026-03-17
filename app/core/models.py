from dataclasses import dataclass


@dataclass
class TodoItem:
    id: int
    title: str
    done: bool
    sort_order: int
    due_at: str | None = None
