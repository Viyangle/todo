# Todo Desktop

基于 `PySide6 + SQLite` 的 Windows 桌面待办应用，支持全局快捷键、系统托盘、塔罗抽牌和 Bangumi 年度动画榜查询。

## 功能概览

- Todo 管理：新增、完成切换、编辑标题、删除、拖拽排序
- 截止时间：支持设置和清除，到期前高亮提醒
- 窗口体验：无边框悬浮、边缘吸附、记忆窗口大小与位置
- 系统托盘：最小化到托盘、托盘菜单显示 / 隐藏与退出
- 全局热键：`Ctrl + Shift + Space` 显示或隐藏窗口
- 塔罗功能：抽牌、历史记录、收藏、可选 AI 总结
- Bangumi 榜单：按年份加载综合 / 评分 / 热度榜，支持最低热度过滤

## 项目结构

```txt
todo/
  app/
    core/
      bangumi_service.py
      content_service.py
      models.py
      tarot_interpreter.py
    data/
      philosopher_quotes.json
      storage.py
      tarot_cards.json
    ui/
      controllers.py
      game_widgets.py
      main_window.py
      main_window_bangumi.py
      main_window_tarot.py
      main_window_todo.py
      pages.py
      todo_widgets.py
      widgets.py
      window_manager.py
      window_widgets.py
  main.py
  requirements.txt
  build.bat
  Todo.spec
```

## 运行环境

- Python 3.10+
- Windows 10 / 11

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动

```bash
python main.py
```

首次运行会自动创建本地数据库，默认位于 `QStandardPaths.AppDataLocation` 下的 `todo.db`。

## 打包 EXE

```powershell
.\build.bat
```

打包输出目录：`dist/Todo/`

## AI 配置（可选）

塔罗总结支持兼容 OpenAI API 的模型服务，环境变量如下：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL_NAME`
- `TAROT_MODEL_TEMPERATURE`

未配置 API Key 时，程序会回退到本地简化总结逻辑。

## 数据说明

- Todo 与塔罗历史：SQLite
- 窗口尺寸、位置与偏好：`QSettings`
- 塔罗牌与哲学语录：本地 JSON 文件
