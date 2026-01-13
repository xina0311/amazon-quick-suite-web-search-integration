# Design Document: Zhipu Web Search Provider

## Overview

本设计文档描述智谱 (Zhipu) Web Search Provider 的技术实现方案。该 Provider 将智谱的 Web Search API 集成到 Amazon Quick Suite AI Search Integration 项目中，通过 AWS Lambda 和 AgentCore Gateway 提供搜索服务。

智谱 Web Search 是专为大模型设计的搜索引擎，具有以下特点：
- 增强的意图识别能力
- 多种搜索引擎选择（基础版、高级版、搜狗、夸克）
- 时间范围和域名过滤
- 结构化的搜索结果输出

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Quick Suite    │────▶│  AgentCore       │────▶│  Zhipu Lambda   │
│  (Chat Agent)   │     │  Gateway         │     │  Function       │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Zhipu API      │
                                                 │  (bigmodel.cn)  │
                                                 └─────────────────┘
```

### 组件说明

1. **Quick Suite**: 用户交互界面，发起搜索请求
2. **AgentCore Gateway**: 路由请求到对应的 Target，处理认证
3. **Zhipu Lambda Function**: 处理搜索请求，调用智谱 API，格式化结果
4. **Zhipu API**: 智谱开放平台的 Web Search API

## Components and Interfaces

### Lambda 函数结构

```
providers/zhipu/
├── zhipu_lambda_function.py   # 主函数文件
├── deploy.sh                   # 部署脚本
├── add_target.py              # Gateway Target 配置
├── test_lambda.sh             # Lambda 测试脚本
├── test_target.sh             # 端到端测试脚本
└── README.md                  # 文档
```

### Lambda Handler 接口

```python
def lambda_handler(event: dict, context) -> dict:
    """
    Lambda 函数入口
    
    Args:
        event: Gateway 传递的参数
            - query (str, required): 搜索关键词
            - max_results (int, optional): 结果数量，1-50，默认10
            - search_engine (str, optional): 搜索引擎类型，默认 search_std
            - recency_filter (str, optional): 时间过滤，默认 noLimit
            - domain_filter (str, optional): 域名过滤
            - content_size (str, optional): 摘要长度，默认 medium
        context: Lambda 上下文
        
    Returns:
        dict: MCP 格式响应
            - statusCode (int): HTTP 状态码
            - body (str): JSON 格式的响应体
    """
```

### API 调用接口

```python
def call_zhipu_api(
    query: str,
    count: int = 10,
    search_engine: str = 'search_std',
    recency_filter: str = 'noLimit',
    domain_filter: str = None,
    content_size: str = 'medium'
) -> dict:
    """
    调用智谱 Web Search API
    
    Endpoint: POST https://open.bigmodel.cn/api/paas/v4/web_search
    
    Request Body:
        {
            "search_query": str,
            "search_engine": str,
            "count": int,
            "search_recency_filter": str,
            "search_domain_filter": str (optional),
            "content_size": str
        }
    
    Returns:
        dict: API 响应
            - id: 任务 ID
            - created: 创建时间戳
            - search_intent: 搜索意图（可选）
            - search_result: 搜索结果列表
    """
```

### 结果格式化接口

```python
def format_results(api_response: dict) -> str:
    """
    将 API 响应格式化为 Markdown
    
    Args:
        api_response: 智谱 API 响应
        
    Returns:
        str: Markdown 格式的搜索结果
    """
```

## Data Models

### 输入参数模型

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索关键词 |
| max_results | integer | 否 | 10 | 结果数量 (1-50) |
| search_engine | string | 否 | search_std | 搜索引擎类型 |
| recency_filter | string | 否 | noLimit | 时间范围过滤 |
| domain_filter | string | 否 | null | 域名白名单 |
| content_size | string | 否 | medium | 摘要长度 |

### 搜索引擎类型

| 值 | 说明 | 价格 |
|----|------|------|
| search_std | 基础版（智谱自研） | 0.01元/次 |
| search_pro | 高级版（智谱自研） | 0.03元/次 |
| search_pro_sogou | 搜狗版 | 0.05元/次 |
| search_pro_quark | 夸克版 | 0.05元/次 |

### 时间范围过滤

| 值 | 说明 |
|----|------|
| oneDay | 一天内 |
| oneWeek | 一周内 |
| oneMonth | 一个月内 |
| oneYear | 一年内 |
| noLimit | 不限制 |

### 摘要长度

| 值 | 说明 |
|----|------|
| low | 简短摘要 |
| medium | 中等长度（默认） |
| high | 详细摘要 |

### API 响应模型

```json
{
    "id": "string",
    "created": 1234567890,
    "search_intent": [
        {
            "query": "原始查询",
            "intent": "SEARCH_ALL",
            "keywords": "重写后的关键词"
        }
    ],
    "search_result": [
        {
            "title": "网页标题",
            "content": "内容摘要",
            "link": "https://example.com",
            "media": "网站名称",
            "icon": "https://example.com/favicon.ico",
            "refer": "1",
            "publish_date": "2025-01-01"
        }
    ]
}
```

### MCP 响应格式

```json
{
    "statusCode": 200,
    "body": "{\"content\": [{\"type\": \"text\", \"text\": \"# 智谱 Web Search 结果\\n\\n...\"}]}"
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Valid query triggers API call

*For any* non-empty query string, when passed to the Lambda handler, the handler SHALL attempt to call the Zhipu API and return a response (either success or API error).

**Validates: Requirements 2.1**

### Property 2: Empty query rejection

*For any* empty or whitespace-only query string, the Lambda handler SHALL return an error response with status code 400 and the original query list SHALL remain unchanged.

**Validates: Requirements 2.2**

### Property 3: Invalid parameter fallback to defaults

*For any* combination of invalid parameter values (max_results outside 1-50, invalid search_engine, invalid recency_filter, invalid content_size), the Lambda handler SHALL use the corresponding default values (10, search_std, noLimit, medium) when constructing the API request.

**Validates: Requirements 2.4, 2.5, 2.6, 2.7**

### Property 4: Result formatting completeness

*For any* valid API response containing search results, the formatted Markdown output SHALL:
- Be valid Markdown text
- Include all result fields (title, link, content, media) for each result
- Display the correct total count of results
- Follow MCP-compatible format with content array containing text type

**Validates: Requirements 4.1, 4.2, 4.5, 4.6**

### Property 5: Empty results handling

*For any* API response with empty search_result array, the formatted output SHALL contain the message "未找到相关结果".

**Validates: Requirements 4.4**

## Error Handling

### Error Categories

| 错误类型 | 状态码 | 处理方式 |
|---------|--------|---------|
| 缺少 query 参数 | 400 | 返回参数错误信息 |
| API Key 无效 | 401 | 返回认证错误信息 |
| API 请求超时 | 500 | 返回超时错误信息 |
| API 返回错误 | 500 | 返回原始错误信息 |
| 内部异常 | 500 | 返回通用错误信息 |

### 错误响应格式

```json
{
    "statusCode": 500,
    "body": "{\"error\": \"错误信息\", \"provider\": \"zhipu\"}"
}
```

### 异常处理流程

```python
try:
    # 1. 参数验证
    if not query:
        return error_response(400, 'Query parameter is required')
    
    # 2. 调用 API
    result = call_zhipu_api(...)
    
    # 3. 格式化结果
    formatted = format_results(result)
    
    return success_response(formatted)
    
except requests.exceptions.Timeout:
    return error_response(500, 'Search request timeout')
    
except requests.exceptions.RequestException as e:
    return error_response(500, f'API request failed: {str(e)}')
    
except Exception as e:
    return error_response(500, f'Internal error: {str(e)}')
```

## Testing Strategy

### 测试类型

本项目采用双重测试策略：

1. **单元测试 (Unit Tests)**: 验证特定示例和边界情况
2. **属性测试 (Property-Based Tests)**: 验证通用属性在所有输入上成立

### 单元测试

使用 pytest 框架，测试以下场景：

- API Key 环境变量读取
- 空查询参数处理
- API 错误响应处理
- 超时处理
- 结果格式化（包含 search_intent）

### 属性测试

使用 hypothesis 库，每个属性测试运行至少 100 次迭代。

测试标注格式：
```python
# Feature: zhipu-web-search, Property 1: Valid query triggers API call
# Validates: Requirements 2.1
```

### 测试文件结构

```
providers/zhipu/
├── tests/
│   ├── __init__.py
│   ├── test_lambda_handler.py      # 单元测试
│   ├── test_properties.py          # 属性测试
│   └── conftest.py                 # 测试配置和 fixtures
```

### Mock 策略

- 使用 `unittest.mock` 模拟 API 调用
- 使用 `responses` 库模拟 HTTP 响应
- 不依赖真实 API 进行自动化测试

## Implementation Notes

### 与现有 Provider 的一致性

- 遵循 `templates/lambda_function_template.py` 的结构
- 使用相同的 MCP 响应格式
- 使用相同的错误处理模式
- 使用相同的部署脚本结构

### 智谱 API 特殊处理

1. **参数名称映射**:
   - `query` → `search_query`
   - `max_results` → `count`
   - `recency_filter` → `search_recency_filter`
   - `domain_filter` → `search_domain_filter`

2. **搜索引擎编码**:
   - 使用下划线格式：`search_std`, `search_pro`
   - 不是连字符格式

3. **响应处理**:
   - 处理 `search_intent` 字段（可选）
   - 处理 `icon` 字段（可选）

### 安全考虑

- API Key 通过环境变量传递，不硬编码
- 生产环境建议使用 AWS Secrets Manager
- 日志中不输出完整 API Key
