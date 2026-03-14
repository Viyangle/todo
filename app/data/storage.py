import sqlite3
from pathlib import Path
from typing import List

from app.core.models import TodoItem


class TodoStorage:
    def __init__(self, db_path: str = "data/todo.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def list_todos(self) -> List[TodoItem]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, done FROM todos ORDER BY done ASC, id ASC"
            ).fetchall()

        return [
            TodoItem(
                id=row["id"],
                title=row["title"],
                done=bool(row["done"]),
            )
            for row in rows
        ]

    def add_todo(self, title: str) -> TodoItem:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Todo title cannot be empty")

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO todos (title, done) VALUES (?, 0)",
                (clean_title,),
            )
            conn.commit()
            todo_id = cursor.lastrowid

        return TodoItem(id=int(todo_id), title=clean_title, done=False)

    def toggle_done(self, todo_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE todos
                SET done = CASE done WHEN 1 THEN 0 ELSE 1 END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (todo_id,),
            )
            conn.commit()

    def delete_completed(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE done = 1")
            conn.commit()

