from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class BangumiAnimeEntry:
    subject_id: int
    title: str
    subtitle: str
    url: str
    rank: int | None
    score: float | None
    votes: int
    info: str

    def to_dict(self) -> dict[str, object]:
        return {
            "subject_id": self.subject_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "url": self.url,
            "rank": self.rank,
            "score": self.score,
            "votes": self.votes,
            "info": self.info,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> BangumiAnimeEntry:
        return cls(
            subject_id=int(data.get("subject_id", 0)),
            title=str(data.get("title", "")),
            subtitle=str(data.get("subtitle", "")),
            url=str(data.get("url", "")),
            rank=int(data["rank"]) if data.get("rank") is not None else None,
            score=float(data["score"]) if data.get("score") is not None else None,
            votes=int(data.get("votes", 0)),
            info=str(data.get("info", "")),
        )


class BangumiService:
    _base_url = "https://bgm.tv"
    _user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    _item_pattern = re.compile(r"<li id=\"item_\d+\"[\s\S]*?</li>")
    _tag_pattern = re.compile(r"<[^>]+>")
    _max_fetch_pages = 3

    def __init__(self, cache_dir: str | Path | None = None, cache_ttl_hours: int = 24) -> None:
        self._page_cache: dict[tuple[int, str, int], str] = {}
        self._result_cache: dict[tuple[int, str, int], list[BangumiAnimeEntry]] = {}
        self._cache_ttl_seconds = max(1, cache_ttl_hours) * 3600
        cache_root = Path(cache_dir) if cache_dir else Path("data") / "bangumi_cache"
        self._cache_dir = cache_root
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_year_rankings(
        self,
        year: int,
        ranking_type: str,
        limit: int = 20,
        min_votes: int = 0,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[BangumiAnimeEntry]:
        ranking_key = ranking_type if ranking_type in {"comprehensive", "score", "hot"} else "comprehensive"
        top_limit = max(1, min(limit, 200))
        vote_threshold = max(0, min_votes)

        cache_key = (year, ranking_key, vote_threshold)
        in_memory_cached = self._result_cache.get(cache_key)
        if in_memory_cached is not None:
            if progress_callback:
                progress_callback("Loaded from memory cache.")
            return in_memory_cached[:top_limit]

        local_cached = self._read_local_cache(year, ranking_key, vote_threshold)
        if local_cached is not None:
            self._result_cache[cache_key] = local_cached
            if progress_callback:
                progress_callback("Loaded from local cache.")
            return local_cached[:top_limit]

        if ranking_key == "hot":
            all_entries = self._get_direct_ranking(
                year=year,
                sort_key="trends",
                min_votes=vote_threshold,
                progress_callback=progress_callback,
            )
        else:
            all_entries = self._get_direct_ranking(
                year=year,
                sort_key="rank",
                min_votes=vote_threshold,
                progress_callback=progress_callback,
            )

        self._result_cache[cache_key] = all_entries
        self._write_local_cache(year, ranking_key, vote_threshold, all_entries)
        return all_entries[:top_limit]

    def _get_direct_ranking(
        self,
        year: int,
        sort_key: str,
        min_votes: int,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[BangumiAnimeEntry]:
        first_html = self._fetch_page(year, sort_key, 1)
        max_page = self._extract_max_page(first_html)
        end_page = min(max_page, self._max_fetch_pages)
        entries: list[BangumiAnimeEntry] = []

        for page in range(1, end_page + 1):
            if progress_callback:
                progress_callback(f"Fetching page {page}/{end_page}...")
            html = first_html if page == 1 else self._fetch_page(year, sort_key, page)
            page_entries = self._parse_entries(html)
            if not page_entries:
                break
            entries.extend([entry for entry in page_entries if entry.votes >= min_votes])

        return entries

    def _get_score_ranking(
        self,
        year: int,
        min_votes: int,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[BangumiAnimeEntry]:
        first_page = self._fetch_page(year, "collects", 1)
        max_page = self._extract_max_page(first_page)
        all_entries = self._parse_entries(first_page)

        for page in range(2, max_page + 1):
            if progress_callback:
                progress_callback(f"Score ranking fetch: page {page}/{max_page}...")
            html = self._fetch_page(year, "collects", page)
            all_entries.extend(self._parse_entries(html))

        unique_entries = self._deduplicate_entries(all_entries)
        filtered_entries = [
            entry
            for entry in unique_entries
            if entry.score is not None and entry.votes >= min_votes
        ]
        filtered_entries.sort(
            key=lambda entry: (
                entry.score or 0.0,
                entry.votes,
                -(entry.rank or 999999),
            ),
            reverse=True,
        )
        return filtered_entries

    def _fetch_page(self, year: int, sort_key: str, page: int) -> str:
        cache_key = (year, sort_key, page)
        cached = self._page_cache.get(cache_key)
        if cached is not None:
            return cached

        query = {"sort": sort_key}
        if page > 1:
            query["page"] = str(page)
        url = f"{self._base_url}/anime/browser/airtime/{year}?{urlencode(query)}"
        request = Request(url, headers={"User-Agent": self._user_agent})
        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
        self._page_cache[cache_key] = html
        return html

    def _extract_max_page(self, html: str) -> int:
        page_numbers = [int(value) for value in re.findall(r"[?&]page=(\d+)", html)]
        return max(page_numbers) if page_numbers else 1

    def _parse_entries(self, html: str) -> list[BangumiAnimeEntry]:
        entries: list[BangumiAnimeEntry] = []
        for block in self._item_pattern.findall(html):
            url_match = re.search(r"<a href=\"(/subject/\d+)\" class=\"l\">", block)
            title_match = re.search(r"<a href=\"/subject/\d+\" class=\"l\">([\s\S]*?)</a>", block)
            if not url_match or not title_match:
                continue

            path = url_match.group(1)
            subject_id = int(path.rsplit("/", 1)[-1])
            subtitle_match = re.search(r"<small class=\"grey\">([\s\S]*?)</small>", block)
            rank_match = re.search(r"<span class=\"rank\"><small>Rank </small>(\d+)</span>", block)
            score_match = re.search(r"<small class=\"fade\">([\d.]+)</small>", block)
            votes_match = re.search(r"<span class=\"tip_j\">\(([\d,]+)[^)]*\)</span>", block)
            info_match = re.search(r"<p class=\"info tip\">\s*([\s\S]*?)\s*</p>", block)

            entries.append(
                BangumiAnimeEntry(
                    subject_id=subject_id,
                    title=self._clean_text(title_match.group(1)),
                    subtitle=self._clean_text(subtitle_match.group(1)) if subtitle_match else "",
                    url=f"{self._base_url}{path}",
                    rank=int(rank_match.group(1)) if rank_match else None,
                    score=float(score_match.group(1)) if score_match else None,
                    votes=int(votes_match.group(1).replace(",", "")) if votes_match else 0,
                    info=self._clean_text(info_match.group(1)) if info_match else "",
                )
            )
        return entries

    def _deduplicate_entries(self, entries: list[BangumiAnimeEntry]) -> list[BangumiAnimeEntry]:
        deduped: dict[int, BangumiAnimeEntry] = {}
        for entry in entries:
            best = deduped.get(entry.subject_id)
            if best is None or (entry.votes, entry.score or 0.0) > (best.votes, best.score or 0.0):
                deduped[entry.subject_id] = entry
        return list(deduped.values())

    def _clean_text(self, raw_html: str) -> str:
        text = self._tag_pattern.sub("", raw_html)
        text = unescape(text)
        return " ".join(text.split())

    def _cache_path(self, year: int, ranking_type: str, min_votes: int) -> Path:
        file_name = f"{year}_{ranking_type}_min{min_votes}.json"
        return self._cache_dir / file_name

    def _read_local_cache(
        self,
        year: int,
        ranking_type: str,
        min_votes: int,
    ) -> list[BangumiAnimeEntry] | None:
        cache_path = self._cache_path(year, ranking_type, min_votes)
        if not cache_path.exists():
            return None

        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        created_at = float(payload.get("created_at", 0))
        if created_at <= 0:
            return None
        if time.time() - created_at > self._cache_ttl_seconds:
            return None

        entries_raw = payload.get("entries")
        if not isinstance(entries_raw, list):
            return None

        return [
            BangumiAnimeEntry.from_dict(item)
            for item in entries_raw
            if isinstance(item, dict)
        ]

    def _write_local_cache(
        self,
        year: int,
        ranking_type: str,
        min_votes: int,
        entries: list[BangumiAnimeEntry],
    ) -> None:
        payload = {
            "created_at": time.time(),
            "year": year,
            "ranking_type": ranking_type,
            "min_votes": min_votes,
            "entries": [entry.to_dict() for entry in entries],
        }
        cache_path = self._cache_path(year, ranking_type, min_votes)
        try:
            cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except OSError:
            return
