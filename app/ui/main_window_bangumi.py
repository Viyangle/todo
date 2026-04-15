from __future__ import annotations

import re
from html import escape

from PySide6.QtCore import QDate, QObject, QSize, QThread, Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QListWidgetItem, QMessageBox

from app.core.bangumi_service import BangumiRecommendation
from app.ui.controllers import BangumiController


class BangumiListWorker(QObject):
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
    ) -> None:
        super().__init__()
        self._controller = controller
        self._year = year
        self._ranking_type = ranking_type
        self._limit = limit
        self._min_votes = min_votes

    def run(self) -> None:
        try:
            entries = self._controller.fetch_year_rankings(
                year=self._year,
                ranking_type=self._ranking_type,
                limit=self._limit,
                min_votes=self._min_votes,
                progress_callback=self.progress.emit,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(entries)


class BangumiRecommendWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        controller: BangumiController,
    ) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:
        try:
            recommendation = self._controller.recommend_from_year_range(
                start_year=1995,
                end_year=2026,
                top_n=50,
                min_votes=0,
                progress_callback=self.progress.emit,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(recommendation)


class BangumiWindowMixin:
    _page_progress_pattern = re.compile(r"page\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)
    _range_progress_pattern = re.compile(r"\((\d+)\s*/\s*(\d+)\)")

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

    def _configure_bangumi_recommend_page(self) -> None:
        self.bangumi_recommend_progress_bar.hide()
        self.bangumi_recommend_progress_bar.setRange(0, 100)
        self.bangumi_recommend_progress_bar.setValue(0)
        self._bangumi_recommend_thread = None
        self._bangumi_recommend_worker = None
        self._bangumi_recommend_loading = False
        self._clear_bangumi_recommendation_card()

    def _on_bangumi_min_heat_toggled(self, checked: bool) -> None:
        self.bangumi_min_heat_checkbox.setToolTip(
            f"Use Bangumi min votes from settings ({self._bangumi_min_votes})" if checked else "No min votes limit"
        )

    def load_bangumi_rankings(self) -> None:
        if self._bangumi_loading:
            return

        year = int(self.bangumi_year_spin.value())
        ranking_type = str(self.bangumi_ranking_combo.currentData() or "comprehensive")
        limit = int(self.bangumi_limit_combo.currentData() or 20)
        min_votes = self._bangumi_min_votes if self.bangumi_min_heat_checkbox.isChecked() else 0

        self._bangumi_loading = True
        self.bangumi_fetch_button.setEnabled(False)
        self.bangumi_fetch_button.setText("loading...")
        self.bangumi_open_recommend_page_button.setEnabled(False)
        self.bangumi_ranking_combo.setEnabled(False)
        self.bangumi_year_spin.setEnabled(False)
        self.bangumi_limit_combo.setEnabled(False)
        self.bangumi_min_heat_checkbox.setEnabled(False)
        self.bangumi_progress_bar.setRange(0, 0)
        self.bangumi_progress_bar.show()
        self.bangumi_results_list.clear()

        self._bangumi_thread = QThread(self)
        self._bangumi_worker = BangumiListWorker(
            controller=self._bangumi_controller,
            year=year,
            ranking_type=ranking_type,
            limit=limit,
            min_votes=min_votes,
        )
        self._bangumi_worker.moveToThread(self._bangumi_thread)
        self._bangumi_thread.started.connect(self._bangumi_worker.run)
        self._bangumi_worker.progress.connect(self._on_bangumi_progress)
        self._bangumi_worker.finished.connect(self._on_bangumi_finished)
        self._bangumi_worker.failed.connect(self._on_bangumi_failed)
        self._bangumi_worker.finished.connect(self._cleanup_bangumi_worker)
        self._bangumi_worker.failed.connect(self._cleanup_bangumi_worker)
        self._bangumi_thread.start()

    def load_bangumi_recommendation(self) -> None:
        if self._bangumi_recommend_loading:
            return

        self._bangumi_recommend_loading = True
        self.bangumi_recommend_pick_button.setEnabled(False)
        self.bangumi_recommend_pick_button.setText("loading...")
        self.bangumi_recommend_progress_bar.setRange(0, 0)
        self.bangumi_recommend_progress_bar.show()

        self._bangumi_recommend_thread = QThread(self)
        self._bangumi_recommend_worker = BangumiRecommendWorker(
            controller=self._bangumi_controller,
        )
        self._bangumi_recommend_worker.moveToThread(self._bangumi_recommend_thread)
        self._bangumi_recommend_thread.started.connect(self._bangumi_recommend_worker.run)
        self._bangumi_recommend_worker.progress.connect(self._on_bangumi_recommend_progress)
        self._bangumi_recommend_worker.finished.connect(self._on_bangumi_recommend_finished)
        self._bangumi_recommend_worker.failed.connect(self._on_bangumi_recommend_failed)
        self._bangumi_recommend_worker.finished.connect(self._cleanup_bangumi_recommend_worker)
        self._bangumi_recommend_worker.failed.connect(self._cleanup_bangumi_recommend_worker)
        self._bangumi_recommend_thread.start()

    def _cleanup_bangumi_worker(self, *_args) -> None:
        self._bangumi_loading = False
        self.bangumi_fetch_button.setEnabled(True)
        self.bangumi_fetch_button.setText("load")
        self.bangumi_open_recommend_page_button.setEnabled(True)
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

    def _cleanup_bangumi_recommend_worker(self, *_args) -> None:
        self._bangumi_recommend_loading = False
        self.bangumi_recommend_pick_button.setEnabled(True)
        self.bangumi_recommend_pick_button.setText("pick")
        self.bangumi_recommend_progress_bar.hide()
        self.bangumi_recommend_progress_bar.setRange(0, 100)
        self.bangumi_recommend_progress_bar.setValue(0)

        if self._bangumi_recommend_thread is not None:
            self._bangumi_recommend_thread.quit()
            self._bangumi_recommend_thread.wait()
            self._bangumi_recommend_thread.deleteLater()
            self._bangumi_recommend_thread = None
        if self._bangumi_recommend_worker is not None:
            self._bangumi_recommend_worker.deleteLater()
            self._bangumi_recommend_worker = None

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

    def _on_bangumi_recommend_progress(self, message: str) -> None:
        text = message.strip()
        if not text:
            return

        range_match = self._range_progress_pattern.search(text)
        if range_match:
            current = int(range_match.group(1))
            total = max(1, int(range_match.group(2)))
            self.bangumi_recommend_progress_bar.setRange(0, total)
            self.bangumi_recommend_progress_bar.setValue(min(current, total))
            return

        if "cache" in text.lower():
            self.bangumi_recommend_progress_bar.setRange(0, 1)
            self.bangumi_recommend_progress_bar.setValue(1)

    def _on_bangumi_finished(self, entries) -> None:
        self.bangumi_results_list.clear()
        self.bangumi_progress_bar.setRange(0, 1)
        self.bangumi_progress_bar.setValue(1)
        if not entries:
            return

        for index, entry in enumerate(entries, start=1):
            score_text = f"{entry.score:.1f}" if entry.score is not None else "-"
            row_html = (
                f"{index:>2}. "
                f"<a href=\"{escape(entry.url)}\">{escape(entry.title)}</a>"
                f" | Score {score_text} | Votes {entry.votes} | Rank {entry.rank or '-'}"
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
            link_label.setStyleSheet("padding: 4px 0; font-size: 15px;")

            item.setSizeHint(link_label.sizeHint())
            self.bangumi_results_list.setItemWidget(item, link_label)

    def _on_bangumi_recommend_finished(self, recommendation: BangumiRecommendation | None) -> None:
        self.bangumi_recommend_progress_bar.setRange(0, 1)
        self.bangumi_recommend_progress_bar.setValue(1)
        if recommendation is None:
            self._clear_bangumi_recommendation_card()
            return

        self._render_bangumi_recommendation(recommendation)

    def _on_bangumi_failed(self, error_message: str) -> None:
        self.bangumi_progress_bar.hide()
        QMessageBox.warning(self, "Bangumi", f"Load failed:\n{error_message}")

    def _on_bangumi_recommend_failed(self, error_message: str) -> None:
        self.bangumi_recommend_progress_bar.hide()
        QMessageBox.warning(self, "Bangumi Recommend", f"Load failed:\n{error_message}")

    def _render_bangumi_recommendation(self, recommendation: BangumiRecommendation) -> None:
        self.bangumi_recommend_name_label.setText(recommendation.title)
        score_text = f"{recommendation.score:.1f}" if recommendation.score is not None else "-"
        self.bangumi_recommend_meta_label.setText(
            f"Score {score_text} | Air Date {recommendation.air_date}"
        )
        summary = recommendation.summary.strip() or recommendation.info.strip() or "No summary available."
        self.bangumi_recommend_summary_label.setText(summary)
        self.bangumi_recommend_summary_label.setToolTip(summary)

        if recommendation.poster_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(recommendation.poster_data):
                scaled = pixmap.scaled(
                    QSize(260, 360),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.bangumi_recommend_poster_label.setPixmap(scaled)
                self.bangumi_recommend_poster_label.setText("")
                self.bangumi_recommend_poster_label.setToolTip(recommendation.title)
                return

        self.bangumi_recommend_poster_label.setPixmap(QPixmap())
        self.bangumi_recommend_poster_label.setText("Poster unavailable")
        self.bangumi_recommend_poster_label.setToolTip(recommendation.title)

    def _clear_bangumi_recommendation_card(self) -> None:
        self.bangumi_recommend_poster_label.setPixmap(QPixmap())
        self.bangumi_recommend_poster_label.setText("No poster")
        self.bangumi_recommend_name_label.setText("No recommendation yet.")
        self.bangumi_recommend_meta_label.setText("Score - | Air Date -")
        self.bangumi_recommend_summary_label.setText("Press pick to get one anime recommendation.")
        self.bangumi_recommend_summary_label.setToolTip("")
