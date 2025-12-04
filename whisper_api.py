# whisper_api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tasks import run_whisper_task
import shutil
import uuid
import os
from fastapi.staticfiles import StaticFiles
import database

UPLOAD_DIR = "upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# 生产环境提醒：如果以后要上线，建议把 allow_origins=["*"] 改成具体的域名列表（比如 ["https://your-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
database.init_db()

# 挂载静态文件目录
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/transcribe")
async def create_task(file: UploadFile = File(...)):
    file_name = file.filename
    # 1. 给文件起个唯一的名
    unique_filename = f"upload_{file_name}_{uuid.uuid4()}.mp3"
    
    # 2. 保存文件
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. 创建任务并入队
    task_id = database.create_task(unique_filename)
    run_whisper_task(task_id, file_path)

    return {
        "status": "queued",
        "task_id": task_id,
        "message": "您的任务已在后台排队，请稍后查看结果文件。"
    }

@app.get("/task/{task_id}")
async def get_task_status(task_id: int):
    task = database.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task