from __future__ import annotations

from html import escape

from PySide6.QtCore import QDate, QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QLabel, QListWidgetItem, QMessageBox

from app.ui.controllers import BangumiController


class BangumiFetchWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

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
                progress_callback=None,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(entries)


class BangumiWindowMixin:
    def _configure_bangumi_page(self) -> None:
        current_year = QDate.currentDate().year()
        self.bangumi_year_spin.setValue(current_year)
        self.bangumi_ranking_combo.setCurrentIndex(0)
        self.bangumi_limit_combo.setCurrentIndex(1)
        self.bangumi_min_heat_checkbox.setChecked(True)
        self._on_bangumi_min_heat_toggled(True)
        self._bangumi_thread = None
        self._bangumi_worker = None
        self._bangumi_loading = False

    def _on_bangumi_min_heat_toggled(self, checked: bool) -> None:
        self.bangumi_min_heat_checkbox.setToolTip(
            f"开启后使用设置里的最低热度（{self._bangumi_min_votes}）" if checked else "关闭后不限制最低热度"
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
        self.bangumi_ranking_combo.setEnabled(False)
        self.bangumi_year_spin.setEnabled(False)
        self.bangumi_limit_combo.setEnabled(False)
        self.bangumi_min_heat_checkbox.setEnabled(False)
        self.bangumi_results_list.clear()

        self._bangumi_thread = QThread(self)
        self._bangumi_worker = BangumiFetchWorker(
            controller=self._bangumi_controller,
            year=year,
            ranking_type=ranking_type,
            limit=limit,
            min_votes=min_votes,
        )
        self._bangumi_worker.moveToThread(self._bangumi_thread)
        self._bangumi_thread.started.connect(self._bangumi_worker.run)
        self._bangumi_worker.finished.connect(self._on_bangumi_finished)
        self._bangumi_worker.failed.connect(self._on_bangumi_failed)
        self._bangumi_worker.finished.connect(self._cleanup_bangumi_worker)
        self._bangumi_worker.failed.connect(self._cleanup_bangumi_worker)
        self._bangumi_thread.start()

    def _cleanup_bangumi_worker(self, *_args) -> None:
        self._bangumi_loading = False
        self.bangumi_fetch_button.setEnabled(True)
        self.bangumi_ranking_combo.setEnabled(True)
        self.bangumi_year_spin.setEnabled(True)
        self.bangumi_limit_combo.setEnabled(True)
        self.bangumi_min_heat_checkbox.setEnabled(True)

        if self._bangumi_thread is not None:
            self._bangumi_thread.quit()
            self._bangumi_thread.wait()
            self._bangumi_thread.deleteLater()
            self._bangumi_thread = None
        if self._bangumi_worker is not None:
            self._bangumi_worker.deleteLater()
            self._bangumi_worker = None

    def _on_bangumi_finished(self, entries) -> None:
        self.bangumi_results_list.clear()
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
        QMessageBox.warning(self, "Bangumi", f"加载失败:\n{error_message}")
