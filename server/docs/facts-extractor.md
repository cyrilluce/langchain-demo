# Facts Extractor Agent

基于 LangChain `create_agent` 的 LLM 代理，用于从文本中提取与主题相关的原子化事实。

## 功能特点

- 使用 LangChain 框架构建
- 集成阿里云 Dashscope/Qwen 模型
- 提取与指定主题相关的原子化事实
- 为每个事实提供原文引用（字符偏移和长度）
- 完整的类型安全和错误处理
- 包含完整的单元测试

## API 端点

### POST /facts/extract

提取与主题相关的原子化事实。

**请求体：**

```json
{
  "content": "2024年全国机场信息汇总如下...机场名 | 客流 ... 武汉天河机场 | 3000万",
  "topic": "湖北机场吞吐量"
}
```

**响应：**

```json
{
  "facts": [
    {
      "fact": "武汉天河机场2024年的客流吞吐量为3000万",
      "references": [
        {
          "offset": 31,
          "length": 14
        }
      ]
    }
  ]
}
```

## 使用示例

### Python 代码

```python
from app.agents.facts_extractor import FactsExtractorAgent

# 初始化代理
agent = FactsExtractorAgent()

# 提取事实
content = """2024年全国机场信息汇总如下：
机场名 | 客流量
武汉天河机场 | 3000万
湖北花湖机场 | 500万"""

facts = await agent.extract_facts(
    content=content,
    topic="湖北机场吞吐量"
)

for fact in facts:
    print(f"事实: {fact.fact}")
    for ref in fact.references:
        text = content[ref.offset:ref.offset + ref.length]
        print(f"  引用: {text} (位置: {ref.offset}, 长度: {ref.length})")
```

### cURL 请求

```bash
curl -X POST http://localhost:8000/facts/extract \
  -H "Content-Type: application/json" \
  -d '{
    "content": "2024年全国机场信息汇总...武汉天河机场 | 3000万",
    "topic": "湖北机场吞吐量"
  }'
```

## 数据模型

### FactReference

```python
class FactReference(BaseModel):
    offset: int  # 引用在原文中的起始位置（从0开始）
    length: int  # 引用的字符长度
```

### ExtractedFact

```python
class ExtractedFact(BaseModel):
    fact: str              # 提取的事实文本
    references: List[FactReference]  # 原文引用列表
```

### FactsExtractionRequest

```python
class FactsExtractionRequest(BaseModel):
    content: str  # 原文（最长50000字符）
    topic: str    # 要查找的主题（最长500字符）
```

### FactsExtractionResponse

```python
class FactsExtractionResponse(BaseModel):
    facts: List[ExtractedFact]  # 提取的事实列表
```

## 错误处理

- 如果未配置 `DASHSCOPE_API_KEY`，初始化时会抛出 `ValueError`
- 如果 LLM 服务失败，API 返回 HTTP 503
- 其他错误返回 HTTP 500

## 测试

运行单元测试：

```bash
cd server
uv run pytest tests/test_facts_extractor.py -v
```

测试覆盖：
- ✅ 基本事实提取
- ✅ 多个事实提取
- ✅ 空内容/空主题处理
- ✅ 无效 JSON 响应处理
- ✅ 引用边界验证
- ✅ LLM 错误处理
- ✅ 多个引用支持
- ✅ 未配置 API key 处理
- ✅ 带额外文本的响应解析
- ✅ 负数偏移量处理

## 实现细节

### 核心组件

1. **FactsExtractorAgent**: 主要代理类
   - 使用 LangChain 的 `create_agent` 创建
   - 集成阿里云 ChatTongyi 模型
   - 包含精心设计的 system prompt

2. **引用验证**
   - 自动修正超出边界的长度
   - 过滤无效的负数偏移
   - 支持多个引用位置

3. **响应解析**
   - 智能提取 JSON（即使 LLM 返回额外文本）
   - 健壮的错误处理
   - 完整的数据验证

## 注意事项

- 需要设置环境变量 `DASHSCOPE_API_KEY`
- `offset` 是基于字符的索引（0-indexed），不是字节
- 中文字符的 offset 和 length 计算基于字符数，不是字节数
- API 限制：content 最长 50000 字符，topic 最长 500 字符
