from dataclasses import dataclass


@dataclass
class TodoItem:
    id: int
    title: str
    done: bool
