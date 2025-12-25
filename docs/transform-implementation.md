# LangChain AIMessage 到 Vercel AI SDK UIMessage 转换实现总结

## 实现概述

实现了将 LangChain BaseMessage 对象转换为 Vercel AI SDK UIMessage 格式的完整功能，这是 Vercel AI SDK `convertToModelMessages` 的逆向转换。

## 实现的文件

### 核心模块

1. **[transform.py](../server/app/vercel_ui_message_transform/transform.py)**
   - 主转换函数 `convert_to_ui_messages`
   - 辅助函数：
     - `_convert_user_message` - 转换用户消息
     - `_convert_assistant_block` - 转换 assistant 消息块
     - `_convert_tool_message_to_part` - 转换工具消息为 part

2. **[__init__.py](../server/app/vercel_ui_message_transform/__init__.py)**
   - 模块导出配置

### 测试文件

3. **[test_transform.py](../server/tests/vercel_ui_message_transform/test_transform.py)**
   - 19 个完整的单元测试
   - 覆盖所有转换场景
   - 测试类：
     - `TestConvertToUIMessages` - 主函数测试
     - `TestConvertUserMessage` - 用户消息转换
     - `TestConvertAssistantBlock` - Assistant 消息块转换
     - `TestConvertToolMessageToPart` - 工具消息转换

### 文档和示例

4. **[README.md](../server/app/vercel_ui_message_transform/README.md)**
   - 完整的使用文档
   - API 参考
   - 转换规则说明

5. **[transform_example.py](../server/examples/transform_example.py)**
   - 4 个实际使用示例
   - 演示基础对话、工具调用、多模态消息、消息合并

## 核心转换逻辑

### 1. 消息类型映射

| LangChain Message | UIMessage Role | 处理方式 |
|-------------------|----------------|----------|
| SystemMessage | `system` | 简单文本 part |
| HumanMessage | `user` | 支持多模态 parts |
| AIMessage | `assistant` | 支持工具调用和多个 parts |
| ToolMessage | `assistant` | 合并到前置 assistant 消息 |

### 2. 关键特性

#### 消息合并
多个连续的 assistant 消息会被合并为一条 UIMessage，内容作为 parts 数组：

```python
# 输入
[
    AIMessage("First"),
    AIMessage("Second"),
    AIMessage("Third")
]

# 输出
{
    "role": "assistant",
    "parts": [
        {"type": "text", "text": "First"},
        {"type": "text", "text": "Second"},
        {"type": "text", "text": "Third"}
    ]
}
```

#### 工具消息合并
ToolMessage 会被合并到前置的 AIMessage 中：

```python
# 输入
[
    AIMessage(tool_calls=[{"id": "1", "name": "weather", "args": {}}]),
    ToolMessage(content="sunny", tool_call_id="1", name="weather")
]

# 输出
{
    "role": "assistant",
    "parts": [
        {"type": "tool-weather", "toolCallId": "1", ...},
        {"type": "tool-weather", "toolCallId": "1", "output": "sunny", ...}
    ]
}
```

#### 多模态支持
HumanMessage 可以包含文本和图片：

```python
# 输入
HumanMessage(content=[
    {"type": "text", "text": "What's this?"},
    {"type": "image_url", "image_url": {"url": "..."}}
])

# 输出
{
    "role": "user",
    "parts": [
        {"type": "text", "text": "What's this?"},
        {"type": "file", "mediaType": "image/*", "url": "..."}
    ]
}
```

## 测试覆盖

### 测试场景

✅ 简单 system/user/assistant 消息  
✅ 完整对话序列  
✅ 带工具调用的 assistant 消息  
✅ 工具消息合并  
✅ 多个连续 assistant 消息合并  
✅ 孤立的工具消息处理  
✅ 空消息列表  
✅ 多模态用户消息  
✅ 空内容处理  
✅ 列表内容转换  

### 测试结果

```bash
19 passed in 0.05s
```

所有测试 100% 通过 ✅

## 代码质量

### Python 类型检查
- ✅ 使用 Pylance 严格类型检查
- ✅ 所有公共函数都有完整的类型注解
- ✅ 使用 `Sequence[BaseMessage]` 支持协变类型

### 代码风格
- ✅ 通过 ruff 代码检查
- ✅ 符合 PEP 8 规范
- ✅ 行长度不超过 88 字符

### 文档
- ✅ 完整的 docstring
- ✅ 使用示例
- ✅ README 文档

## 使用方式

### 在 API 端点中使用

```python
from app.vercel_ui_message_transform import convert_to_ui_messages
from langchain_core.messages import BaseMessage

@app.get("/chat/{thread_id}/history")
async def get_chat_history(thread_id: str):
    # 从 LangChain 获取消息历史
    messages: List[BaseMessage] = get_langchain_history(thread_id)
    
    # 转换为 UIMessage 格式
    ui_messages = convert_to_ui_messages(messages)
    
    return {"messages": ui_messages}
```

### 与现有模块的关系

```
vercel_ui_message_stream/      # 实时流式转换（已存在）
  ├── converter.py
  ├── model_converter.py
  └── tool_converter.py

vercel_ui_message_transform/   # 历史消息批量转换（新实现）
  ├── transform.py            ← 核心转换逻辑
  ├── __init__.py
  └── README.md
```

两个模块互补：
- `stream` 用于实时流式输出
- `transform` 用于历史消息批量转换

## 参考资源

- **Vercel AI SDK 源码**：https://github.com/vercel/ai/blob/main/packages/ai/src/ui/convert-to-model-messages.ts
- **LangChain Messages**：https://python.langchain.com/docs/concepts/messages/
- **项目文档**：[docs/session-history-feature.md](../docs/session-history-feature.md)

## 下一步

这个模块可以用于：

1. **历史消息查询** - `/chat/{thread_id}/history` 端点
2. **消息导出** - 导出对话记录给前端
3. **对话恢复** - 从 checkpoint 恢复对话状态

已经为会话历史功能的完整实现打下了基础！🎉
