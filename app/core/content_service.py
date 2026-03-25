from __future__ import annotations

import html
import json
import random
from pathlib import Path


class ContentService:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent

    def load_tarot_cards(self) -> list[dict[str, object]]:
        cards_path = self.base_dir / "data" / "tarot_cards.json"
        try:
            raw_text = cards_path.read_text(encoding="utf-8")
            cards = json.loads(raw_text)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return []

        if not isinstance(cards, list):
            return []

        valid_cards: list[dict[str, object]] = []
        for entry in cards:
            if not isinstance(entry, dict):
                continue
            if not entry.get("name"):
                continue
            if not entry.get("upright_meaning"):
                continue
            if not entry.get("reversed_meaning"):
                continue
            valid_cards.append(entry)
        return valid_cards

    def load_philosopher_quotes(self) -> list[dict[str, str]]:
        quotes_path = self.base_dir / "data" / "philosopher_quotes.json"
        try:
            raw_text = quotes_path.read_text(encoding="utf-8")
            quotes = json.loads(raw_text)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return []

        if not isinstance(quotes, list):
            return []

        valid_quotes: list[dict[str, str]] = []
        for entry in quotes:
            if not isinstance(entry, dict):
                continue

            author = str(entry.get("author", "")).strip()
            quote = str(entry.get("quote", "")).strip()
            source = str(entry.get("source", "")).strip()
            if not author or not quote:
                continue

            valid_quotes.append(
                {
                    "author": author,
                    "quote": quote,
                    "source": source,
                }
            )
        return valid_quotes

    def pick_quote_html(self, quotes: list[dict[str, str]], current_html: str = "") -> str:
        available_quotes = [
            quote for quote in quotes
            if self.format_quote_html(quote) != current_html
        ]
        if not available_quotes:
            available_quotes = quotes[:]

        selected = random.choice(available_quotes) if available_quotes else None
        return self.format_quote_html(selected)

    def format_quote_html(self, quote_entry: dict[str, str] | None) -> str:
        if not quote_entry:
            return "<div>No quotes available.</div>"

        author = quote_entry.get("author", "").strip()
        quote = quote_entry.get("quote", "").strip()
        quote_html = html.escape(quote)
        author_html = html.escape(author)

        return (
            "<div style='font-size:13px; line-height:1.5;'>"
            f"{quote_html}"
            "</div>"
            "<div style='font-size:13px; line-height:1.4; text-align:right; margin-top:6px;'>"
            f"——{author_html}"
            "</div>"
        )
