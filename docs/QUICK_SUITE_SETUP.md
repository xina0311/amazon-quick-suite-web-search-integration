# Amazon Quick Suite 配置指南

本文档介绍如何在 Amazon Quick Suite 中配置 MCP Integration，以使用已部署的 AI Search Providers。

## 📋 前置条件

在配置 Quick Suite 之前，您需要：

1. ✅ 已完成基础设施部署（Cognito + Gateway）
2. ✅ 至少部署了一个 AI Search Provider（博查或秘塔）
3. ✅ 拥有 `config.txt` 配置文件
4. ✅ Amazon Quick Suite Author Pro 权限

## 🔧 配置步骤

### 步骤 1: 获取配置参数

从项目根目录的 `config.txt` 文件中获取以下信息：

```bash
cat config.txt
```

您需要的配置参数：
- `GATEWAY_URL` - MCP Server Endpoint
- `CLIENT_ID` - Client ID
- `CLIENT_SECRET` - Client Secret  
- `TOKEN_ENDPOINT` - Token URL

### 步骤 2: 登录 Amazon Quick Suite

1. 访问 Amazon Quick Suite 控制台
2. 使用具有 Author Pro 角色的账户登录

### 步骤 3: 创建 MCP Integration

1. 导航到：**Integrations** > **Actions** > **Model Context Protocol**
2. 点击 **"+"** 按钮创建新的 Integration

### 步骤 4: 填写配置信息

#### 基本信息

**Name**: `AI Search Integration`

**Description**: 根据您部署的 Provider 定制描述

##### 如果只部署了博查：
```
提供实时网页搜索功能。

可用工具：
- BochaWebSearchTarget___bocha_web_search: 博查网页搜索，适合查找最新资讯和新闻
```

##### 如果只部署了秘塔：
```
提供多种类型的搜索功能。

可用工具：
- MetasoWebSearchTarget___metaso_web_search: 秘塔 AI Search，支持网页、文档、论文、图片、视频、播客搜索
```

##### 如果两者都部署了：
```
提供多种 AI Search 服务，满足不同的搜索需求。

可用工具：
- BochaWebSearchTarget___bocha_web_search: 博查网页搜索，适合查找最新资讯和新闻
- MetasoWebSearchTarget___metaso_web_search: 秘塔 AI Search，支持网页、文档、论文、图片、视频、播客搜索
```

#### 连接配置

**MCP Server Endpoint**:
```
从 config.txt 复制 GATEWAY_URL 的值
例如: https://xxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
```

**Authentication Type**: 选择 `Service authentication`

**Client ID**:
```
从 config.txt 复制 CLIENT_ID 的值
```

**Client Secret**:
```
从 config.txt 复制 CLIENT_SECRET 的值
```

**Token URL**:
```
从 config.txt 复制 TOKEN_ENDPOINT 的值
例如: https://xxx.auth.us-east-1.amazoncognito.com/oauth2/token
```

### 步骤 5: 保存并验证

1. 点击 **Save** 保存配置
2. 等待 1-2 分钟，系统会自动验证连接
3. 确认状态显示为 **Available** (绿色)
4. 查看 **Available Actions**，确认能看到已部署的搜索工具

## ✅ 验证部署

### 查看可用工具

在 Integration 详情页面，应该能看到以下工具（取决于您部署的 Provider）：

#### 博查搜索工具
- **工具名称**: `BochaWebSearchTarget___bocha_web_search`
- **描述**: 博查 Web Search - 实时网页搜索
- **参数**: 
  - `query` (必填): 搜索关键词
  - `max_results` (可选): 结果数量 (1-50)

#### 秘塔搜索工具
- **工具名称**: `MetasoWebSearchTarget___metaso_web_search`
- **描述**: 秘塔 AI Search - 多类型搜索
- **参数**:
  - `query` (必填): 搜索关键词
  - `scope` (可选): 搜索范围 (webpage/document/paper/image/video/podcast)
  - `max_results` (可选): 结果数量 (1-50)
  - `include_summary` (可选): 提升召回率
  - `include_raw_content` (可选): 获取原文
  - `concise_snippet` (可选): 简洁摘要

## 🎯 使用示例

### 在 Chat Agent 中测试

创建或打开一个 Chat Agent，尝试以下提示词：

#### 博查搜索示例

```
使用博查搜索查找关于 AWS Lambda 的最新信息
```

```
搜索一下人工智能的新闻资讯
```

```
用博查查找 Amazon Bedrock 的相关内容
```

#### 秘塔搜索示例

```
使用秘塔搜索查找关于量子计算的学术论文
```

```
搜索机器学习相关的技术文档
```

```
用秘塔搜索深度学习的教学视频
```

#### 对比测试

```
分别使用博查和秘塔搜索关于"人工智能"的信息，并对比结果
```

## 🔍 工具选择建议

根据不同的搜索需求选择合适的工具：

| 搜索需求 | 推荐工具 | 原因 |
|---------|---------|------|
| 新闻资讯 | 博查 | 实时性强，新闻覆盖全面 |
| 学术论文 | 秘塔 | 专门的论文搜索引擎 |
| 技术文档 | 秘塔 | 支持文档类型筛选 |
| 通用网页 | 两者均可 | 根据偏好选择 |
| 图片/视频 | 秘塔 | 支持多媒体搜索 |

## 🛠️ 故障排除

### 问题 1: Integration 状态为 "Unavailable"

**可能原因**:
- Gateway 尚未就绪
- 认证配置错误
- 网络连接问题

**解决方案**:
```bash
# 1. 检查 Gateway 状态
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $(grep GATEWAY_ARN config.txt | cut -d'=' -f2)

# 2. 验证 Token 获取
cd utils
python3 test_gateway.py
```

### 问题 2: 看不到搜索工具

**可能原因**:
- Provider Lambda 未部署
- Gateway Target 未添加

**解决方案**:
```bash
# 检查已部署的 Targets
aws bedrock-agentcore-control list-gateway-targets \
  --gateway-identifier $(grep GATEWAY_ARN config.txt | cut -d'=' -f2)

# 确认 Lambda 函数存在
aws lambda list-functions --query 'Functions[?contains(FunctionName, `WebSearchFunction`)].FunctionName'
```

### 问题 3: 搜索返回错误

**可能原因**:
- API Key 未配置或已过期
- Lambda 函数错误

**解决方案**:
```bash
# 查看 Lambda 日志
aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-east-1
aws logs tail /aws/lambda/MetasoWebSearchFunction --follow --region us-east-1

# 测试 Lambda 函数
cd providers/bocha
aws lambda invoke --function-name BochaWebSearchFunction \
  --payload '{"query": "test"}' response.json
```

## 📝 配置更新

### 更新 Description

当您添加新的 Provider 时，记得更新 Integration 的 Description：

1. 在 Quick Suite 中找到您的 Integration
2. 点击编辑
3. 在 Description 中添加新工具的说明
4. 保存更改

### 重新配置 Integration

如果需要完全重新配置：

1. 删除现有的 Integration
2. 按照上述步骤重新创建
3. 等待状态变为 Available

## 🔒 安全建议

1. **保护配置文件**
   - 不要将 `config.txt` 提交到版本控制
   - 定期轮换 Client Secret

2. **最小权限原则**
   - 只给需要的用户 Author Pro 权限
   - 定期审查权限分配

3. **监控使用**
   - 定期检查 CloudWatch 日志
   - 监控 API 调用量和成本

## 📚 相关文档

- [项目主 README](../README.md)
- [架构设计](../ARCHITECTURE.md)
- [博查 Provider 文档](../providers/bocha/README.md)
- [秘塔 Provider 文档](../providers/metaso/README.md)

## 💡 最佳实践

1. **测试工具功能**
   - 配置完成后，先用简单的查询测试每个工具
   - 确认返回结果符合预期

2. **优化提示词**
   - 明确指定要使用的搜索工具
   - 提供清晰的搜索关键词

3. **监控性能**
   - 关注搜索响应时间
   - 定期检查 Lambda 函数性能

4. **成本优化**
   - 合理设置 max_results
   - 避免重复搜索相同内容

---

**配置完成后，您就可以开始使用强大的 AI Search 功能了！** 🎉

如有问题，请参考故障排除部分或查看详细的日志信息。
