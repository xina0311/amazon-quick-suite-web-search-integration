# 🚀 快速开始 - 5分钟部署指南

本指南将帮助您在5分钟内完成博查 Web Search 与 Amazon Quick Suite 的集成。

## ⚡ 一键部署

```bash
# 1. 进入项目目录
cd bocha-web-search-integration

# 2. 设置博查 API Key
export BOCHA_API_KEY="your-actual-api-key"

# 3. 一键部署（约3-5分钟）
./deploy_all.sh us-west-2
```

## 📋 部署后配置

部署完成后，您会看到以下配置信息：

```
Gateway URL: https://bedrock-agentcore.us-west-2.amazonaws.com/...
Client ID: xxxxxxxxxxxxx
Client Secret: xxxxxxxxxxxxx
Token URL: https://bocha-search-xxxx.auth.us-west-2.amazoncognito.com/oauth2/token
```

### 在 Quick Suite 中配置

1. **登录 Quick Suite** → Integrations → Actions → Model Context Protocol
2. **点击 "+"** 创建新 Integration
3. **填写配置**：
   - Name: `Bocha Web Search`
   - MCP Endpoint: `<GATEWAY_URL>`
   - Authentication: `Service Authentication`
   - Client ID: `<CLIENT_ID>`
   - Client Secret: `<CLIENT_SECRET>`
   - Token URL: `<TOKEN_ENDPOINT>`
4. **等待** 约1-2分钟，状态变为 "Available"
5. **测试** 在 Chat Agent 中使用：
   ```
   使用博查搜索查找 "Amazon Bedrock" 的信息
   ```

## ✅ 验证检查清单

- [ ] AWS CLI 已配置 (`aws sts get-caller-identity`)
- [ ] 博查 API Key 已设置
- [ ] 部署脚本执行成功
- [ ] Quick Suite Integration 状态为 "Available"
- [ ] Chat Agent 能够调用博查搜索

## 🆘 快速故障排除

### 问题：Token 获取失败
```bash
# 测试 token
./test-bocha-s2s-token.sh
```

### 问题：Lambda 错误
```bash
# 查看日志
aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-west-2
```

### 问题：需要更新 API Key
```bash
# 编辑 Lambda 函数
nano bocha_lambda_function.py
# 重新部署
./deploy_lambda.sh
```

## 📚 更多帮助

- 详细指南：[README.md](README.md)
- 完整文档：[../Bocha_Web_Search_Quick_Suite_Integration_Guide.md](../Bocha_Web_Search_Quick_Suite_Integration_Guide.md)

## 🧹 清理资源

```bash
./cleanup-cognito-bocha-s2s.sh
aws lambda delete-function --function-name BochaWebSearchFunction --region us-west-2
```

---

**需要帮助？** 查看 [README.md](README.md) 中的故障排除部分
