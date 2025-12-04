from huey import SqliteHuey
import whisper
import os
import database
import frontend_agent
from dotenv import load_dotenv

load_dotenv()

# 1. 配置 Huey 使用本地文件做数据库
huey = SqliteHuey('whisper_queue.db')

RESULTS_DIR = "results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)


# 加载模型

print("--- Worker: 正在加载 Whisper 模型 ---")
model = whisper.load_model("small", device="cpu")
print("--- Worker: 模型加载完毕  ---")

# 3. 定义任务
@huey.task()
def run_whisper_task(task_id, file_path):
    """
    这个函数在后台 Worker 里运行，不会卡住 API
    """
    print(f"--- Worker: 开始处理任务 {task_id} ---")
    database.update_task_status(task_id, "processing")

    
    try:
        # 这里是调用本地的 Whisper 服务来进行 Speech To Text 的服务，只要给出路径，ffmpeg 会自动读取这个路径
        # 这个项目原作使用的是 OpenAI 的 Whisper 服务，需要通过with语句读取文件，上传音频文件给 OpenAI。
        result = model.transcribe(file_path, fp16=False)
        # 真实场景里，这里应该把结果存进数据库
        # 这里为了演示，只打印出来，并把结果写到一个文本文件里
        # base_name = os.path.splitext(os.path.basename(file_path))[0]
        # output_txt = os.path.join(RESULTS_DIR, base_name + '.txt')
        # with open(output_txt, "w", encoding="utf-8") as f:
        #     f.write(result["text"])
        # print("--- Worker: 处理完毕，结果写入文件：{}".format(output_txt))
        
        
        # 4. 调用 LangChain 处理意图 (如果有 API KEY)
        final_result = result["text"]
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            print(f"--- Worker: 正在调用 LLM 分析意图, {final_result} ---")
            llm_result = frontend_agent.process_voice_command(result["text"], api_key)
            # 将 LLM 的结果合并到最终结果中，或者直接存 JSON
            # 这里我们把 LLM 的结果转成字符串存进去，或者存成 JSON 字符串
            import json
            """
            json.dump(obj): 接收 Python 对象（如字典、列表） → 转换成 JSON 字符串；
            json.loads(str): 接收 JSON 字符串 → 转换成 Python 对象（如字典、列表）
            """
            final_result = json.dumps(llm_result, ensure_ascii=False)
            print("--- Worker: LLM 分析完毕: {} ---".format(final_result))

        database.update_task_status(task_id, "completed", result=final_result)
        return final_result

    except Exception as e:
        print("--- Worker: 处理失败：{}".format(e))
        database.update_task_status(task_id, "failed", result=str(e))
        return str(e)