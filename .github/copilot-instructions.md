# langchain-demo 的 Copilot 指引

## 架构概览

这是一个 **monorepo**，包含两个通过 HTTP 通信的独立服务：

- **server/**: Python FastAPI 后端，集成 LangChain 进行 LLM 编排（阿里云 Dashscope/Qwen 模型）
- **ui/**: React TypeScript 前端，使用 Vite + Bun 运行时 + Vercel AI SDK 进行流式传输

**关键架构决策**：当 `DASHSCOPE_API_KEY` 未配置时，服务器以 **回退模式** 运行，返回回显响应而不是失败。这使得无需 LLM 凭证即可进行开发。

## 项目结构和关键文件

```
server/
  app/
    main.py         # FastAPI 路由: /agent (非流式), /agent/stream (流式), /health
    agent.py        # LLMAgent 类 - 使用 LangChain
    config.py       # 环境配置，通过 python-dotenv 支持 .env
    models.py       # Pydantic 请求/响应模式
  pyproject.toml    # 使用 `uv` 包管理器 (不是 pip)
  dev.sh           # 快速启动脚本: ./dev.sh

ui/
  src/
    App.tsx         # 主组件 - 使用 @ai-sdk/react useChat hook
    services/api.ts # 非流式端点的 HTTP 客户端
  package.json      # Bun 作为包管理器和运行时

```

## 关键开发工作流

### 单元测试
server 每次开发必须新增或更新至少一个针对当前变更的单元测试，放置于 `./server/tests` 目录下，并保证

### 服务器开发
```bash
cd server
# 安装依赖
uv sync

# 快速启动
./dev.sh  # 在 :8000 端口运行带热重载的 uvicorn

# 可选: 设置 LLM 凭证
export DASHSCOPE_API_KEY="sk-..."
export DASHSCOPE_MODEL="qwen-turbo"  # 或 qwen-plus, qwen-max
```

### UI 开发
```bash
cd ui
bun install  # 不是 npm/yarn - 使用 Bun
bun run dev  # Vite 开发服务器在 :5173 端口

# 环境配置
# 创建 .env.local: VITE_API_BASE_URL=http://localhost:8000
```

### 测试
- **服务器**: `cd server && pytest tests/ -v`
- **UI**: `cd ui && bun test`

## API 契约模式

### 非流式端点 (`POST /agent`)
```python
# 请求: PromptRequest
{"prompt": "用户问题"}

# 响应: AgentResponse (200)
{"answer": "生成的响应"}

# 错误: ErrorResponse (503)
{"error": "LLM service temporarily unavailable", "code": "LLM_UNAVAILABLE"}
```

### 流式端点 (`POST /agent/stream`)
- **输入格式**: Vercel AI SDK `UIMessage` 格式，包含 `messages` 数组
- **提取**: 从 `parts[].text` 提取最后一条用户消息，或回退到 `content`
- **输出**: 与 `@ai-sdk/react` `useChat` hook 兼容的 Server-Sent Events 流
- **格式**: `0:"文本块"\n` (Vercel AI SDK 流式协议)

## 项目特定约定

### 错误处理
- **始终返回 HTTP 503**（不是 500）用于 LLM 失败 - 客户端期望这个特定代码
- **永远不要在 agent 代码中抛出未处理的异常** - 用 try/except 包装并抛出 `Exception(f"LLM service error: {str(e)}")`
- FastAPI 处理器捕获并转换为 503，带结构化错误 JSON

### 类型安全
- **Python**: 要保证没有 python 语法错误
- **TypeScript**: 启用严格模式，所有属性必须类型化

## 外部依赖

- **阿里云 Dashscope**: 需要 `DASHSCOPE_API_KEY` 环境变量，模型名称: `qwen-turbo`, `qwen-plus`, `qwen-max`
- **包管理器**: Python 使用 `uv` (不直接使用 pip)，UI 使用 `bun` (不是 npm/yarn)
- **LangChain 版本**: `langchain>=1.1.3`, `langchain-community>=0.4.1` (在 pyproject.toml 中指定)

## CORS 配置
- **本地开发的宽松配置**: `main.py` 中的 `allow_origins=["*"]`
- 使任何端口的 UI 都能调用后端 - 对 Vite HMR 至关重要

## 流式实现说明

服务端(langchain) <-> 服务端(UIMessageStream) <-> 客户端：前后端交互统一使用 Vercel AI SDK `UIMessage` 格式

UI 使用 `@ai-sdk/react` 的 `useChat` hook，它处理：
- 消息状态管理
- 自动流式连接
- 通过 `status` 和 `error` 属性管理加载/错误状态
