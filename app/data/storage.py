import sqlite3
from pathlib import Path
from typing import Iterable, List

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
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    due_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._ensure_schema(conn)
            conn.commit()

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(todos)").fetchall()
        }

        if "sort_order" not in columns:
            conn.execute("ALTER TABLE todos ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
            conn.execute("UPDATE todos SET sort_order = id WHERE sort_order = 0")

        if "due_at" not in columns:
            conn.execute("ALTER TABLE todos ADD COLUMN due_at TEXT")

    def list_todos(self) -> List[TodoItem]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, done, sort_order, due_at FROM todos ORDER BY sort_order ASC, id ASC"
            ).fetchall()

        return [
            TodoItem(
                id=row["id"],
                title=row["title"],
                done=bool(row["done"]),
                sort_order=row["sort_order"],
                due_at=row["due_at"],
            )
            for row in rows
        ]

    def add_todo(self, title: str, due_at: str | None = None) -> TodoItem:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Todo title cannot be empty")

        with self._connect() as conn:
            next_sort_order = conn.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_sort_order FROM todos"
            ).fetchone()["next_sort_order"]
            cursor = conn.execute(
                "INSERT INTO todos (title, done, sort_order, due_at) VALUES (?, 0, ?, ?)",
                (clean_title, next_sort_order, due_at),
            )
            conn.commit()
            todo_id = cursor.lastrowid

        return TodoItem(
            id=int(todo_id),
            title=clean_title,
            done=False,
            sort_order=int(next_sort_order),
            due_at=due_at,
        )

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

    def update_order(self, todo_ids: Iterable[int]) -> None:
        with self._connect() as conn:
            for index, todo_id in enumerate(todo_ids, start=1):
                conn.execute(
                    "UPDATE todos SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (index, todo_id),
                )
            conn.commit()

    def delete_completed(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE done = 1")
            conn.commit()
