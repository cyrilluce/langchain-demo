# Vercel UI Message Transform

将 LangChain BaseMessage 对象转换为 Vercel AI SDK UIMessage 格式的工具模块。

## 概述

这个模块实现了 Vercel AI SDK `convertToModelMessages` 函数的逆向转换，将 LangChain 的消息对象转换为前端可用的 UIMessage 格式。

## 核心功能

### `convert_to_ui_messages(messages: Sequence[BaseMessage]) -> List[Dict[str, Any]]`

主转换函数，将 LangChain 消息列表转换为 UIMessage 格式。

**转换规则：**

1. **System Message** → `role: "system"` 的 UIMessage
2. **HumanMessage** → `role: "user"` 的 UIMessage
3. **AIMessage** → `role: "assistant"` 的 UIMessage
4. **ToolMessage** → 合并到前置 assistant 消息的 `tool-result` part

**关键特性：**

- **消息合并**：多个连续的 assistant 消息会被合并为一条消息，内容作为 parts 数组
- **工具调用处理**：tool message 会被合并到对应的 assistant 消息中
- **多模态支持**：支持图片等文件类型的转换

## 使用示例

### 基础对话转换

```python
from langchain_core.messages import HumanMessage, AIMessage
from app.vercel_ui_message_transform import convert_to_ui_messages

messages = [
    HumanMessage(content="Hello!"),
    AIMessage(content="Hi there! How can I help?")
]

ui_messages = convert_to_ui_messages(messages)
# 结果可直接用于前端 Vercel AI SDK
```

### 带工具调用的转换

```python
from langchain_core.messages import AIMessage, ToolMessage

messages = [
    AIMessage(
        content="Let me check that.",
        tool_calls=[{
            "id": "call-1",
            "name": "get_weather",
            "args": {"city": "Tokyo"}
        }]
    ),
    ToolMessage(
        content='{"temperature": 22}',
        tool_call_id="call-1",
        name="get_weather"
    )
]

ui_messages = convert_to_ui_messages(messages)
# ToolMessage 会被合并到 AIMessage 的 parts 中
```

### 多模态消息转换

```python
from langchain_core.messages import HumanMessage

messages = [
    HumanMessage(content=[
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ])
]

ui_messages = convert_to_ui_messages(messages)
# 图片被转换为 file part
```

## UIMessage vs ModelMessage

**UIMessage**（前端格式）：

- 多个 assistant/tool 消息会被合并为一条
- 内容通过 `parts` 数组表示
- Tool 结果作为 `tool-result` 类型的 part

**ModelMessage**（后端/模型格式）：

- 每个消息独立
- Tool 消息单独成行
- 更接近 LLM API 的原始格式

## 完整示例

查看 `examples/transform_example.py` 获取更多使用示例。

## 测试

```bash
cd server
uv run pytest tests/vercel_ui_message_transform/test_transform.py -v
```

## 与其他模块的关系

- **vercel_ui_message_stream**: 处理流式消息的实时转换
- **vercel_ui_message_transform**: 处理历史消息的批量转换（本模块）

## 参考资料

- [Vercel AI SDK UIMessage 格式](https://ai-sdk.dev/docs/reference/ai-sdk-ui/ui-message)
- [Vercel AI SDK convertToModelMessages](https://github.com/vercel/ai/blob/main/packages/ai/src/ui/convert-to-model-messages.ts)
- [LangChain Messages](https://python.langchain.com/docs/concepts/messages/)
