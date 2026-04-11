from __future__ import annotations

from PySide6.QtCore import QDate, QDateTime, QPoint, QTime, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QAbstractItemView, QInputDialog, QListWidgetItem, QMenu, QMessageBox

from app.ui.pages import TodoDueDateDialog
from app.ui.todo_widgets import TodoRowWidget


class TodoWindowMixin:
    def set_todo_filter(self, filter_key: str) -> None:
        normalized_filter = filter_key if filter_key in {
            "all",
            "today",
            "future_3_days",
            "overdue",
            "long_term",
        } else "all"
        if self._todo_filter == normalized_filter:
            self._update_todo_filter_buttons()
            return

        self._todo_filter = normalized_filter
        self._update_todo_filter_buttons()
        self._refresh_list()

    def _update_todo_filter_buttons(self) -> None:
        button_map = {
            "all": self.filter_all_button,
            "today": self.filter_today_button,
            "future_3_days": self.filter_future_button,
            "overdue": self.filter_overdue_button,
            "long_term": self.filter_longterm_button,
        }
        for filter_key, button in button_map.items():
            button.blockSignals(True)
            button.setChecked(self._todo_filter == filter_key)
            button.blockSignals(False)

        allow_reorder = self._todo_filter == "all"
        self.todo_list.setDragEnabled(allow_reorder)
        self.todo_list.viewport().setAcceptDrops(allow_reorder)
        self.todo_list.setAcceptDrops(allow_reorder)
        self.todo_list.setDragDropMode(
            QAbstractItemView.InternalMove if allow_reorder else QAbstractItemView.NoDragDrop
        )

    def add_todo(self) -> None:
        text = self.input_edit.text()
        if not text.strip():
            return

        try:
            self._todo_controller.add_todo(
                title=text,
                due_enabled=self.enable_due_checkbox.isChecked(),
                due_date=self._due_date,
                due_time=self._due_time,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Warning", str(error))
            return

        self.input_edit.clear()
        self._refresh_list(scroll_to_bottom=True)

    def _toggle_due_edit_enabled(self, checked: bool) -> None:
        if not checked:
            self._due_popup_show_timer.stop()
            self._due_popup_hide_timer.stop()
            self.due_popup.hide()
            return

        if self.enable_due_checkbox.underMouse():
            self._due_popup_show_timer.start()

    def eventFilter(self, watched, event):  # type: ignore[override]
        if watched is self.enable_due_checkbox:
            if event.type() == event.Type.Enter and self.enable_due_checkbox.isChecked():
                self._due_popup_show_timer.start()
            elif event.type() == event.Type.Leave:
                self._due_popup_show_timer.stop()
                self._due_popup_hide_timer.start()
            elif event.type() == event.Type.MouseButtonPress:
                self._due_popup_show_timer.stop()
        elif watched is self.due_popup:
            if event.type() == event.Type.Enter:
                self._due_popup_hide_timer.stop()
            elif event.type() == event.Type.Leave:
                self._due_popup_hide_timer.start()

        return super().eventFilter(watched, event)

    def _show_due_popup(self) -> None:
        if not self.enable_due_checkbox.isChecked():
            return

        anchor = self.enable_due_checkbox.mapToGlobal(QPoint(0, self.enable_due_checkbox.height() + 6))
        popup_width = 280
        popup_height = 260
        screen = QApplication.screenAt(anchor) or QApplication.primaryScreen()
        if screen is None:
            return

        bounds = screen.availableGeometry()
        x = max(bounds.left(), min(anchor.x(), bounds.right() - popup_width))
        y = max(bounds.top(), min(anchor.y(), bounds.bottom() - popup_height))
        self.due_popup.setGeometry(x, y, popup_width, popup_height)
        self.due_popup.show()
        self.due_popup.raise_()

    def _hide_due_popup_if_outside(self) -> None:
        if not self.due_popup.isVisible():
            return

        if self.due_hour_combo.view().isVisible() or self.due_minute_combo.view().isVisible():
            return

        cursor_global = QCursor.pos()
        due_local = self.enable_due_checkbox.mapFromGlobal(cursor_global)
        over_due = self.enable_due_checkbox.rect().contains(due_local)
        over_popup = self.due_popup.geometry().contains(cursor_global)
        if over_due or over_popup:
            return
        self.due_popup.hide()

    def _on_due_date_changed(self, selected_date: QDate) -> None:
        self._due_date = selected_date

    def _on_due_time_changed(self, _value: str) -> None:
        hour = int(self.due_hour_combo.currentText())
        minute = int(self.due_minute_combo.currentText())
        self._due_time = QTime(hour, minute, 0)

    def _is_due_soon(self, due_at: str | None, done: bool) -> bool:
        return self._todo_controller.is_due_soon(due_at, done, self._due_soon_minutes)

    def refresh_main_page(self) -> None:
        self._refresh_list()
        self._refresh_quote()

    def _refresh_quote(self) -> None:
        self._current_quote = self._content_service.pick_quote(
            self._philosopher_quotes,
            current_quote=self._current_quote,
        )
        if not self._current_quote:
            self.quote_box.set_quote("No quotes available.")
            return

        self.quote_box.set_quote(
            self._current_quote.get("quote", ""),
            self._current_quote.get("author", ""),
        )

    def _refresh_list(self, keep_scroll: bool = False, scroll_to_bottom: bool = False) -> None:
        scroll_bar = self.todo_list.verticalScrollBar()
        previous_scroll = scroll_bar.value()
        todos = self._filter_todos(self._todo_controller.list_todos())
        self._sync_todo_list_items(todos)

        if scroll_to_bottom:
            self.todo_list.scrollToBottom()
        elif keep_scroll:
            scroll_bar.setValue(previous_scroll)

    def _sync_todo_list_items(self, todos) -> None:
        existing_items = {}
        for index in range(self.todo_list.count()):
            item = self.todo_list.item(index)
            todo_id = item.data(Qt.UserRole)
            if todo_id is not None:
                existing_items[int(todo_id)] = item

        target_ids = {todo.id for todo in todos}
        for index in range(self.todo_list.count() - 1, -1, -1):
            item = self.todo_list.item(index)
            todo_id = item.data(Qt.UserRole)
            if todo_id is None or int(todo_id) in target_ids:
                continue
            self.todo_list.removeItemWidget(item)
            self.todo_list.takeItem(index)

        for target_index, todo in enumerate(todos):
            item = existing_items.get(todo.id)
            if item is None:
                item, row_widget = self._create_todo_list_item(todo)
                self.todo_list.insertItem(target_index, item)
                self._update_todo_list_item(item, todo, row_widget)
                continue

            current_index = self.todo_list.row(item)
            if current_index != target_index:
                widget = self.todo_list.itemWidget(item)
                if widget is not None:
                    self.todo_list.removeItemWidget(item)
                moved_item = self.todo_list.takeItem(current_index)
                self.todo_list.insertItem(target_index, moved_item)
                if widget is not None:
                    self.todo_list.setItemWidget(moved_item, widget)
                item = moved_item

            self._update_todo_list_item(item, todo)

    def _filter_todos(self, todos) -> list:
        if self._todo_filter == "all":
            return todos

        now = QDateTime.currentDateTime()
        today = now.date()
        future_end = today.addDays(3)
        filtered = []
        for todo in todos:
            due_at = getattr(todo, "due_at", None)
            done = bool(getattr(todo, "done", False))

            if self._todo_filter == "long_term":
                if not due_at:
                    filtered.append(todo)
                continue

            if not due_at:
                continue

            due_time = QDateTime.fromString(due_at, Qt.ISODate)
            if not due_time.isValid():
                continue

            due_date = due_time.date()
            if self._todo_filter == "today":
                if due_date == today:
                    filtered.append(todo)
            elif self._todo_filter == "future_3_days":
                if today < due_date <= future_end:
                    filtered.append(todo)
            elif self._todo_filter == "overdue":
                if not done and due_time < now:
                    filtered.append(todo)

        return filtered

    def _create_todo_list_item(self, todo) -> tuple[QListWidgetItem, TodoRowWidget]:
        item = QListWidgetItem("")
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable)

        row_widget = TodoRowWidget(
            todo.title,
            todo.due_at,
            todo.done,
            self._is_due_soon(todo.due_at, todo.done),
            self.todo_list,
        )
        row_widget.indicator.clicked.connect(
            lambda _checked=False, current_item=item: self.toggle_todo(current_item)
        )
        return item, row_widget

    def _update_todo_list_item(self, item: QListWidgetItem, todo, row_widget: TodoRowWidget | None = None) -> None:
        item.setData(Qt.UserRole, todo.id)
        item.setData(Qt.UserRole + 1, todo.title)
        item.setData(Qt.UserRole + 2, todo.due_at)

        widget = row_widget or self.todo_list.itemWidget(item)
        if isinstance(widget, TodoRowWidget):
            widget.update_content(
                todo.title,
                todo.due_at,
                todo.done,
                self._is_due_soon(todo.due_at, todo.done),
            )
            item.setSizeHint(widget.sizeHint())
            if row_widget is not None:
                self.todo_list.setItemWidget(item, row_widget)

    def persist_current_order(self) -> None:
        todo_ids = []
        for index in range(self.todo_list.count()):
            item = self.todo_list.item(index)
            todo_id = item.data(Qt.UserRole)
            if todo_id is not None:
                todo_ids.append(int(todo_id))

        if not todo_ids:
            return

        self._todo_controller.update_order(todo_ids)
        self._refresh_list(keep_scroll=True)

    def toggle_todo(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        if todo_id is None:
            return

        self._todo_controller.toggle_done(int(todo_id))
        self._refresh_list(keep_scroll=True)

    def _show_todo_context_menu(self, position: QPoint) -> None:
        item = self.todo_list.itemAt(position)
        if item is None:
            return

        self.todo_list.setCurrentItem(item)
        menu = QMenu(self)
        edit_title_action = menu.addAction("Edit title")
        edit_due_action = menu.addAction("Edit due time")
        clear_due_action = menu.addAction("Clear due time")
        menu.addSeparator()
        delete_action = menu.addAction("Delete task")

        selected_action = menu.exec(self.todo_list.viewport().mapToGlobal(position))
        if selected_action is edit_title_action:
            self._edit_todo_title(item)
        elif selected_action is edit_due_action:
            self._edit_todo_due_time(item)
        elif selected_action is clear_due_action:
            self._clear_todo_due_time(item)
        elif selected_action is delete_action:
            self._delete_todo(item)

    def _edit_todo_title(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        current_title = item.data(Qt.UserRole + 1) or ""
        if todo_id is None:
            return

        new_title, accepted = QInputDialog.getText(
            self,
            "Edit Title",
            "Task title",
            text=str(current_title),
        )
        if not accepted:
            return

        try:
            self._todo_controller.update_todo_title(int(todo_id), new_title)
        except ValueError as error:
            QMessageBox.warning(self, "Warning", str(error))
            return
        self._refresh_list(keep_scroll=True)

    def _edit_todo_due_time(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        due_at = item.data(Qt.UserRole + 2)
        if todo_id is None:
            return

        dialog = TodoDueDateDialog(str(due_at) if due_at else None, self)
        if dialog.exec() != TodoDueDateDialog.Accepted:
            return

        due_date, due_time = dialog.selected_due()
        self._todo_controller.update_todo_due_at(
            int(todo_id),
            due_enabled=True,
            due_date=due_date,
            due_time=due_time,
        )
        self._refresh_list(keep_scroll=True)

    def _clear_todo_due_time(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        if todo_id is None:
            return

        self._todo_controller.update_todo_due_at(
            int(todo_id),
            due_enabled=False,
            due_date=QDate.currentDate(),
            due_time=QTime(0, 0),
        )
        self._refresh_list(keep_scroll=True)

    def _delete_todo(self, item: QListWidgetItem) -> None:
        todo_id = item.data(Qt.UserRole)
        title = item.data(Qt.UserRole + 1) or "this task"
        if todo_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Delete '{title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._todo_controller.delete_todo(int(todo_id))
        self._refresh_list(keep_scroll=True)

    def delete_completed(self) -> None:
        self._todo_controller.delete_completed()
        self._refresh_list(keep_scroll=True)
