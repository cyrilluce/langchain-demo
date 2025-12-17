import json
from typing import Literal, Optional, Any, Union
from pydantic import BaseModel, TypeAdapter, field_validator
from enum import Enum


# 假设的 providerMetadataSchema
class ProviderMetadata(BaseModel):
    # 根据你的实际 providerMetadataSchema 定义
    pass


# FinishReason 枚举（对应 Zod 的 as const enum）
class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content-filter"
    TOOL_CALLS = "tool-calls"
    ERROR = "error"
    OTHER = "other"
    UNKNOWN = "unknown"

    # 文本相关事件


class TextStart(BaseModel):
    type: Literal["text-start"] = "text-start"
    id: str
    providerMetadata: Optional[ProviderMetadata] = None


class TextDelta(BaseModel):
    type: Literal["text-delta"] = "text-delta"
    id: str
    delta: str
    providerMetadata: Optional[ProviderMetadata] = None


class TextEnd(BaseModel):
    type: Literal["text-end"] = "text-end"
    id: str
    providerMetadata: Optional[ProviderMetadata] = None


# 错误事件
class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    errorText: str


# 工具输入相关事件
class ToolInputStart(BaseModel):
    type: Literal["tool-input-start"] = "tool-input-start"
    toolCallId: str
    toolName: str
    providerExecuted: Optional[bool] = None
    dynamic: Optional[bool] = None
    title: Optional[str] = None


class ToolInputDelta(BaseModel):
    type: Literal["tool-input-delta"] = "tool-input-delta"
    toolCallId: str
    inputTextDelta: str


class ToolInputAvailable(BaseModel):
    type: Literal["tool-input-available"] = "tool-input-available"
    toolCallId: str
    toolName: str
    input: Any
    providerExecuted: Optional[bool] = None
    providerMetadata: Optional[ProviderMetadata] = None
    dynamic: Optional[bool] = None
    title: Optional[str] = None


class ToolInputError(BaseModel):
    type: Literal["tool-input-error"] = "tool-input-error"
    toolCallId: str
    toolName: str
    input: Any
    providerExecuted: Optional[bool] = None
    providerMetadata: Optional[ProviderMetadata] = None
    dynamic: Optional[bool] = None
    errorText: str
    title: Optional[str] = None


class ToolApprovalRequest(BaseModel):
    type: Literal["tool-approval-request"] = "tool-approval-request"
    approvalId: str
    toolCallId: str


# 工具输出相关事件
class ToolOutputAvailable(BaseModel):
    type: Literal["tool-output-available"] = "tool-output-available"
    toolCallId: str
    output: Any
    providerExecuted: Optional[bool] = None
    dynamic: Optional[bool] = None
    preliminary: Optional[bool] = None


class ToolOutputError(BaseModel):
    type: Literal["tool-output-error"] = "tool-output-error"
    toolCallId: str
    errorText: str
    providerExecuted: Optional[bool] = None
    dynamic: Optional[bool] = None


class ToolOutputDenied(BaseModel):
    type: Literal["tool-output-denied"] = "tool-output-denied"
    toolCallId: str


# 推理相关事件
class ReasoningStart(BaseModel):
    type: Literal["reasoning-start"] = "reasoning-start"
    id: str
    providerMetadata: Optional[ProviderMetadata] = None


class ReasoningDelta(BaseModel):
    type: Literal["reasoning-delta"] = "reasoning-delta"
    id: str
    delta: str
    providerMetadata: Optional[ProviderMetadata] = None


class ReasoningEnd(BaseModel):
    type: Literal["reasoning-end"] = "reasoning-end"
    id: str
    providerMetadata: Optional[ProviderMetadata] = None


# 数据源相关事件
class SourceUrl(BaseModel):
    type: Literal["source-url"] = "source-url"
    sourceId: str
    url: str
    title: Optional[str] = None
    providerMetadata: Optional[ProviderMetadata] = None


class SourceDocument(BaseModel):
    type: Literal["source-document"] = "source-document"
    sourceId: str
    mediaType: str
    title: str
    filename: Optional[str] = None
    providerMetadata: Optional[ProviderMetadata] = None


class FileEvent(BaseModel):
    type: Literal["file"] = "file"
    url: str
    mediaType: str
    providerMetadata: Optional[ProviderMetadata] = None


# 自定义 data-* 事件
class DataCustomEvent(BaseModel):
    id: Optional[str] = None
    data: Any
    transient: Optional[bool] = None

    type: str

    @field_validator("type", mode="before")
    @classmethod
    def validate_type_prefix(cls, v: str) -> str:
        if not isinstance(v, str) or not v.startswith("data-"):
            raise ValueError('Type must start with "data-"')
        return v


# 步骤控制事件
class StartStep(BaseModel):
    type: Literal["start-step"] = "start-step"


class FinishStep(BaseModel):
    type: Literal["finish-step"] = "finish-step"


# 消息生命周期事件
class StartEvent(BaseModel):
    type: Literal["start"] = "start"
    messageId: Optional[str] = None
    messageMetadata: Optional[Any] = None


class FinishEvent(BaseModel):
    type: Literal["finish"] = "finish"
    finishReason: Optional[FinishReason] = None
    messageMetadata: Optional[Any] = None


class AbortEvent(BaseModel):
    type: Literal["abort"] = "abort"


class MessageMetadataEvent(BaseModel):
    type: Literal["message-metadata"] = "message-metadata"
    messageMetadata: Any


# 定义完整的联合类型
Event = Union[
    TextStart,
    TextDelta,
    TextEnd,
    ErrorEvent,
    ToolInputStart,
    ToolInputDelta,
    ToolInputAvailable,
    ToolInputError,
    ToolApprovalRequest,
    ToolOutputAvailable,
    ToolOutputError,
    ToolOutputDenied,
    ReasoningStart,
    ReasoningDelta,
    ReasoningEnd,
    SourceUrl,
    SourceDocument,
    FileEvent,
    DataCustomEvent,  # 注意：需要特殊处理 type 字段
    StartStep,
    FinishStep,
    StartEvent,
    FinishEvent,
    AbortEvent,
    MessageMetadataEvent,
]

# 创建验证器
event_validator = TypeAdapter(Event)


def validateVercelUIMessageChunk(message: dict[str, Any]) -> None:
    try:
        event_validator.validate_python(message, strict=True, extra="forbid")
    except Exception as e:
        print(
            f"UIMessageChunk不合法: {json.dumps(message, indent=2, ensure_ascii=False)}"
        )
        raise e
