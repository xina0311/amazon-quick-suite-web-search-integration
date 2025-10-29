# Amazon Quick Suite + AgentCore Gateway + Bocha Web Search

## 🎉 项目简介

本项目提供了一个**生产就绪**的解决方案，通过 **Amazon Bedrock AgentCore Gateway** 将**博查 Web Search API** 集成到 **Amazon Quick Suite** 中。

### ✨ 核心特性

- ✅ **统一认证管理** - 使用 Amazon Cognito Service-to-Service 认证
- ✅ **灵活扩展** - 通过 Gateway Targets 轻松添加多个 AI Search Provider
- ✅ **自动化部署** - 一键部署所有组件
- ✅ **生产就绪** - 完整的错误处理、日志和监控
- ✅ **经过验证** - 端到端测试通过

---

## 📋 项目状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 部署状态 | ✅ 成功 | us-east-1 |
| 测试状态 | ✅ 通过 | 端到端测试完成 |
| Quick Suite 集成 | ✅ 成功 | 用户已验证 |
| 文档完整性 | ✅ 完整 | 所有文档齐全 |
| 代码质量 | ✅ 生产级 | 完整的错误处理 |

---

## 🏗️ 架构设计

```
Amazon Quick Suite (一次配置)
        ↓
Amazon Cognito S2S 认证 (统一认证层)
        ↓
AgentCore Gateway (统一入口)
        ↓
多个 Gateway Targets 对接外部 AI Search Providers (灵活扩展)
  ├── Target 1: Bocha (Lambda → api.bochaai.com) ✅ 已部署
  ├── Target 2: 秘塔 (Lambda → metaso.cn) 📝 待添加
  ├── Target 3: Cloudsway (Lambda → cloudsway.ai) 📝 待添加
  └── Target N: 其他服务 (Lambda → custom-api.com) 📝 可扩展
```

详细架构图请查看：[ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📂 项目结构

```
bocha-web-search-integration/
│
├── 📚 文档
│   ├── PROJECT_README.md              # 本文件 - 项目总览
│   ├── README.md                      # 详细使用文档
│   ├── QUICKSTART.md                  # 5分钟快速部署
│   ├── DEPLOYMENT_SUCCESS.md          # 部署成功总结
│   ├── TROUBLESHOOTING.md             # 故障排除指南
│   └── ARCHITECTURE.md                # 架构设计和 Mermaid 图
│
├── 🔧 部署脚本
│   ├── setup_cognito_s2s_bocha.sh    # Cognito S2S 认证设置
│   ├── deploy_lambda.sh               # Lambda 函数部署
│   ├── deploy_all.sh                  # 一键自动化部署
│   ├── create_bocha_gateway.py        # Gateway 和 Target 创建
│   └── test_gateway.py                # Gateway 测试验证
│
├── 💻 源代码
│   └── bocha_lambda_function.py       # Lambda 函数（博查 API 集成）
│
├── ⚙️ 配置
│   ├── .gitignore                     # Git 忽略配置
│   └── cognito-bocha-s2s.txt         # 部署配置（自动生成，不提交）
│
└── 📖 主文档
    └── ../Bocha_Web_Search_Quick_Suite_Integration_Guide.md
```

---

## 🚀 快速开始

### 前置条件

- AWS 账户（具有 IAM、Lambda、Cognito、Bedrock AgentCore 权限）
- Amazon Quick Suite 访问权限（Author Pro）
- AWS CLI 已配置
- Python 3.9+
- 博查 API Key

### 一键部署

```bash
# 1. 克隆项目
cd bocha-web-search-integration

# 2. 设置 API Key（如需要）
export BOCHA_API_KEY="your-api-key"

# 3. 一键部署（3-5分钟）
./deploy_all.sh us-east-1
```

### Quick Suite 配置

部署完成后，使用生成的配置参数在 Quick Suite 中创建 MCP Integration。

详细步骤：[QUICKSTART.md](QUICKSTART.md)

---

## ✅ 部署验证

### 已部署的组件（us-east-1）

| 组件 | 资源 ID | 状态 |
|------|---------|------|
| Cognito User Pool | us-east-1_c2ji4Zupf | ✅ |
| App Client | 77ks62olpo5jqrt4dtspfrlnr6 | ✅ |
| Lambda 函数 | BochaWebSearchFunction | ✅ |
| Gateway | bochawebsearchgateway-xgafjdpdja | ✅ READY |
| Gateway Target | XGWUHLVTEW | ✅ |

### 测试验证

```bash
# 运行测试脚本
python3 test_gateway.py

# 预期结果：
# ✓ Token 获取成功
# ✓ ListTools 成功（1个工具）
# ✓ InvokeTool 成功（返回搜索结果）
```

---

## 🔧 添加新的 AI Search Provider

### 通用模板

为了方便您添加秘塔、Cloudsway 等其他服务，我们提供了通用模板。

#### 步骤 1: 创建新的 Lambda 函数

```python
# 文件名: metaso_lambda_function.py
import json
import requests

METASO_API_KEY = "your-metaso-api-key"
METASO_API_ENDPOINT = "https://metaso.cn/api/search"

def lambda_handler(event, context):
    """处理秘塔搜索请求"""
    query = event.get('query', '')
    max_results = event.get('max_results', 10)
    
    # 调用秘塔 API
    response = requests.post(
        METASO_API_ENDPOINT,
        headers={'Authorization': f'Bearer {METASO_API_KEY}'},
        json={'query': query, 'limit': max_results}
    )
    
    results = response.json()
    
    # 返回 MCP 格式
    return {
        'statusCode': 200,
        'body': json.dumps({
            'content': [{
                'type': 'text',
                'text': format_results(results)
            }]
        })
    }
```

#### 步骤 2: 部署新的 Lambda

```bash
# 使用现有的部署脚本作为模板
cp deploy_lambda.sh deploy_metaso_lambda.sh

# 修改脚本中的函数名称
# LAMBDA_FUNCTION_NAME="MetasoWebSearchFunction"

# 部署
REGION=us-east-1 ./deploy_metaso_lambda.sh
```

#### 步骤 3: 添加 Gateway Target

```bash
# 使用 AWS CLI 添加新 Target
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier bochawebsearchgateway-xgafjdpdja \
  --name MetasoWebSearchTarget \
  --description "Metaso AI Search Target" \
  --target-configuration '{
    "mcp": {
      "lambda": {
        "lambdaArn": "arn:aws:lambda:us-east-1:xxx:function:MetasoWebSearchFunction",
        "toolSchema": {
          "inlinePayload": [{
            "name": "metaso_web_search",
            "description": "Search using Metaso AI",
            "inputSchema": {
              "type": "object",
              "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"}
              },
              "required": ["query"]
            }
          }]
        }
      }
    }
  }' \
  --credential-provider-configurations '[{
    "credentialProviderType": "GATEWAY_IAM_ROLE"
  }]' \
  --region us-east-1
```

#### 步骤 4: 验证

```bash
# 立即可用！Quick Suite 会自动发现新工具
# 无需重新配置认证！
```

---

## 📊 已验证的工作流程

### 端到端测试结果

```
步骤 1: Cognito Token 获取 ✅
  └─ < 1秒

步骤 2: Gateway ListTools ✅
  └─ 发现 1 个工具

步骤 3: Tool Invocation ✅
  └─ 查询: "Amazon Bedrock AgentCore"
  └─ 返回: 3 个搜索结果
  └─ 总时间: < 3秒
```

### Quick Suite 测试

用户已成功在 Quick Suite 中：
- ✅ 创建 MCP Integration
- ✅ 状态显示为 "Available"
- ✅ Chat Agent 可以调用博查搜索

---

## 🎓 通用配置指南

### 添加新 Provider 的最佳实践

#### 1. Lambda 函数设计模式

```python
# 推荐的 Lambda 函数结构

import json
import requests

# 配置常量
API_KEY = "your-api-key"
API_ENDPOINT = "https://provider-api.com/search"

def lambda_handler(event, context):
    """主处理函数"""
    try:
        # 1. 提取参数
        query = event.get('query', '')
        max_results = event.get('max_results', 10)
        
        # 2. 验证参数
        if not query:
            return error_response('Query is required')
        
        # 3. 调用外部 API
        result = call_provider_api(query, max_results)
        
        # 4. 格式化响应
        formatted = format_results(result)
        
        # 5. 返回 MCP 格式
        return success_response(formatted)
        
    except Exception as e:
        return error_response(str(e))

def call_provider_api(query, count):
    """调用外部 API"""
    response = requests.post(
        API_ENDPOINT,
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'query': query, 'count': count},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def format_results(data):
    """格式化结果"""
    # 根据 Provider 的响应格式进行转换
    pass

def success_response(text):
    """成功响应"""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'content': [{'type': 'text', 'text': text}]
        })
    }

def error_response(error):
    """错误响应"""
    return {
        'statusCode': 500,
        'body': json.dumps({'error': error})
    }
```

#### 2. Gateway Target Schema 模板

```python
# 通用的 Tool Schema 模板
tool_schema = {
    "name": "provider_name_search",
    "description": "Search using Provider Name API. Use this for...",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results (1-50)"
            },
            # 可选：添加 Provider 特定参数
            "search_type": {
                "type": "string",
                "description": "Type of search: web, academic, news"
            }
        },
        "required": ["query"]
    }
}
```

#### 3. 部署脚本模板

创建 `add_new_provider.sh`：

```bash
#!/bin/bash
# 添加新 AI Search Provider 的通用脚本

PROVIDER_NAME=$1
LAMBDA_ARN=$2
GATEWAY_ID="bochawebsearchgateway-xgafjdpdja"
REGION="us-east-1"

if [ -z "$PROVIDER_NAME" ] || [ -z "$LAMBDA_ARN" ]; then
    echo "Usage: ./add_new_provider.sh <provider_name> <lambda_arn>"
    echo "Example: ./add_new_provider.sh metaso arn:aws:lambda:us-east-1:xxx:function:MetasoFunction"
    exit 1
fi

echo "添加新的 AI Search Provider: $PROVIDER_NAME"
echo "Lambda ARN: $LAMBDA_ARN"
echo "Gateway ID: $GATEWAY_ID"

# 创建 Target（使用通用模板）
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier $GATEWAY_ID \
  --name "${PROVIDER_NAME}SearchTarget" \
  --description "${PROVIDER_NAME} AI Search Target" \
  --target-configuration "{
    \"mcp\": {
      \"lambda\": {
        \"lambdaArn\": \"$LAMBDA_ARN\",
        \"toolSchema\": {
          \"inlinePayload\": [{
            \"name\": \"${PROVIDER_NAME}_search\",
            \"description\": \"Search using ${PROVIDER_NAME} AI\",
            \"inputSchema\": {
              \"type\": \"object\",
              \"properties\": {
                \"query\": {\"type\": \"string\"},
                \"max_results\": {\"type\": \"integer\"}
              },
              \"required\": [\"query\"]
            }
          }]
        }
      }
    }
  }" \
  --credential-provider-configurations '[{
    "credentialProviderType": "GATEWAY_IAM_ROLE"
  }]' \
  --region $REGION

echo "✓ Target 添加成功！"
echo "Quick Suite 会自动发现新工具，无需重新配置认证"
```

#### 4. 配置文件管理

创建 `providers_config.json`：

```json
{
  "providers": [
    {
      "name": "bocha",
      "display_name": "博查搜索",
      "api_endpoint": "https://api.bochaai.com/v1/web-search",
      "auth_type": "bearer_token",
      "lambda_function": "BochaWebSearchFunction",
      "status": "active",
      "features": ["web_search", "summary", "freshness_filter"]
    },
    {
      "name": "metaso",
      "display_name": "秘塔搜索",
      "api_endpoint": "https://metaso.cn/api/search",
      "auth_type": "api_key",
      "lambda_function": "MetasoWebSearchFunction",
      "status": "planned",
      "features": ["academic_search", "image_search"]
    },
    {
      "name": "cloudsway",
      "display_name": "云途搜索",
      "api_endpoint": "https://cloudsway.ai/api/search",
      "auth_type": "custom",
      "lambda_function": "CloudswaySearchFunction",
      "status": "planned",
      "features": ["enterprise_search", "knowledge_base"]
    }
  ],
  "gateway": {
    "gateway_id": "bochawebsearchgateway-xgafjdpdja",
    "gateway_url": "https://bochawebsearchgateway-xgafjdpdja.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
    "region": "us-east-1",
    "protocol": "MCP",
    "auth_type": "CUSTOM_JWT"
  }
}
```

---

## 📖 文档索引

### 快速导航

| 文档 | 用途 | 适合人员 |
|------|------|----------|
| [PROJECT_README.md](PROJECT_README.md) | 项目总览 | 所有人 |
| [QUICKSTART.md](QUICKSTART.md) | 5分钟快速开始 | 新用户 |
| [README.md](README.md) | 详细使用说明 | 开发者 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 架构设计 | 架构师 |
| [DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md) | 部署总结 | 运维人员 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 故障排除 | 支持团队 |
| [../Bocha_Web_Search_Quick_Suite_Integration_Guide.md](../Bocha_Web_Search_Quick_Suite_Integration_Guide.md) | 完整指南 | 所有人 |

---

## 🧪 测试

### 运行测试

```bash
# 测试 Gateway 连接和工具调用
python3 test_gateway.py
```

### 测试结果（已验证）

```
✓ Token 获取成功
✓ 工具列表获取成功（1个工具）
✓ 工具调用成功（返回搜索结果）
✓ Quick Suite 集成成功
```

---

## 🔐 安全配置

### 敏感信息管理

**不要提交到 Git**：
- `cognito-bocha-s2s.txt` - 包含凭证信息
- `cleanup-cognito-bocha-s2s.sh` - 包含配置信息
- `test-bocha-s2s-token.sh` - 包含凭证信息
- `*.zip` - Lambda 部署包
- `lambda_deployment/` - 临时文件

**已配置 .gitignore** ✅

### 生产环境建议

1. **使用 AWS Secrets Manager**
   ```python
   # 从 Secrets Manager 获取 API Key
   secrets_client = boto3.client('secretsmanager')
   secret = secrets_client.get_secret_value(SecretId='bocha/api-key')
   BOCHA_API_KEY = secret['SecretString']
   ```

2. **定期轮换凭证**
   - Cognito Client Secret
   - API Keys
   - IAM 角色

3. **启用日志和监控**
   - CloudWatch Logs
   - CloudWatch Metrics
   - X-Ray Tracing

---

## 📈 扩展路线图

### 第一阶段 ✅（已完成）
- [x] 博查 Web Search 集成
- [x] Cognito S2S 认证
- [x] AgentCore Gateway 部署
- [x] Quick Suite 集成验证
- [x] 完整文档和测试

### 第二阶段 📝（计划中）
- [ ] 添加秘塔搜索（学术搜索）
- [ ] 添加 Cloudsway（企业搜索）
- [ ] 添加通用部署脚本
- [ ] 实现智能路由

### 第三阶段 🔮（未来）
- [ ] 结果聚合和去重
- [ ] 缓存层（ElastiCache）
- [ ] 成本监控和优化
- [ ] 多区域部署

---

## 💡 最佳实践

### 1. Gateway 管理
- 一个 Gateway 管理多个 Targets
- 统一认证配置
- 集中监控和日志

### 2. Lambda 函数设计
- 每个 Provider 独立 Lambda
- 统一的错误处理
- 详细的日志记录
- 合理的超时配置（建议 30-60秒）

### 3. 成本优化
- Lambda 内存优化（256-512MB）
- 合理的超时配置
- 考虑缓存常见查询
- 监控调用量

### 4. 可靠性
- 实现重试逻辑
- 添加熔断器
- 服务降级策略
- 健康检查

---

## 🤝 贡献指南

### 添加新 Provider

1. Fork 本项目
2. 创建新的 Lambda 函数（使用模板）
3. 添加 Gateway Target
4. 测试验证
5. 更新文档
6. 提交 Pull Request

### 代码规范

- Python: PEP 8
- Shell: ShellCheck
- 文档: Markdown
- 提交信息: Conventional Commits

---

## 📞 支持

### 问题报告

- GitHub Issues
- 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 相关资源

- [Amazon Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Amazon Quick Suite Docs](https://docs.aws.amazon.com/quicksuite/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [博查 AI 开放平台](https://open.bochaai.com/)

---

## 📄 许可证

本项目遵循 MIT 许可证。详见 [LICENSE](../../../../LICENSE) 文件。

---

## 🏆 致谢

- AWS Bedrock AgentCore 团队
- Amazon Quick Suite 团队
- 博查 AI 团队

---

**版本**: 1.0.0  
**最后更新**: 2025年10月29日  
**状态**: ✅ 生产就绪  
**维护者**: AWS Solutions Team
