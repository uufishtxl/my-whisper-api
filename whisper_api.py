from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
import whisper
import uvicorn
import shutil
import os

app = FastAPI()

# --- 1. 全局加载模型 (只在启动时加载一次) ---
print("正在加载 Whisper 模型，请稍候...")
# 使用 CPU 加载 tiny 模型 (你可以改成 small 或 medium)
# fp16=False 是为了兼容你的 CPU 环境
model = whisper.load_model("small", device="cpu")
print("✅ 模型加载完毕，服务已就绪！")

# --- 🕵️‍♂️ 侦探中间件：打印接收到的真实请求 ---
@app.middleware("http")
async def log_request_info(request: Request, call_next):
    print("\n" + "="*30)
    print(f"📡 收到请求: {request.method} {request.url}")
    
    # 1. 打印 Header，看看 Content-Type 对不对
    ct = request.headers.get("content-type", "没传 Content-Type")
    print(f"📋 Content-Type: {ct}")
    
    # 2. 只有 multipart 才有 boundary，如果没有 boundary，文件肯定传不过来
    if "multipart/form-data" in ct and "boundary" not in ct:
        print("❌ 严重错误: Content-Type 里缺少 boundary！你是不是手动设置了 Header？")
    
    # 继续处理请求
    response = await call_next(request)
    
    if response.status_code == 422:
        print("❌ 结果: 校验失败 (422)。服务器没找到想要的文件字段。")
    else:
        print(f"✅ 结果: 状态码 {response.status_code}")
    
    print("="*30 + "\n")
    return response

# --- 你的业务代码 ---
print("Loading model...")
# model = whisper.load_model("tiny", device="cpu") 
# 为了调试快一点，先注释掉加载模型，反正 422 还没进到这一步

@app.post("/transcribe")
async def create_task(file: UploadFile = File(...)):
    #                     ^^^^
    #    请死死盯着这个名字，它叫 "file"
    #    那么你的 Postman/Requests 里的 key 也必须叫 "file"
    
    temp_filename = f"temp_{file.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"收到文件: {temp_filename}，开始转录...")
        
        # 3. 调用 Whisper 进行转录
        # fp16=False 防止报错
        result = model.transcribe(temp_filename, fp16=False)
        
        # 4. 清理临时文件
        os.remove(temp_filename)
        
        return {
            "filename": file.filename,
            "text": result["text"].strip(),
            "language": result["language"]
        }

    except Exception as e:
        return {"error": str(e)}

# 启动代码
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)