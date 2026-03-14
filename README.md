# Todo Desktop

A floating Windows todo app built with `PySide6 + SQLite`.

## Features

- Always-on-top floating window
- Frameless glass-style UI with rounded corners
- Drag the title bar to move the window
- Snap to screen edges when dragged near them
- Resize the window with the bottom-right handle
- Remember window size and position after restart
- System tray support
- Minimize to tray with the top-right `-` button
- Quit the app with the top-right `x` button or tray menu
- Global hotkey to show or hide the window: `Ctrl + Shift + Space`
- Add todos with the input box or the `+` button
- Click the circle in front of a todo to mark it done or undone
- Clear all completed todos with the `clear` button
- Refresh the list with the `refresh` button
- Restore the default window size with the `default` button
- Drag and drop to reorder todos
- Auto-scroll while dragging near the top or bottom of the list
- Local SQLite persistence

## Project Structure

```txt
todo/
  app/
    core/
      models.py
    data/
      storage.py
    ui/
      main_window.py
  data/
  main.py
  requirements.txt
```

## Requirements

- Python 3.10+
- Windows 10/11

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On first run, the database file is created automatically:

`data/todo.db`

## Notes

- If `Ctrl + Shift + Space` is already used by another app, the global hotkey may fail to register.
- Window size and position are stored locally through `QSettings`.
- Use the tray menu `Quit` or the top-right `x` button for a full exit.
