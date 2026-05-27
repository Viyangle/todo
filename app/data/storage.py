import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterable, List

from app.core.models import TarotReading, TodoItem


class TodoStorage:
    _tarot_history_limit = 20
    _backup_version = 1

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else self._default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _default_db_path(self) -> Path:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parents[2]
        return base_dir / "data" / "todo.db"

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tarot_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    spread_type TEXT NOT NULL,
                    cards_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._ensure_schema(conn)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_sort_order ON todos(sort_order, id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tarot_readings_favorite_id "
                "ON tarot_readings(is_favorite, id DESC)"
            )
            conn.commit()

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        todo_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(todos)").fetchall()
        }

        if "sort_order" not in todo_columns:
            conn.execute("ALTER TABLE todos ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
            conn.execute("UPDATE todos SET sort_order = id WHERE sort_order = 0")

        if "due_at" not in todo_columns:
            conn.execute("ALTER TABLE todos ADD COLUMN due_at TEXT")

        tarot_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(tarot_readings)").fetchall()
        }
        if "is_favorite" not in tarot_columns:
            conn.execute("ALTER TABLE tarot_readings ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0")

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

    def update_todo_title(self, todo_id: int, title: str) -> None:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Todo title cannot be empty")

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE todos
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (clean_title, todo_id),
            )
            conn.commit()

    def update_todo_due_at(self, todo_id: int, due_at: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE todos
                SET due_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (due_at, todo_id),
            )
            conn.commit()

    def update_order(self, todo_ids: Iterable[int]) -> None:
        rows = [(index, int(todo_id)) for index, todo_id in enumerate(todo_ids, start=1)]
        if not rows:
            return

        with self._connect() as conn:
            conn.executemany(
                "UPDATE todos SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                rows,
            )
            conn.commit()

    def delete_completed(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE done = 1")
            conn.commit()

    def delete_todo(self, todo_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            conn.commit()

    def add_tarot_reading(
        self,
        spread_type: str,
        cards: list[dict[str, str]],
        summary: str,
        question: str | None = None,
    ) -> TarotReading:
        cards_json = json.dumps(cards, ensure_ascii=False)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tarot_readings (question, spread_type, cards_json, summary)
                VALUES (?, ?, ?, ?)
                """,
                (question, spread_type, cards_json, summary),
            )
            reading_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT id, question, spread_type, cards_json, summary, created_at, is_favorite
                FROM tarot_readings
                WHERE id = ?
                """,
                (reading_id,),
            ).fetchone()
            conn.execute(
                """
                DELETE FROM tarot_readings
                WHERE is_favorite = 0
                  AND id NOT IN (
                    SELECT id
                    FROM tarot_readings
                    WHERE is_favorite = 0
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (self._tarot_history_limit,),
            )
            conn.commit()

        return TarotReading(
            id=row["id"],
            question=row["question"],
            spread_type=row["spread_type"],
            cards_json=row["cards_json"],
            summary=row["summary"],
            created_at=row["created_at"],
            is_favorite=bool(row["is_favorite"]),
        )

    def set_tarot_reading_favorite(self, reading_id: int, is_favorite: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tarot_readings
                SET is_favorite = ?
                WHERE id = ?
                """,
                (1 if is_favorite else 0, reading_id),
            )
            conn.commit()

    def get_tarot_reading(self, reading_id: int) -> TarotReading | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, question, spread_type, cards_json, summary, created_at, is_favorite
                FROM tarot_readings
                WHERE id = ?
                """,
                (reading_id,),
            ).fetchone()

        if row is None:
            return None

        return TarotReading(
            id=row["id"],
            question=row["question"],
            spread_type=row["spread_type"],
            cards_json=row["cards_json"],
            summary=row["summary"],
            created_at=row["created_at"],
            is_favorite=bool(row["is_favorite"]),
        )

    def list_tarot_readings(self, limit: int = 50, favorites_only: bool = False) -> List[TarotReading]:
        with self._connect() as conn:
            if favorites_only:
                rows = conn.execute(
                    """
                    SELECT id, question, spread_type, cards_json, summary, created_at, is_favorite
                    FROM tarot_readings
                    WHERE is_favorite = 1
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (max(1, limit),),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, question, spread_type, cards_json, summary, created_at, is_favorite
                    FROM tarot_readings
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (max(1, limit),),
                ).fetchall()

        return [
            TarotReading(
                id=row["id"],
                question=row["question"],
                spread_type=row["spread_type"],
                cards_json=row["cards_json"],
                summary=row["summary"],
                created_at=row["created_at"],
                is_favorite=bool(row["is_favorite"]),
            )
            for row in rows
        ]

    def export_data(self, file_path: str | Path) -> dict[str, int]:
        target_path = Path(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            todo_rows = conn.execute(
                """
                SELECT id, title, done, sort_order, due_at, created_at, updated_at
                FROM todos
                ORDER BY sort_order ASC, id ASC
                """
            ).fetchall()
            tarot_rows = conn.execute(
                """
                SELECT id, question, spread_type, cards_json, summary, is_favorite, created_at
                FROM tarot_readings
                ORDER BY id ASC
                """
            ).fetchall()

        payload = {
            "version": self._backup_version,
            "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "todos": [
                {
                    "id": int(row["id"]),
                    "title": str(row["title"]),
                    "done": bool(row["done"]),
                    "sort_order": int(row["sort_order"]),
                    "due_at": row["due_at"],
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                }
                for row in todo_rows
            ],
            "tarot_readings": [
                {
                    "id": int(row["id"]),
                    "question": row["question"],
                    "spread_type": str(row["spread_type"]),
                    "cards_json": str(row["cards_json"]),
                    "summary": str(row["summary"]),
                    "is_favorite": bool(row["is_favorite"]),
                    "created_at": str(row["created_at"]),
                }
                for row in tarot_rows
            ],
        }
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"todos": len(payload["todos"]), "tarot_readings": len(payload["tarot_readings"])}

    def preview_import_data(self, file_path: str | Path) -> dict[str, object]:
        metadata, todos, tarot_readings = self._load_backup_rows(file_path)
        return {
            "version": metadata.get("version"),
            "exported_at": metadata.get("exported_at", ""),
            "todos": len(todos),
            "tarot_readings": len(tarot_readings),
        }

    def import_data(self, file_path: str | Path) -> dict[str, int]:
        _metadata, todos, tarot_readings = self._load_backup_rows(file_path)

        with self._connect() as conn:
            conn.execute("DELETE FROM todos")
            conn.execute("DELETE FROM tarot_readings")

            if todos:
                conn.executemany(
                    """
                    INSERT INTO todos (id, title, done, sort_order, due_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    todos,
                )

            if tarot_readings:
                conn.executemany(
                    """
                    INSERT INTO tarot_readings (
                        id, question, spread_type, cards_json, summary, is_favorite, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    tarot_readings,
                )

            self._reset_sequence(conn, "todos", max([row[0] for row in todos], default=0))
            self._reset_sequence(conn, "tarot_readings", max([row[0] for row in tarot_readings], default=0))
            conn.commit()

        return {"todos": len(todos), "tarot_readings": len(tarot_readings)}

    def _load_backup_rows(
        self,
        file_path: str | Path,
    ) -> tuple[dict[str, object], list[tuple[int, str, int, int, str | None, str, str]], list[tuple[int, str | None, str, str, str, int, str]]]:
        source_path = Path(file_path)
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid backup file: {error}") from error

        if not isinstance(payload, dict):
            raise ValueError("Invalid backup format.")

        todos_raw = payload.get("todos", [])
        tarot_raw = payload.get("tarot_readings", [])
        if not isinstance(todos_raw, list) or not isinstance(tarot_raw, list):
            raise ValueError("Invalid backup payload lists.")

        todos = [self._normalize_todo_backup_item(item) for item in todos_raw]
        tarot_readings = [self._normalize_tarot_backup_item(item) for item in tarot_raw]
        return payload, todos, tarot_readings

    def _normalize_todo_backup_item(self, item: object) -> tuple[int, str, int, int, str | None, str, str]:
        if not isinstance(item, dict):
            raise ValueError("Invalid todo item in backup.")

        todo_id = int(item.get("id", 0))
        title = str(item.get("title", "")).strip()
        if todo_id <= 0 or not title:
            raise ValueError("Todo item missing id/title.")

        due_at = item.get("due_at")
        due_at_value = str(due_at).strip() if isinstance(due_at, str) and due_at.strip() else None
        created_at = str(item.get("created_at", "")).strip() or time.strftime("%Y-%m-%d %H:%M:%S")
        updated_at = str(item.get("updated_at", "")).strip() or created_at

        return (
            todo_id,
            title,
            1 if bool(item.get("done", False)) else 0,
            max(1, int(item.get("sort_order", todo_id))),
            due_at_value,
            created_at,
            updated_at,
        )

    def _normalize_tarot_backup_item(self, item: object) -> tuple[int, str | None, str, str, str, int, str]:
        if not isinstance(item, dict):
            raise ValueError("Invalid tarot item in backup.")

        reading_id = int(item.get("id", 0))
        spread_type = str(item.get("spread_type", "")).strip()
        cards_json = str(item.get("cards_json", "")).strip()
        summary = str(item.get("summary", "")).strip()
        if reading_id <= 0 or not spread_type or not cards_json or not summary:
            raise ValueError("Tarot item missing required fields.")

        question_raw = item.get("question")
        question = str(question_raw).strip() if isinstance(question_raw, str) and question_raw.strip() else None
        created_at = str(item.get("created_at", "")).strip() or time.strftime("%Y-%m-%d %H:%M:%S")

        return (
            reading_id,
            question,
            spread_type,
            cards_json,
            summary,
            1 if bool(item.get("is_favorite", False)) else 0,
            created_at,
        )

    def _reset_sequence(self, conn: sqlite3.Connection, table_name: str, seq_value: int) -> None:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table_name,))
        if seq_value > 0:
            conn.execute(
                "INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                (table_name, seq_value),
            )
