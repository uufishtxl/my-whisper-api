# 如何规定 LLM 输出的 JSON 格式

在 LangChain 开发中，让 LLM 稳定输出结构化数据（如 JSON）是核心难点。主要有两种流派：

## 1. 软限制 (Soft Constraints) - Prompt Engineering

使用 `JsonOutputParser`。

**原理**：
通过 Prompt Engineering，在 Prompt 末尾注入一段格式说明（`format_instructions`），“求”模型输出 JSON。

**代码示例**：
```python
from langchain_core.output_parsers import JsonOutputParser

# 1. 定义解析器
parser = JsonOutputParser(pydantic_object=UICommand)

# 2. 定义 Prompt (必须包含 format_instructions 占位符)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant.\n{format_instructions}"),
    ("user", "{text}")
]).partial(format_instructions=parser.get_format_instructions()) # 使用 partial 注入

# 3. 构建链
chain = prompt | llm | parser
```

### 💡 进阶技巧：使用 `.partial()` "焊死" 变量

在上面的代码中，我们使用了 `.partial(format_instructions=...)`。

**为什么要这么做？**
Prompt 模板里有 `{format_instructions}` 这个占位符。如果不处理，每次调用 `chain.invoke` 时都必须手动传进去：
```python
# 笨办法：每次都要传
chain.invoke({
    "text": "...", 
    "format_instructions": parser.get_format_instructions() # 累赘！
})
```

**`.partial()` 的作用**：
它像 Python 的 `functools.partial` 一样，**提前填充**部分变量，生成一个新的 Prompt 模板。
```python
# 聪明办法：提前焊死
prompt = raw_prompt.partial(format_instructions=parser.get_format_instructions())

# 调用时清爽多了
chain.invoke({"text": "..."})
```

**执行时机**：
这个“焊死”的操作是在**代码定义阶段**（解释器执行到这一行时）就完成了。
这意味着 `parser.get_format_instructions()` 只会运行一次。等到真正处理用户请求（`invoke`）时，Prompt 里已经包含了完整的格式说明，不需要再动态计算或传递了。

---

## 2. 硬限制 (Hard Constraints) - Function Calling

使用 `with_structured_output`。

**原理**：
利用现代模型（OpenAI, DeepSeek, Claude 3）原生的 **Function Calling (Tool Use)** 能力。直接在底层 API 层面强制模型调用一个“输出函数”，参数必须符合 Schema。

**代码示例**：
```python
# 1. 定义结构化 LLM (直接绑定 Pydantic 模型)
structured_llm = llm.with_structured_output(UICommand)

# 2. 定义 Prompt (不需要 format_instructions 了！)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Extract the user's intent."),
    ("user", "{text}")
])

# 3. 构建链
chain = prompt | structured_llm
```

**特点**：
*   ✅ **极度稳定**：模型微调过，严格遵守 Schema，几乎不出错。
*   ✅ **省 Token**：不需要在 Prompt 里写格式说明。
*   ✅ **代码干净**：逻辑更自然。
*   ❌ **模型依赖**：必须使用支持 Function Calling 的模型。

---

## 总结

| 特性 | JsonOutputParser (软) | with_structured_output (硬) |
| :--- | :--- | :--- |
| **原理** | Prompt 提示词 | 底层 API (Function Calling) |
| **稳定性** | 中 (依赖模型指令遵循能力) | 高 (强制约束) |
| **Token 消耗** | 高 (Prompt 变长) | 低 |
| **适用模型** | 所有 LLM | OpenAI, DeepSeek, Claude 等现代模型 |
| **推荐场景** | 只有普通补全能力的模型 | **生产环境首选** (只要模型支持) |