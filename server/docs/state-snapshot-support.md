# StateSnapshot 支持文档

## 概述

`StreamToVercelConverter` 现在支持处理 `StateSnapshot` 对象，将其转换为 Vercel AI SDK 的 `data-checkpoint` 格式。

## 默认行为

默认情况下，`StateSnapshot` 会被转换为以下格式：

```python
{
    "type": "data-checkpoint",
    "transient": True,
    "checkpoint": {
        "id": "checkpoint-id-from-config",
        "parent": "parent-checkpoint-id-or-null"
    }
}
```

## 基本用法

```python
from app.vercel_ui_message_stream.converter import StreamToVercelConverter

async def my_stream():
    # 混合流：包含 AI 消息、工具消息和状态快照
    yield AIMessageChunk(id="msg-1", content="Processing...")
    
    # StateSnapshot 会自动转换为 data-checkpoint 事件
    yield StateSnapshot(
        values={},
        next=(),
        config={"configurable": {"checkpoint_id": "chk-123"}},
        metadata={},
        created_at="2024-01-01T00:00:00Z",
        parent_config=None,
        tasks=(),
        interrupts=(),
    )
    
    yield ToolMessage(content='{"result": "done"}', tool_call_id="call-1")

# 使用默认转换器
converter = StreamToVercelConverter()
async for event in converter.stream(my_stream()):
    print(event)
```

## 自定义转换器

你可以提供自定义的转换函数来控制 `StateSnapshot` 的输出格式：

```python
from langgraph.types import StateSnapshot
from app.vercel_ui_message_stream.converter import StreamToVercelConverter

def custom_checkpoint_converter(snapshot: StateSnapshot) -> dict:
    """自定义转换器：添加额外的元数据"""
    return {
        "type": "custom-checkpoint",
        "transient": True,
        "checkpoint": {
            "id": snapshot.config.get("configurable", {}).get("checkpoint_id"),
            "parent": (
                snapshot.parent_config.get("configurable", {}).get("checkpoint_id")
                if snapshot.parent_config else None
            ),
            "timestamp": snapshot.created_at,
            # 添加自定义字段
            "metadata": snapshot.metadata,
            "has_next": len(snapshot.next) > 0,
        }
    }

# 使用自定义转换器
converter = StreamToVercelConverter(
    checkpoint_converter=custom_checkpoint_converter
)

async for event in converter.stream(my_stream()):
    print(event)
```

## Step 生命周期

重要：`StateSnapshot` 不会影响 step 生命周期。它们被视为当前 step 的一部分，不会触发新的 `start-step` 或 `finish-step` 事件。

```python
# 流程示例：
# 1. start-step (from AI message)
# 2. text-start, text-delta, text-end (from AI message)
# 3. data-checkpoint (from StateSnapshot - NO step change)
# 4. tool-output-available (from Tool message - NO step change)
# 5. finish-step (end of stream)
```

## API 参考

### StreamToVercelConverter.__init__

```python
def __init__(
    self,
    checkpoint_converter: Callable[[StateSnapshot], dict[str, Any]] | None = None,
) -> None
```

**参数：**
- `checkpoint_converter`: 可选的自定义转换函数
  - 输入：`StateSnapshot` 对象
  - 输出：包含转换后事件数据的字典
  - 默认：使用 `_default_checkpoint_converter`

### 默认转换器

```python
@staticmethod
def _default_checkpoint_converter(snapshot: StateSnapshot) -> dict[str, Any]:
    """
    默认的 StateSnapshot 转换器
    
    从 snapshot.config["configurable"]["checkpoint_id"] 提取 checkpoint ID
    从 snapshot.parent_config["configurable"]["checkpoint_id"] 提取 parent ID
    
    如果没有 config，ID 将设置为 "unknown"
    如果没有 parent_config，parent 将设置为 None
    """
```

## 完整示例

参见 [test_state_snapshot.py](../tests/vercel_ui_message_stream/test_state_snapshot.py) 了解完整的使用示例和测试用例。
