# 会话历史功能使用说明

## 概述

本次更新添加了会话历史管理功能，允许用户：
1. 创建带有唯一 thread_id 的会话
2. 加载历史会话并继续对话
3. 可选择从特定检查点（checkpoint）回溯会话状态

## 后端 API 变更

### 1. 获取历史记录接口

**端点**: `GET /chat/{thread_id}/history`

**参数**:
- `thread_id` (路径参数): 会话的唯一标识符
- `checkpoint_id` (查询参数, 可选): 检查点 ID，用于获取特定时间点的历史

**响应示例**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you today?"
    }
  ]
}
```

### 2. 流式接口更新

**端点**: `POST /agent/stream`

**请求体新增字段**:
```json
{
  "messages": [...],
  "thread_id": "thread-123",  // 可选，默认为 "1"
  "checkpoint_id": "checkpoint-456"  // 可选，用于从特定检查点继续
}
```

## 前端使用方式

### 路由结构

- `/` - 自动重定向到新会话
- `/chat/{threadId}` - 会话页面，支持加载历史记录

### 新会话

访问根路径 `/` 会自动创建一个新的 thread ID 并重定向到 `/chat/{threadId}`

### 加载现有会话

直接访问 `/chat/{threadId}` 可以加载该会话的历史记录（如果存在）

### 示例代码

前端使用 Vercel AI SDK 的 `useChat` hook，自动在请求体中包含 `thread_id`:

```typescript
const { threadId } = useParams<{ threadId?: string }>();
const currentThreadId = threadId || "default";

const { messages, setMessages, sendMessage } = useChat({
  transport: new DefaultChatTransport({
    api: apiUrl,
    body: {
      thread_id: currentThreadId,  // 自动包含在每个请求中
    },
  }),
});

// 初始加载历史
useEffect(() => {
  const loadHistory = async () => {
    if (!threadId) return;
    const history = await getHistory(threadId);
    // 转换并设置消息
    setMessages(convertToUIMessages(history));
  };
  loadHistory();
}, [threadId]);
```

## 实现细节

### Agent 变更

`LLMAgent` 类新增：
- `get_history(thread_id, checkpoint_id)` 方法：获取会话历史
- `astream_messages()` 现在接受 `config` 参数，支持传入 thread_id 和 checkpoint_id

### 数据库持久化

使用 LangGraph 的 `AsyncPostgresSaver` 作为 checkpointer，自动保存每次对话的状态到 PostgreSQL 数据库。

## 测试

运行单元测试：
```bash
cd server
uv run pytest tests/test_history.py -v
```

## 注意事项

1. **Thread ID 格式**: 建议使用 `thread-{timestamp}` 或 UUID 格式
2. **向后兼容**: 如果不提供 thread_id，默认使用 "1"
3. **检查点**: checkpoint_id 是可选的，主要用于时间旅行功能（回溯到历史状态）
