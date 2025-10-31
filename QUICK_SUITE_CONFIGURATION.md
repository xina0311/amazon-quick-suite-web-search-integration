# Amazon Quick Suite Integration 配置指南

按照以下步骤在 Amazon Quick Suite 中配置 MCP Integration。

## 📋 配置信息

### 从 config.txt 获取以下信息

```bash
cat config.txt | grep -E "(GATEWAY_URL|CLIENT_ID|CLIENT_SECRET|TOKEN_ENDPOINT)"
```

您需要：
- **GATEWAY_URL**: https://aisearchgateway-hmyu9jjtvj.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
- **CLIENT_ID**: 6mm4p8ta3vbld6q4nl39pnvsah
- **CLIENT_SECRET**: 16ogd2mt7km98mdi2v7kb4m46suf7aq61pna8vfcr2ooa37pm19t
- **TOKEN_ENDPOINT**: https://bocha-search-1761795855.auth.us-east-1.amazoncognito.com/oauth2/token

## 🚀 配置步骤

### 步骤 1: 登录 Amazon Quick Suite

1. 访问 Amazon Quick Suite 控制台
2. 使用具有 **Author Pro** 角色的账户登录

### 步骤 2: 创建新的 MCP Integration

1. 导航到：**Integrations** → **Actions** → **Model Context Protocol**
2. 点击 **"+"** 按钮创建新的 Integration

### 步骤 3: 填写基本信息

**Name** (Integration 名称):
```
AI Web Search
```

**Description** (推荐使用 - 最清晰明确):
```
This integration provides two specialized AI web search tools.

First tool BochaWebSearchTarget___bocha_web_search is designed for real-time web content, breaking news, latest articles and current events. Best for finding recent information and news stories.

Second tool MetasoWebSearchTarget___metaso_web_search is designed for research and academic content including scholarly papers, technical documents, webpages, images, videos and podcasts. Best for academic research and technical documentation.

When users need current news or recent articles, use BochaWebSearchTarget. When users need research papers or technical documents, use MetasoWebSearchTarget.
```

**Description** (简短版本 - 如果字符数受限):
```
Two AI search tools. Bocha searches real-time news and web articles. Metaso searches academic papers, documents, webpages, images and videos. Choose Bocha for current news, choose Metaso for research and technical content.
```

**Description** (最简版本):
```
AI web search with Bocha and Metaso tools for news, papers and documents.
```

**注意**: Description 只允许字母、数字、空格、下划线、句号、逗号、感叹号、问号和连字符，不能使用括号、冒号、斜杠等特殊字符。

### 步骤 4: 配置连接参数

#### MCP Server Endpoint
```
https://aisearchgateway-hmyu9jjtvj.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
```

#### Authentication Type
选择: **Service authentication**

#### Client ID
```
6mm4p8ta3vbld6q4nl39pnvsah
```

#### Client Secret
```
16ogd2mt7km98mdi2v7kb4m46suf7aq61pna8vfcr2ooa37pm19t
```

#### Token URL
```
https://bocha-search-1761795855.auth.us-east-1.amazoncognito.com/oauth2/token
```

### 步骤 5: 保存并验证

1. 点击 **Save** 保存配置
2. 等待 **1-2 分钟**，系统会自动验证连接
3. 确认状态显示为 **"Available"** (绿色勾选)
4. 点击 Integration 查看详情

### 步骤 6: 查看可用工具

在 Integration 详情页，点击 **"Available Actions"**，您应该看到：

#### 工具 1: Bocha Web Search
- **名称**: `BochaWebSearchTarget___bocha_web_search`
- **描述**: Real-time web search, ideal for finding latest news and articles
- **参数**:
  - `query` (required, string): Search query keywords
  - `max_results` (optional, integer): Number of results to return (1-50, default 10)

#### 工具 2: Metaso AI Search
- **名称**: `MetasoWebSearchTarget___metaso_web_search`
- **描述**: Multi-scope AI search supporting various content types
- **参数**:
  - `query` (required, string): Search query keywords
  - `scope` (optional, string): Search scope - webpage/document/paper/image/video/podcast
  - `max_results` (optional, integer): Number of results (1-50, default 10)
  - `include_summary` (optional, boolean): Enhance recall with summaries
  - `include_raw_content` (optional, boolean): Fetch raw content
  - `concise_snippet` (optional, boolean): Concise snippets

## 🎯 测试 Integration

### 在 Chat Agent 中测试

创建或打开一个 Chat Agent，尝试以下提示词：

#### 测试博查搜索
```
Use the bocha web search tool to find information about "Amazon Bedrock AgentCore"
```

或中文：
```
使用博查搜索查找关于 Amazon Bedrock AgentCore 的信息
```

#### 测试秘塔搜索
```
Use the metaso search tool to find academic papers about "machine learning"
```

或中文：
```
使用秘塔搜索查找关于机器学习的学术论文
```

#### 对比两个搜索工具
```
Compare results from both bocha and metaso search tools for "artificial intelligence"
```

或中文：
```
分别使用博查和秘塔搜索"人工智能"，并对比结果
```

## ✅ 验证成功标志

### Integration 状态
- ✅ 状态显示为 "Available"
- ✅ 没有错误消息
- ✅ 可以看到 2 个 Available Actions

### Chat Agent 测试
- ✅ Agent 能够识别并调用搜索工具
- ✅ 返回搜索结果（标题、链接、摘要）
- ✅ 结果格式正确，内容相关

## 🔧 故障排除

### 问题 1: Integration 状态为 "Unavailable"

**可能原因**:
- Gateway URL 不正确
- 认证信息错误
- Token URL 不正确

**解决方案**:
```bash
# 验证配置信息
cat config.txt | grep -E "(GATEWAY_URL|CLIENT_ID|TOKEN_ENDPOINT)"

# 测试 Gateway
cd utils && python3 test_gateway.py
```

### 问题 2: 看不到工具

**可能原因**:
- Target 未添加
- Gateway 未就绪

**解决方案**:
```bash
# 列出 Targets
aws bedrock-agentcore-control list-gateway-targets \
  --gateway-identifier aisearchgateway-hmyu9jjtvj \
  --region us-east-1

# 应该看到 BochaWebSearchTarget 和 MetasoWebSearchTarget
```

### 问题 3: 搜索返回错误

**可能原因**:
- Lambda API Key 未配置
- Lambda 函数错误

**解决方案**:
```bash
# 检查 Lambda 环境变量
aws lambda get-function-configuration \
  --function-name BochaWebSearchFunction \
  --query 'Environment.Variables.BOCHA_API_KEY'

aws lambda get-function-configuration \
  --function-name MetasoWebSearchFunction \
  --query 'Environment.Variables.METASO_API_KEY'

# 查看 Lambda 日志
aws logs tail /aws/lambda/BochaWebSearchFunction --follow
aws logs tail /aws/lambda/MetasoWebSearchFunction --follow
```

## 💡 使用建议

### 选择合适的搜索工具

| 需求 | 推荐工具 | 原因 |
|------|---------|------|
| 新闻资讯 | Bocha | Real-time, comprehensive news coverage |
| 学术论文 | Metaso | Specialized paper search engine |
| 技术文档 | Metaso | Document type filtering |
| 通用网页 | Both | Choose based on preference |
| 图片/视频 | Metaso | Multimedia search support |

### 提示词建议

**明确指定工具**:
```
Use bocha search to find...
Use metaso search with paper scope to find...
```

**让 Agent 选择**:
```
Search for information about [topic]
(Agent will automatically choose the appropriate tool)
```

## 📚 相关文档

- [项目 README](README.md) - 项目概览
- [部署指南](DEPLOYMENT_GUIDE.md) - 完整部署步骤
- [优化报告](OPTIMIZATION_COMPLETE.md) - 优化总结
- [博查文档](providers/bocha/README.md) - 博查详细说明
- [秘塔文档](providers/metaso/README.md) - 秘塔详细说明

## 🎊 配置完成检查清单

配置完成后，确认以下内容：

- [ ] Integration 状态为 "Available"
- [ ] 可以看到 2 个 Available Actions
- [ ] Bocha 搜索工具可用
- [ ] Metaso 搜索工具可用
- [ ] Chat Agent 可以调用搜索工具
- [ ] 搜索返回正确的结果

**全部勾选后，配置即完成！** ✅

---

**配置完成后，您就拥有了一个强大的 AI Search 集成系统！** 🚀
