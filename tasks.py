from huey import SqliteHuey
import whisper_api
import os

# 1. 配置 Huey 使用本地文件做数据库
huey = SqliteHuey('whisper_queue.db')

# 加载模型

print("--- Worker: 正在加载 Whisper 模型 ---")
model = whisper.load_model("small", device="cpu")
print("--- Worker: 模型加载完毕  ---")

# 3. 定义任务
@huey.task()
def run_whisper_task(file_path):
    """
    
    """