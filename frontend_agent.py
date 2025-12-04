from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os

# 定义输出结构
class UICommand(BaseModel):
    action: str = Field(description="The action to perform. Allowed values: 'change_color', 'change_size', 'change_text', 'unknown'. If the user's intent is not clear or not related to UI control, use 'unknown'.")
    target: str = Field(description="The target element, e.g., 'background', 'title', 'button'. If action is 'unknown', this can be empty or 'none'.")
    value: str = Field(description="The value for the action. IMPORTANT: For 'change_color', this MUST be a valid English CSS color name (e.g., 'red', 'skyblue', 'pink') or a Hex code (e.g., '#FF0000'). Do NOT use Chinese characters for color values. If action is 'unknown', put the original user text here.")

def process_voice_command(text: str, api_key: str):
    # 初始化 DeepSeek 模型 (兼容 OpenAI 协议)
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0
    )
    
    # 使用 JsonOutputParser
    parser = JsonOutputParser(pydantic_object=UICommand)

    # 定义 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that controls a web UI. Extract the user's intent into a structured JSON command.\n{format_instructions}\nIf the user's intent is not related to controlling the UI (e.g. general chat), set action to 'unknown' and put the original text in 'value'.\nIMPORTANT: When the action is 'change_color', translate the color to a valid English CSS color name or Hex code."),
        ("user", "{text}")
    ])

    # 将 format_instructions 注入到 prompt 中
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    # 构建链
    chain = prompt | llm | parser

    # 执行
    try:
        result = chain.invoke({
            "text": text
        })
        return result
    except Exception as e:
        return {"error": str(e)}
