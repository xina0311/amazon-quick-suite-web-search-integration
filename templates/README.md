# 🎨 Templates - 通用 Provider 添加模板

本目录包含用于添加新 AI Search Provider 的通用模板。

## 📁 模板文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `lambda_function_template.py` | Lambda 函数模板 | 完整的 Lambda 函数代码框架 |
| `add_new_provider.sh` | 部署脚本 | 自动添加 Gateway Target |
| `README.md` | 使用说明 | 本文件 |

---

## 🚀 快速开始 - 添加新 Provider

### 示例：添加秘塔搜索 (Metaso)

#### 步骤 1: 创建 Lambda 函数

```bash
# 1. 复制模板
cp templates/lambda_function_template.py metaso_lambda_function.py

# 2. 编辑文件，修改配置
nano metaso_lambda_function.py
```

修改以下部分：

```python
# 配置
PROVIDER_NAME = "metaso"
API_KEY = "your-metaso-api-key"
API_ENDPOINT = "https://api.metaso.cn/v1/search"  # 实际 API 地址

# 实现 call_provider_api 函数
def call_provider_api(query, count, search_type='web', language='zh'):
    headers = {
        'X-API-Key': API_KEY,  # 根据实际认证方式修改
        'Content-Type': 'application/json'
    }
    
    payload = {
        'query': query,
        'limit': count,  # 秘塔使用 'limit'
        'type': search_type
    }
    
    response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

# 实现 format_results 函数
def format_results(api_response):
    # 根据秘塔的响应格式进行解析
    results = api_response.get('results', [])
    
    formatted = "# 秘塔搜索结果\n\n"
    for idx, item in enumerate(results, 1):
        formatted += f"## {idx}. {item['title']}\n"
        formatted += f"**链接:** {item['url']}\n"
        formatted += f"**摘要:** {item['snippet']}\n\n"
    
    return formatted
```

#### 步骤 2: 部署 Lambda

```bash
# 创建部署包
mkdir -p metaso_deployment
cd metaso_deployment
cp ../metaso_lambda_function.py .
pip install requests -t .
zip -r ../metaso_lambda.zip .
cd ..

# 部署（使用现有的 IAM 角色）
aws lambda create-function \
  --function-name MetasoWebSearchFunction \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/BochaLambdaExecutionRole \
  --handler metaso_lambda_function.lambda_handler \
  --zip-file fileb://metaso_lambda.zip \
  --timeout 30 \
  --region us-east-1
```

#### 步骤 3: 添加到 Gateway

```bash
# 使用通用脚本添加
chmod +x templates/add_new_provider.sh
./templates/add_new_provider.sh metaso arn:aws:lambda:us-east-1:XXX:function:MetasoWebSearchFunction
```

#### 步骤 4: 测试

```bash
# Quick Suite 会自动发现新工具
# 在 Chat Agent 中测试：
# "使用秘塔搜索查找关于 AI Agent 的学术论文"
```

---

## 📋 支持的 Provider 示例

### 1. 博查 (Bocha AI) ✅ 已实现

- **API**: `https://api.bochaai.com/v1/web-search`
- **认证**: Bearer Token
- **特点**: 网页搜索、新闻、详细摘要

### 2. 秘塔 (Metaso) 📝 模板可用

- **API**: `https://api.metaso.cn/search`（示例）
- **认证**: API Key
- **特点**: 学术搜索、图片搜索

**Lambda 实现要点**：
```python
# 请求格式
{
    "query": "搜索词",
    "limit": 10,
    "type": "academic"  # 或 "web", "image"
}

# 响应格式（预期）
{
    "results": [
        {
            "title": "标题",
            "url": "链接",
            "snippet": "摘要",
            "source": "来源",
            "date": "发布日期"
        }
    ]
}
```

### 3. Cloudsway (云途) 📝 模板可用

- **API**: `https://api.cloudsway.ai/search`（示例）
- **认证**: Custom Token
- **特点**: 企业搜索、知识库

**Lambda 实现要点**：
```python
# 请求格式
{
    "query": "搜索词",
    "count": 10,
    "domain": "enterprise"
}

# 响应格式（预期）
{
    "data": {
        "items": [
            {
                "title": "标题",
                "link": "链接",
                "description": "描述"
            }
        ]
    }
}
```

---

## 🎓 最佳实践

### 1. Lambda 函数设计

```python
# ✅ 推荐的结构
- 清晰的配置部分
- 详细的日志输出
- 完整的错误处理
- 超时控制（30秒）
- 响应格式化

# ❌ 避免
- 硬编码凭证
- 缺少错误处理
- 超时时间过长
- 返回格式不统一
```

### 2. 部署规范

```bash
# 函数命名规范
{Provider}WebSearchFunction

# IAM 角色
可以共用 BochaLambdaExecutionRole

# Lambda 配置
- Runtime: Python 3.11
- Memory: 256MB
- Timeout: 30s
- Handler: {provider}_lambda_function.lambda_handler
```

### 3. Gateway Target 配置

```bash
# Target 命名规范
{Provider}SearchTarget

# Tool 命名规范
{provider}_search

# 工具将显示为
{Provider}SearchTarget___{provider}_search
```

---

## 🧪 测试新 Provider

创建测试脚本 `test_{provider}.py`：

```python
import requests
import json
import base64

# 加载配置
with open('../cognito-bocha-s2s.txt', 'r') as f:
    for line in f:
        if line.startswith('CLIENT_ID='):
            client_id = line.split('=', 1)[1].strip()
        elif line.startswith('CLIENT_SECRET='):
            client_secret = line.split('=', 1)[1].strip()
        elif line.startswith('TOKEN_ENDPOINT='):
            token_endpoint = line.split('=', 1)[1].strip()
        elif line.startswith('GATEWAY_URL='):
            gateway_url = line.split('=', 1)[1].strip()
        elif line.startswith('SCOPES='):
            scopes = line.split('=', 1)[1].strip()

# 获取 token
credentials = f"{client_id}:{client_secret}"
encoded = base64.b64encode(credentials.encode()).decode()
token_response = requests.post(
    token_endpoint,
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded}'
    },
    data={
        'grant_type': 'client_credentials',
        'scope': scopes
    }
)
token = token_response.json()['access_token']

# 测试新工具
payload = {
    'jsonrpc': '2.0',
    'method': 'tools/call',
    'params': {
        'name': 'MetasoSearchTarget___metaso_search',  # 修改工具名称
        'arguments': {
            'query': 'test query',
            'max_results': 3
        }
    },
    'id': 1
}

response = requests.post(
    gateway_url,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json=payload
)

print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

---

## 📚 参考文档

### Provider API 文档收集

在实现新 Provider 前，需要了解：

1. **API 端点 URL**
2. **认证方式** (Bearer Token / API Key / Custom)
3. **请求格式** (参数名称、数据类型)
4. **响应格式** (数据结构、字段名称)
5. **速率限制** (QPS、日配额)
6. **特殊功能** (图片搜索、时间过滤等)

### 常见 API 认证方式

```python
# 方式 1: Bearer Token
headers = {'Authorization': f'Bearer {API_KEY}'}

# 方式 2: API Key Header
headers = {'X-API-Key': API_KEY}

# 方式 3: Basic Auth
credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
headers = {'Authorization': f'Basic {credentials}'}

# 方式 4: Query Parameter
url = f'{API_ENDPOINT}?api_key={API_KEY}'
```

---

## 🔧 故障排除

### 问题 1: Lambda 函数调用失败

```bash
# 查看日志
aws logs tail /aws/lambda/YourFunctionName --follow --region us-east-1
```

### 问题 2: Target 创建失败

```bash
# 检查 Gateway 状态
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier <gateway-id> \
  --region us-east-1
```

### 问题 3: Tool 未出现在 Quick Suite

- 等待 1-2 分钟（Gateway 同步时间）
- 刷新 Quick Suite 页面
- 检查 Integration 状态

---

## 💡 提示

1. **复用现有资源**
   - 可以共用 Cognito User Pool
   - 可以共用 Gateway
   - 可以共用 IAM 角色

2. **渐进式添加**
   - 先添加一个 Provider 并测试
   - 确认工作正常后再添加下一个

3. **文档更新**
   - 在 `providers_config.json` 中记录新 Provider
   - 更新 README.md 中的支持列表

---

**模板已就绪！** 开始添加您的 AI Search Provider 吧！🚀
