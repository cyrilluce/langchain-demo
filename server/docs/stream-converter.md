# LangChain to Vercel AI SDK Stream Converter

## 概述

本实现提供了从 LangChain AIMessageChunk 流到 Vercel AI SDK UIMessageChunk 流的完整转换系统。

## 设计架构

### 核心组件

#### 1. ModelConverter (模型转换器)

负责转换 LangChain 模型/LLM 节点的输出：

- **reasoning** → `reasoning-start`, `reasoning-delta`, `reasoning-end`
- **text** → `text-start`, `text-delta`, `text-end`
- **tool_call_chunk** → `tool-input-start`, `tool-input-delta`, `tool-input-available`

#### 2. ToolsConverter (工具转换器)

负责转换 LangChain 工具执行节点的输出：

- **ToolMessage text** → `tool-output-start`, `tool-output-delta`, `tool-output-available`

#### 3. StreamConverter (流转换器)

主转换器，负责路由和协调：

- 根据消息类型路由到相应的转换器
- 管理消息级别的生命周期（start/finish）
- 处理流的开始和结束标记

## 关键特性

### 1. 状态管理

- **index 跟踪**: LangChain 使用 index 关联同一工具调用的多个 chunk
- **ID 生成**: 为每个 chunk 生成唯一的 ID
- **累积缓冲**: 维护中间状态用于最终的 available 事件

### 2. 协议兼容

遵循 Vercel AI SDK Data Stream Protocol:

- Server-Sent Events (SSE) 格式
- 标准的 start/delta/end 模式
- 正确的 JSON 序列化

### 3. 类型安全

- 使用 getattr 安全访问可选属性（如 reasoning）
- 支持 dict 和对象两种 tool_chunk 格式
- 适当的类型转换和错误处理

## 使用示例

### 基本流式转换

```python
from app.stream_converters import StreamConverter
from app.agent import agent

converter = StreamConverter()

async def stream_response(prompt: str):
    # 获取 LangChain 消息流
    message_stream = agent.astream_messages(prompt)
    
    # 转换为 Vercel AI SDK 格式
    async for event in converter.convert_stream(message_stream):
        yield event
```

### 在 FastAPI 中使用

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/agent/stream")
async def stream_endpoint(request: Request):
    # ... 提取 prompt ...
    
    converter = StreamConverter()
    
    async def event_stream():
        message_stream = agent.astream_messages(prompt)
        async for frame in converter.convert_stream(message_stream):
            yield frame
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"x-vercel-ai-ui-message-stream": "v1"},
    )
```

## 流事件格式

### 消息开始

```json
data: {"type": "start", "messageId": "msg_..."}
```

### 文本块

```json
data: {"type": "text-start", "id": "text_..."}
data: {"type": "text-delta", "id": "text_...", "delta": "Hello"}
data: {"type": "text-end", "id": "text_..."}
```

### 推理块 (reasoning)

```json
data: {"type": "reasoning-start", "id": "reasoning_..."}
data: {"type": "reasoning-delta", "id": "reasoning_...", "delta": "Let me think..."}
data: {"type": "reasoning-end", "id": "reasoning_..."}
```

### 工具调用输入

```json
data: {"type": "tool-input-start", "toolCallId": "call_...", "toolName": "get_weather"}
data: {"type": "tool-input-delta", "toolCallId": "call_...", "inputTextDelta": "{\"city\":"}
data: {"type": "tool-input-available", "toolCallId": "call_...", "input": {"city": "SF"}}
```

### 工具输出

```json
data: {"type": "tool-output-start", "toolCallId": "call_...", "id": "output_..."}
data: {"type": "tool-output-delta", "toolCallId": "call_...", "id": "output_...", "delta": "The weather"}
data: {"type": "tool-output-available", "toolCallId": "call_...", "output": "The weather is sunny"}
```

### 消息完成

```json
data: {"type": "finish"}
data: [DONE]
```

## 测试

完整的单元测试位于 `tests/test_stream_converters.py`，覆盖：

- 文本流转换
- 推理内容转换
- 工具调用 chunk 转换
- 工具输出转换
- 完整流程集成测试
- 边界情况和错误处理

运行测试：

```bash
cd server
pytest tests/test_stream_converters.py -v
```

## 注意事项

### 1. LangChain chunk 累积

LangChain 的 AIMessageChunk 可以通过 `+` 操作累积：

```python
full = chunk1 + chunk2 + chunk3
```

我们的转换器维护状态以正确处理这种累积行为。

### 2. chunk_position 标记

LangChain 1.1.3+ 提供 `chunk_position='last'` 标记最后一个 chunk，用于触发 finalize。

### 3. 工具调用的 index

LangChain 使用 index 字段关联同一工具调用的多个 chunk。我们的转换器跟踪这些索引以生成一致的 toolCallId。

### 4. JSON 解析

工具参数可能以部分 JSON 字符串流式传输。我们累积这些片段并在 finalize 时解析完整的 JSON。

### 5. ToolMessage 内容类型

LangChain 的 ToolMessage 自动将 dict 内容转换为字符串。我们的转换器尝试解析这些字符串回 JSON。

## 扩展性

### 添加新的转换器

设计支持未来添加其他节点类型的转换器：

```python
class CustomNodeConverter(BaseConverter):
    async def convert(self, chunk):
        # 实现自定义转换逻辑
        pass
```

### 组合不同的 LangGraph 结构

可以组合不同的转换器来处理复杂的 LangGraph 图结构：

```python
converter = StreamConverter()
converter.add_custom_converter('custom_node', CustomNodeConverter())
```

## 参考文档

- [LangChain Streaming](https://docs.langchain.com/oss/python/langchain/streaming)
- [Vercel AI SDK Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
