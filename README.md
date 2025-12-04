# my-whisper-api

一个基于 FastAPI 和 Whisper 的音频转文字 API，使用 Huey 进行异步处理。

## 项目结构

```
my-whisper-api/
├── tasks.py          # 任务处理文件
├── whisper_api.py    # FastAPI 应用
├── huey.db           # Huey 数据库
├── huey.db-wal       # Huey 数据库的 WAL 文件
├── whisper_queue.db  # Whisper 任务队列数据库
├── README.md         # 项目说明
└── pyproject.toml    # 项目配置
```

## `uv`开发指南

### 初始化项目

```bash
uv init
```

### 添加和安装依赖

```bash
uv add <package_name>
uv add <package_name> --dev
```

#### 关于 `"numpy<2.0"

`uv` 会自动安装 `numpy`，但是版本会比较高，导致 `whisper` 无法正常工作，所以需要手动安装 `numpy<2.0`。

```bash
uv add "numpy<2.0"
```

由于 Shell 的限制，建议 `numpy<2.0` 用双引号括起来。这主要是因为 `>` 在 Windows Shell 中是重定向操作符，所以需要使用引号来避免歧义。

### 运行项目

因为本项目使用的是 FastAPI 框架，因此运行项目时，会执行 `uvicorn` 命令。

```bash
uv run uvicorn whisper_api:app --reload
```

默认在 `8000` 端口运行。如果要修改端口，可以使用 `--port` 参数。比如：

```bash
uv run uvicorn whisper_api:app --reload --port 8001
```

### 运行 `huey` worker

此项目使用了 `huey` 作为任务队列，因此需要运行 `huey` worker。

```bash
uv run huey_consumer tasks.huey
```

`huey_consumer` 会持续监听任务队列，当有任务时，会自动执行。

Q：为什么是 `tasks.huey`，而不是 `tasks.py`？

A：因为 `huey` 会自动加载 `tasks.py` 中的 `huey` 对象，所以这里只需要指定 `tasks.huey` 即可。注意哦，这里不是导入文件，而是导入 `tasks.py` 中的 `huey` 对象，是给 Python 解释器看的。 