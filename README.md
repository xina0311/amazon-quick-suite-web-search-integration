# 博查 Web Search - Amazon Quick Suite 集成

本项目提供了将博查 Web Search API 集成到 Amazon Quick Suite 的完整解决方案。

## 🎯 功能特性

- ✅ Amazon Cognito Service-to-Service (S2S) 认证
- ✅ AWS Lambda 函数集成博查 Web Search API
- ✅ Amazon Bedrock AgentCore Gateway
- ✅ Amazon Quick Suite MCP Integration
- ✅ 自动化部署脚本
- ✅ 完整的故障排除指南

## 📋 前置条件

1. **AWS 账户**
   - 具有创建 IAM 角色和策略的权限
   - Amazon Quick Suite 访问权限（Author Pro 订阅）

2. **本地环境**
   - AWS CLI 已配置 (`aws configure`)
   - Python 3.9+
   - jq (JSON 处理工具)
   - 命令行环境 (Terminal/Bash)

3. **博查 API**
   - 博查 Web Search API Key

## 🚀 快速开始

### 方式 1: 自动化部署（推荐）

```bash
# 1. 进入项目目录
cd bocha-web-search-integration

# 2. 设置博查 API Key（可选，也可以在部署后手动更新）
export BOCHA_API_KEY="your-actual-api-key"

# 3. 运行自动化部署脚本
chmod +x *.sh
./deploy_all.sh us-west-2
```

### 方式 2: 分步部署

```bash
# 1. 创建 Cognito S2S 认证
chmod +x setup_cognito_s2s_bocha.sh
./setup_cognito_s2s_bocha.sh us-west-2

# 2. 测试 Token 获取（可选）
./test-bocha-s2s-token.sh

# 3. 部署 Lambda 函数
chmod +x deploy_lambda.sh
./deploy_lambda.sh

# 4. 创建 AgentCore Gateway
python3 create_bocha_gateway.py
```

## 📁 项目结构

```
bocha-web-search-integration/
├── README.md                          # 本文件
├── setup_cognito_s2s_bocha.sh         # Cognito S2S 认证设置脚本
├── bocha_lambda_function.py           # Lambda 函数代码
├── deploy_lambda.sh                   # Lambda 部署脚本
├── create_bocha_gateway.py            # Gateway 创建脚本
├── deploy_all.sh                      # 一键自动化部署脚本
└── cognito-bocha-s2s.txt              # 配置文件（部署后生成）
```

## 🔧 配置 Amazon Quick Suite

部署完成后，按照以下步骤在 Quick Suite 中配置：

1. **登录 Amazon Quick Suite**
   - 使用 Author Pro 角色权限的账户

2. **创建 MCP Integration**
   - 导航到：Integrations > Actions > Model Context Protocol
   - 点击 "+" 创建新的 Integration

3. **配置参数**（从 `cognito-bocha-s2s.txt` 获取）
   ```
   Name: Bocha Web Search
   Description: Real-time web search using Bocha API
   MCP Endpoint: <GATEWAY_URL>
   Authentication: Service Authentication
   Client ID: <CLIENT_ID>
   Client Secret: <CLIENT_SECRET>
   Token URL: <TOKEN_ENDPOINT>
   ```

4. **验证 Integration**
   - 等待约 1-2 分钟，确认状态为 "Available"
   - 查看可用的 Actions，应该能看到 `bocha_web_search`

5. **测试**
   - 在 Chat Agent 中使用提示：
     ```
     使用博查搜索功能，帮我查找关于 "Amazon Bedrock" 的最新信息
     ```

## 📝 配置文件说明

部署后会生成 `cognito-bocha-s2s.txt` 文件，包含所有配置信息：

```
POOL_ID=<Cognito User Pool ID>
REGION=<AWS Region>
CLIENT_ID=<App Client ID>
CLIENT_SECRET=<App Client Secret>
TOKEN_ENDPOINT=<OAuth Token URL>
DISCOVERY_URL=<OIDC Discovery URL>
LAMBDA_ARN=<Lambda Function ARN>
GATEWAY_ARN=<AgentCore Gateway ARN>
GATEWAY_URL=<Gateway Endpoint URL>
```

**注意**：请妥善保管此文件，其中包含敏感信息（Client Secret）。

## 🧪 测试

### 测试 Cognito Token

```bash
./test-bocha-s2s-token.sh
```

### 测试 Lambda 函数

```bash
aws lambda invoke \
  --function-name BochaWebSearchFunction \
  --region us-west-2 \
  --payload '{"body": "{\"name\": \"bocha_web_search\", \"arguments\": {\"query\": \"test\"}}"}' \
  response.json
cat response.json
```

### 在 Quick Suite 中测试

使用以下提示测试 Integration：

1. **基础搜索**
   ```
   使用博查搜索查找关于 "Amazon Bedrock AgentCore" 的信息
   ```

2. **技术问题**
   ```
   搜索一下 Python MCP 开发教程
   ```

3. **新闻搜索**
   ```
   用博查搜索最近关于 AI Agent 的新闻
   ```

## 🔒 更新博查 API Key

### 方式 1: 通过环境变量

```bash
# 编辑 Lambda 函数代码
nano bocha_lambda_function.py

# 更新 BOCHA_API_KEY 行
BOCHA_API_KEY = "your-new-api-key"

# 重新部署
./deploy_lambda.sh
```

### 方式 2: 使用 AWS Lambda 环境变量

```bash
aws lambda update-function-configuration \
  --function-name BochaWebSearchFunction \
  --environment Variables={BOCHA_API_KEY=your-new-api-key} \
  --region us-west-2
```

## 🧹 清理资源

如需删除所有创建的资源：

```bash
# 运行清理脚本（由 setup 脚本生成）
./cleanup-cognito-bocha-s2s.sh

# 手动删除 Lambda 函数
aws lambda delete-function \
  --function-name BochaWebSearchFunction \
  --region us-west-2

# 删除 Lambda IAM 角色
aws iam detach-role-policy \
  --role-name BochaLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name BochaLambdaExecutionRole

# 删除 AgentCore Gateway（需要手动在 AWS Console 中操作）
```

## 🐛 故障排除

### 问题 1: Token 获取失败

**症状**: `Failed to obtain token`

**解决方案**:
- 检查 AWS CLI 配置
- 验证 Cognito User Pool 和 App Client 配置
- 运行 `./test-bocha-s2s-token.sh` 查看详细错误

### 问题 2: Lambda 函数错误

**症状**: `Internal server error`

**解决方案**:
```bash
# 查看 Lambda 日志
aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-west-2
```

### 问题 3: Gateway 连接失败

**症状**: `Unable to connect to MCP server`

**解决方案**:
- 确认 Gateway URL 正确
- 检查 Cognito Allowed Clients 配置
- 验证 Lambda 函数状态

### 问题 4: 博查 API 调用失败

**症状**: `HTTP 401 Unauthorized`

**解决方案**:
- 验证博查 API Key 是否正确
- 检查博查 API endpoint URL
- 确认账户状态和 API 额度

## 📚 相关文档

- [完整操作指南](../Bocha_Web_Search_Quick_Suite_Integration_Guide.md)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Amazon Quick Suite Documentation](https://docs.aws.amazon.com/quicksuite/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## 💡 注意事项

1. **安全性**
   - 不要将 `cognito-bocha-s2s.txt` 文件提交到版本控制
   - 定期轮换 API Key 和 Cognito 凭证
   - 使用 AWS Secrets Manager 存储敏感信息（生产环境）

2. **成本**
   - Lambda 调用费用
   - Cognito 认证费用
   - AgentCore Gateway 费用
   - 博查 API 调用费用

3. **限制**
   - Lambda 默认超时：30秒
   - Lambda 默认内存：256MB
   - 博查 API 调用限制（根据您的订阅计划）

## 🤝 支持

如有问题或建议，请：
1. 查看完整操作指南
2. 检查故障排除部分
3. 查看 AWS 服务文档
4. 联系技术支持

## 📄 许可证

本项目遵循 MIT 许可证。

---

**版本**: 1.0  
**最后更新**: 2025年10月  
**作者**: AWS Solutions Team
