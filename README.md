# Todo Desktop

一个基于 `PySide6 + SQLite` 的 Windows 桌面待办应用，采用悬浮置顶窗口设计，支持截止时间、拖拽排序、系统托盘、全局快捷键，以及内置塔罗抽牌和哲学语录展示。

## 项目特点

### 待办功能

- 支持输入任务后按回车，或点击 `+` 按钮添加待办
- 支持为待办设置可选截止时间
- 未设置截止时间的任务显示为“长期事务”
- 即将到期的任务会高亮提醒
- 点击任务前方圆形按钮可切换完成 / 未完成状态
- 支持拖拽调整待办顺序
- 拖拽到列表上下边缘时会自动滚动
- 支持一键清空所有已完成任务
- 支持 `refresh` 刷新待办列表

### 主页附加内容

- 待办列表下方显示哲学语录
- 语录数据来自独立配置文件 `app/data/philosopher_quotes.json`
- 当前内置叔本华、加缪、萨特、尼采等多条中文语录
- 点击 `refresh` 会同时刷新待办列表和随机语录

### 窗口与交互

- 无边框、圆角、毛玻璃风格浮动窗口
- 窗口始终置顶
- 支持拖动标题栏移动窗口
- 拖到屏幕边缘附近时自动吸附
- 右下角支持拖拽缩放
- 自动保证窗口至少有一部分保持在屏幕内，避免拖丢
- 自动记忆窗口大小和位置
- 支持系统托盘
- 点击右上角 `-` 最小化到托盘
- 点击右上角 `x` 或托盘菜单 `Quit` 彻底退出
- 支持全局快捷键 `Ctrl + Shift + Space` 显示 / 隐藏窗口

### 设置页

- 可在主页点击 `config` 进入设置页
- 支持设置默认窗口宽度和高度
- 支持设置“即将到期”提醒时间窗口
- 支持将当前窗口尺寸直接保存为默认尺寸

### 塔罗功能

- 内置塔罗页面
- 支持三张牌阵：`Past / Present / Future`
- 可输入问题后抽取三张牌
- 每张牌会随机正位或逆位
- 显示卡牌名称、朝向、关键词与解读摘要
- 抽牌结果会保存到本地 SQLite
- 支持查看历史抽牌记录
- 若配置了兼容 OpenAI 的模型接口，可生成更自然的塔罗总结
- 未配置模型时，会使用本地 fallback 摘要逻辑

## 项目结构

```txt
todo/
  app/
    core/
      models.py
      tarot_interpreter.py
    data/
      philosopher_quotes.json
      storage.py
      tarot_cards.json
    ui/
      main_window.py
  data/
    todo.db
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

## 启动项目

```bash
python main.py
```

首次运行时会自动创建本地数据库文件：

```txt
data/todo.db
```

## 打包为 EXE

建议在项目虚拟环境中执行：

```powershell
.\build.bat
```

打包完成后可运行：

```txt
dist/Todo/Todo.exe
```

如果要拷贝到其他电脑，请复制整个 `dist/Todo` 目录，而不是只复制单个 `.exe` 文件。

## 可选模型配置

塔罗摘要功能支持通过环境变量接入兼容 OpenAI API 的模型服务：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL_NAME`
- `TAROT_MODEL_TEMPERATURE`

当前代码默认值中：

- `OPENAI_BASE_URL` 默认是 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `OPENAI_MODEL_NAME` 默认是 `qwen-max`

如果未配置 `OPENAI_API_KEY`，程序仍可正常运行，只是塔罗总结会退回本地简化逻辑。

## 本地数据说明

- 待办数据和塔罗历史保存在本地 SQLite 数据库中
- 窗口大小、窗口位置、默认尺寸、提醒时间通过 `QSettings` 保存
- 哲学语录来自本地 JSON 配置文件，可自行扩展或替换

## 注意事项

- 全局快捷键 `Ctrl + Shift + Space` 如果被其他程序占用，可能注册失败
- 该项目当前主要面向 Windows，快捷键实现依赖 Windows 原生接口
- 若直接关闭窗口，程序默认会隐藏到托盘，而不是退出
- 需要彻底退出时，请使用右上角 `x` 或托盘菜单 `Quit`
