# Requirements Document

## Introduction

本文档定义了将智谱 (Zhipu) Web Search API 集成到 Amazon Quick Suite AI Search Integration 项目的需求。智谱是国内领先的 AI 大模型公司，其 Web Search API 专为大模型优化，能够返回更适合 AI Agent 处理的搜索结果。

智谱 Web Search 的特点：
- 专为大模型设计的搜索引擎
- 增强的意图识别能力
- 返回结构化的搜索结果（标题、URL、摘要、来源、发布日期等）
- 支持多种搜索引擎和时间范围过滤

## Glossary

- **Zhipu_Provider**: 智谱搜索服务的 Lambda 函数实现，负责接收 Gateway 请求并调用智谱 API
- **Gateway_Target**: AgentCore Gateway 中配置的智谱搜索目标，用于路由搜索请求
- **MCP_Tool**: Model Context Protocol 工具定义，描述工具的输入输出 schema
- **Search_Engine**: 智谱支持的搜索引擎类型（search-std 标准版, search-pro 专业版, search-pro-sogou 搜狗版, search-pro-quark 夸克版）
- **Recency_Filter**: 时间范围过滤器（oneDay, oneWeek, oneMonth, oneYear, noLimit）
- **Config_File**: 项目配置文件 config.txt，存储 Gateway ARN、Lambda ARN 等配置信息

## Requirements

### Requirement 1: Lambda 函数部署

**User Story:** As a developer, I want to deploy a Lambda function for Zhipu Web Search, so that I can process search requests through AgentCore Gateway.

#### Acceptance Criteria

1. THE Zhipu_Provider SHALL be deployable as an AWS Lambda function with Python 3.9+ runtime
2. WHEN the Lambda function is deployed, THE Zhipu_Provider SHALL read the API key from the ZHIPU_API_KEY environment variable
3. IF the ZHIPU_API_KEY environment variable is not set, THEN THE Zhipu_Provider SHALL raise a clear error message at startup
4. THE Zhipu_Provider SHALL include the requests library as a dependency
5. THE Zhipu_Provider SHALL be configured with 30-second timeout and 256MB memory

### Requirement 2: 搜索请求处理

**User Story:** As a Quick Suite user, I want to search using Zhipu Web Search, so that I can get AI-optimized search results.

#### Acceptance Criteria

1. WHEN a search request is received with a query parameter, THE Zhipu_Provider SHALL call the Zhipu Web Search API
2. WHEN the query parameter is empty or missing, THE Zhipu_Provider SHALL return an error response with status code 400
3. THE Zhipu_Provider SHALL support the following optional parameters:
   - max_results (count): 返回结果数量（1-50，默认 10）
   - search_engine: 搜索引擎类型，支持以下值：
     - search_std: 基础版（智谱自研），0.01元/次
     - search_pro: 高级版（智谱自研），多引擎协作，0.03元/次
     - search_pro_sogou: 搜狗版，覆盖腾讯生态和知乎，0.05元/次
     - search_pro_quark: 夸克版，精准垂直内容，0.05元/次
   - recency_filter: 时间范围过滤（oneDay, oneWeek, oneMonth, oneYear, noLimit，默认 noLimit）
   - domain_filter: 域名白名单过滤，限定搜索范围（可选）
   - content_size: 摘要字数控制（low, medium, high，默认 medium）
4. WHEN max_results is outside the valid range (1-50), THE Zhipu_Provider SHALL use the default value of 10
5. WHEN an invalid search_engine value is provided, THE Zhipu_Provider SHALL use the default value search_std
6. WHEN an invalid recency_filter value is provided, THE Zhipu_Provider SHALL use the default value noLimit
7. WHEN an invalid content_size value is provided, THE Zhipu_Provider SHALL use the default value medium

### Requirement 3: API 调用

**User Story:** As a system integrator, I want the Lambda to correctly call Zhipu API, so that search requests are properly processed.

#### Acceptance Criteria

1. THE Zhipu_Provider SHALL call the endpoint https://open.bigmodel.cn/api/paas/v4/web_search using POST method
2. THE Zhipu_Provider SHALL include the Authorization header with Bearer token format
3. THE Zhipu_Provider SHALL set Content-Type header to application/json
4. THE Zhipu_Provider SHALL set a 30-second timeout for API requests
5. WHEN the API returns an error response, THE Zhipu_Provider SHALL return an error with the original error message and status code
6. WHEN the API request times out, THE Zhipu_Provider SHALL return a timeout error response with clear message

### Requirement 4: 结果格式化

**User Story:** As a Quick Suite user, I want search results formatted in readable Markdown, so that I can easily understand the search results.

#### Acceptance Criteria

1. WHEN search results are received, THE Zhipu_Provider SHALL format them as Markdown text
2. THE Zhipu_Provider SHALL include the following fields for each result:
   - title: 网页标题
   - link: 网页 URL
   - content: 内容摘要
   - media: 来源网站名称
   - icon: 网站图标 URL（如有）
   - publish_date: 发布日期（如有）
3. WHEN the API returns search_intent, THE Zhipu_Provider SHALL display the recognized intent and rewritten keywords
4. WHEN no results are found, THE Zhipu_Provider SHALL return a message indicating "未找到相关结果"
5. THE Zhipu_Provider SHALL return results in MCP-compatible format with content array containing text type
6. THE Zhipu_Provider SHALL display the total number of results found

### Requirement 5: Gateway Target 配置

**User Story:** As a developer, I want to register Zhipu as a Gateway Target, so that Quick Suite can discover and use the search tool.

#### Acceptance Criteria

1. THE Gateway_Target SHALL be named ZhipuWebSearchTarget
2. THE MCP_Tool SHALL be named zhipu_web_search
3. THE MCP_Tool SHALL have description: "智谱 Web Search - 专为大模型优化的搜索引擎，支持多种搜索引擎（基础版/高级版/搜狗/夸克）和时间范围过滤，具有增强的意图识别能力"
4. THE MCP_Tool SHALL define input schema with:
   - query (string, required): 搜索查询关键词
   - max_results (integer, optional): 返回结果数量（1-50，默认10）
   - search_engine (string, optional): 搜索引擎类型（search_std/search_pro/search_pro_sogou/search_pro_quark）
   - recency_filter (string, optional): 时间范围过滤（oneDay/oneWeek/oneMonth/oneYear/noLimit）
   - domain_filter (string, optional): 域名白名单过滤
   - content_size (string, optional): 摘要字数控制（low/medium/high）
5. WHEN the target is created, THE Gateway_Target SHALL use GATEWAY_IAM_ROLE for credential provider

### Requirement 6: 部署脚本

**User Story:** As a developer, I want deployment scripts, so that I can easily deploy and configure the Zhipu provider.

#### Acceptance Criteria

1. THE deploy.sh script SHALL check for ZHIPU_API_KEY environment variable before deployment
2. THE deploy.sh script SHALL create IAM role ZhipuLambdaExecutionRole if not exists
3. THE deploy.sh script SHALL package the Lambda code with requests dependency
4. THE deploy.sh script SHALL create or update Lambda function ZhipuWebSearchFunction
5. THE deploy.sh script SHALL save ZHIPU_LAMBDA_ARN to config.txt
6. THE add_target.py script SHALL read GATEWAY_ARN and REGION from config.txt
7. THE add_target.py script SHALL create or update the Gateway Target
8. WHEN the target already exists, THE add_target.py script SHALL update it instead of failing
9. THE add_target.py script SHALL save ZHIPU_TARGET_ID to config.txt

### Requirement 7: 测试脚本

**User Story:** As a developer, I want test scripts, so that I can verify the deployment is working correctly.

#### Acceptance Criteria

1. THE test_lambda.sh script SHALL invoke the Lambda function with a test query
2. THE test_lambda.sh script SHALL display the response in readable format
3. THE test_target.sh script SHALL test the Gateway Target end-to-end
4. WHEN tests fail, THE scripts SHALL display clear error messages

### Requirement 8: 文档

**User Story:** As a developer, I want comprehensive documentation, so that I can understand how to deploy and use the Zhipu provider.

#### Acceptance Criteria

1. THE README.md SHALL include an overview of Zhipu Web Search capabilities and features
2. THE README.md SHALL include API Key 获取说明
3. THE README.md SHALL include step-by-step deployment instructions
4. THE README.md SHALL include all supported parameters and their descriptions
5. THE README.md SHALL include example usage prompts for Quick Suite
6. THE README.md SHALL include troubleshooting guidance for common issues
7. THE README.md SHALL include comparison with other providers (博查、秘塔)
8. THE README.md SHALL include cost estimation
