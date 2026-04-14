from __future__ import annotations

import re
from html import escape
from typing import Literal

from PySide6.QtCore import QDate, QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QLabel, QListWidgetItem, QMessageBox

from app.core.bangumi_service import BangumiAnimeEntry
from app.ui.controllers import BangumiController


class BangumiFetchWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        controller: BangumiController,
        year: int,
        ranking_type: str,
        limit: int,
        min_votes: int,
        mode: Literal["list", "recommend"],
    ) -> None:
        super().__init__()
        self._controller = controller
        self._year = year
        self._ranking_type = ranking_type
        self._limit = limit
        self._min_votes = min_votes
        self._mode = mode

    def run(self) -> None:
        try:
            entries = self._controller.fetch_year_rankings(
                year=self._year,
                ranking_type=self._ranking_type,
                limit=self._limit,
                min_votes=self._min_votes,
                progress_callback=self.progress.emit,
            )
            recommendation = None
            if self._mode == "recommend":
                recommendation = self._controller.recommend_anime(
                    year=self._year,
                    ranking_type=self._ranking_type,
                    limit=self._limit,
                    min_votes=self._min_votes,
                )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit({"mode": self._mode, "entries": entries, "recommendation": recommendation})


class BangumiWindowMixin:
    _page_progress_pattern = re.compile(r"page\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)

    def _configure_bangumi_page(self) -> None:
        current_year = QDate.currentDate().year()
        self.bangumi_year_spin.setValue(current_year)
        self.bangumi_ranking_combo.setCurrentIndex(0)
        self.bangumi_limit_combo.setCurrentIndex(1)
        self.bangumi_min_heat_checkbox.setChecked(True)
        self.bangumi_progress_bar.hide()
        self.bangumi_progress_bar.setRange(0, 100)
        self.bangumi_progress_bar.setValue(0)
        self._on_bangumi_min_heat_toggled(True)
        self._bangumi_thread = None
        self._bangumi_worker = None
        self._bangumi_loading = False
        self._bangumi_last_params: dict[str, int | str] | None = None
        self._bangumi_last_entries: list[BangumiAnimeEntry] = []
        self._set_bangumi_recommendation_text("点击 recommend，从当前筛选条件里挑一部番剧。")

    def _on_bangumi_min_heat_toggled(self, checked: bool) -> None:
        self.bangumi_min_heat_checkbox.setToolTip(
            f"开启后使用设置里的最低热度（{self._bangumi_min_votes}）" if checked else "关闭后不限制最低热度"
        )

    def load_bangumi_rankings(self) -> None:
        self._start_bangumi_request("list")

    def recommend_bangumi(self) -> None:
        params = self._current_bangumi_params()
        if self._bangumi_last_params == params and self._bangumi_last_entries:
            recommendation = self._bangumi_controller.recommend_anime(
                year=int(params["year"]),
                ranking_type=str(params["ranking_type"]),
                limit=int(params["limit"]),
                min_votes=int(params["min_votes"]),
            )
            self._set_bangumi_recommendation(recommendation)
            return

        self._start_bangumi_request("recommend")

    def _current_bangumi_params(self) -> dict[str, int | str]:
        return {
            "year": int(self.bangumi_year_spin.value()),
            "ranking_type": str(self.bangumi_ranking_combo.currentData() or "comprehensive"),
            "limit": int(self.bangumi_limit_combo.currentData() or 20),
            "min_votes": self._bangumi_min_votes if self.bangumi_min_heat_checkbox.isChecked() else 0,
        }

    def _start_bangumi_request(self, mode: Literal["list", "recommend"]) -> None:
        if self._bangumi_loading:
            return

        params = self._current_bangumi_params()

        self._bangumi_loading = True
        self.bangumi_fetch_button.setEnabled(False)
        self.bangumi_recommend_button.setEnabled(False)
        self.bangumi_fetch_button.setText("loading..." if mode == "list" else "load")
        self.bangumi_recommend_button.setText("picking..." if mode == "recommend" else "recommend")
        self.bangumi_ranking_combo.setEnabled(False)
        self.bangumi_year_spin.setEnabled(False)
        self.bangumi_limit_combo.setEnabled(False)
        self.bangumi_min_heat_checkbox.setEnabled(False)
        self.bangumi_progress_bar.setRange(0, 0)
        self.bangumi_progress_bar.show()
        if mode == "list":
            self.bangumi_results_list.clear()
        self._set_bangumi_recommendation_text("正在加载榜单..." if mode == "list" else "正在挑选中...")

        self._bangumi_thread = QThread(self)
        self._bangumi_worker = BangumiFetchWorker(
            controller=self._bangumi_controller,
            year=int(params["year"]),
            ranking_type=str(params["ranking_type"]),
            limit=int(params["limit"]),
            min_votes=int(params["min_votes"]),
            mode=mode,
        )
        self._bangumi_worker.moveToThread(self._bangumi_thread)
        self._bangumi_thread.started.connect(self._bangumi_worker.run)
        self._bangumi_worker.progress.connect(self._on_bangumi_progress)
        self._bangumi_worker.finished.connect(self._on_bangumi_finished)
        self._bangumi_worker.failed.connect(self._on_bangumi_failed)
        self._bangumi_worker.finished.connect(self._cleanup_bangumi_worker)
        self._bangumi_worker.failed.connect(self._cleanup_bangumi_worker)
        self._bangumi_thread.start()

    def _cleanup_bangumi_worker(self, *_args) -> None:
        self._bangumi_loading = False
        self.bangumi_fetch_button.setEnabled(True)
        self.bangumi_recommend_button.setEnabled(True)
        self.bangumi_fetch_button.setText("load")
        self.bangumi_recommend_button.setText("recommend")
        self.bangumi_ranking_combo.setEnabled(True)
        self.bangumi_year_spin.setEnabled(True)
        self.bangumi_limit_combo.setEnabled(True)
        self.bangumi_min_heat_checkbox.setEnabled(True)
        self.bangumi_progress_bar.hide()
        self.bangumi_progress_bar.setRange(0, 100)
        self.bangumi_progress_bar.setValue(0)

        if self._bangumi_thread is not None:
            self._bangumi_thread.quit()
            self._bangumi_thread.wait()
            self._bangumi_thread.deleteLater()
            self._bangumi_thread = None
        if self._bangumi_worker is not None:
            self._bangumi_worker.deleteLater()
            self._bangumi_worker = None

    def _on_bangumi_progress(self, message: str) -> None:
        text = message.strip()
        if not text:
            return

        page_match = self._page_progress_pattern.search(text)
        if page_match:
            current = int(page_match.group(1))
            total = max(1, int(page_match.group(2)))
            self.bangumi_progress_bar.setRange(0, total)
            self.bangumi_progress_bar.setValue(min(current, total))
            return

        if "cache" in text.lower():
            self.bangumi_progress_bar.setRange(0, 1)
            self.bangumi_progress_bar.setValue(1)

    def _on_bangumi_finished(self, payload) -> None:
        mode = payload.get("mode") if isinstance(payload, dict) else "list"
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
        recommendation = payload.get("recommendation") if isinstance(payload, dict) else None
        self.bangumi_results_list.clear()
        self.bangumi_progress_bar.setRange(0, 1)
        self.bangumi_progress_bar.setValue(1)
        self._bangumi_last_params = self._current_bangumi_params()
        self._bangumi_last_entries = list(entries)
        if mode == "recommend":
            self._set_bangumi_recommendation(recommendation)
        else:
            self._set_bangumi_recommendation_text("点击 recommend，从当前筛选条件里挑一部番剧。")
        if not entries:
            return

        for index, entry in enumerate(entries, start=1):
            score_text = f"{entry.score:.1f}" if entry.score is not None else "-"
            row_html = (
                f"{index:>2}. "
                f"<a href=\"{escape(entry.url)}\">{escape(entry.title)}</a>"
                f" | 评分 {score_text} | 热度 {entry.votes} | Rank {entry.rank or '-'}"
            )

            item = QListWidgetItem("")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.bangumi_results_list.addItem(item)

            link_label = QLabel(row_html)
            link_label.setTextFormat(Qt.RichText)
            link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            link_label.setOpenExternalLinks(True)
            link_label.setWordWrap(True)
            link_label.setToolTip(entry.subtitle or entry.info or entry.title)
            link_label.setStyleSheet("padding: 2px 0;")

            item.setSizeHint(link_label.sizeHint())
            self.bangumi_results_list.setItemWidget(item, link_label)

    def _on_bangumi_failed(self, error_message: str) -> None:
        self.bangumi_progress_bar.hide()
        self._set_bangumi_recommendation_text("推荐失败，请稍后再试。")
        QMessageBox.warning(self, "Bangumi", f"加载失败:\n{error_message}")

    def _set_bangumi_recommendation(self, entry: BangumiAnimeEntry | None) -> None:
        if entry is None:
            self._set_bangumi_recommendation_text("当前条件下没有可推荐的番剧。")
            return

        score_text = f"{entry.score:.1f}" if entry.score is not None else "-"
        detail = entry.subtitle or entry.info or "Bangumi 推荐"
        self._set_bangumi_recommendation_text(
            f"今日推荐: {entry.title}\n评分 {score_text} | 热度 {entry.votes} | Rank {entry.rank or '-'}\n{detail}"
        )

    def _set_bangumi_recommendation_text(self, text: str) -> None:
        self.bangumi_recommendation_label.setText(text)
        self.bangumi_recommendation_label.setToolTip(text)
