# Todo Desktop (MVP)

A floating todo app for Windows based on `PySide6 + SQLite`.

Current features:

- Floating window (`Always on Top`)
- Frameless window with drag-to-move
- Edge snapping when dragging near screen borders
- Minimize to system tray (close button also hides to tray)
- Global hotkey to show/hide window: `Ctrl + Shift + Space`
- Add / toggle done / delete todos
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

On first run, database file is created automatically:

`data/todo.db`

## Notes

- If `Ctrl + Shift + Space` is already used by another app, global hotkey registration may fail.
- Use tray icon right-click menu `Quit` for full exit.

