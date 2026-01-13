# 智谱 Web Search Provider

智谱 (Zhipu) Web Search 是专为大模型优化的搜索引擎，提供多种搜索引擎选择和丰富的过滤选项。

## 📋 功能特点

- ✅ 专为大模型优化的搜索结果
- ✅ 多搜索引擎支持（标准版、专业版、搜狗、夸克）
- ✅ 时间范围过滤（一天、一周、一月、一年）
- ✅ 域名白名单过滤
- ✅ 摘要长度控制
- ✅ 搜索意图识别
- ✅ 中文搜索优化

## 🚀 部署

### 前置条件

1. ✅ 已完成基础设施部署（运行 `./deploy_infrastructure.sh`）
2. ✅ 拥有智谱 API Key

### API Key 获取

1. 访问 [智谱开放平台](https://open.bigmodel.cn/)
2. 注册账户并完成实名认证
3. 进入控制台 → API Keys → 创建新的 API Key
4. 复制 API Key 保存

### 部署步骤

```bash
# 1. 进入智谱目录
cd providers/zhipu

# 2. 设置 API Key
export ZHIPU_API_KEY="your-zhipu-api-key"

# 3. 部署 Lambda 函数
./deploy.sh

# 4. 添加到 Gateway
python3 add_target.py

# 5. 返回项目根目录
cd ../..
```

## 📝 配置说明

### 环境变量

- `ZHIPU_API_KEY`: 智谱 API Key（必需）
- `REGION`: AWS 区域（默认：us-east-1）

## 🎯 使用方式

### Quick Suite 中使用

**工具名称**: `ZhipuWebSearchTarget___zhipu_web_search`

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索关键词 |
| `max_results` | integer | ❌ | 10 | 返回结果数量 (1-50) |
| `search_engine` | string | ❌ | search_std | 搜索引擎类型 |
| `recency_filter` | string | ❌ | noLimit | 时间范围过滤 |
| `domain_filter` | array | ❌ | - | 域名白名单 |
| `content_size` | string | ❌ | medium | 摘要长度 |

### 搜索引擎类型 (search_engine)

| 值 | 说明 | 价格 |
|----|------|------|
| `search_std` | 标准版搜索 | 0.01 元/次 |
| `search_pro` | 专业版搜索 | 0.03 元/次 |
| `search_pro_sogou` | 专业版-搜狗 | 0.05 元/次 |
| `search_pro_quark` | 专业版-夸克 | 0.05 元/次 |

### 时间范围过滤 (recency_filter)

| 值 | 说明 |
|----|------|
| `oneDay` | 最近一天 |
| `oneWeek` | 最近一周 |
| `oneMonth` | 最近一月 |
| `oneYear` | 最近一年 |
| `noLimit` | 不限时间 |

### 摘要长度 (content_size)

| 值 | 说明 |
|----|------|
| `low` | 简短摘要 |
| `medium` | 中等长度 |
| `high` | 详细摘要 |

### 示例提示词

```
使用智谱搜索查找关于 AWS Lambda 的最新信息

用智谱专业版搜索人工智能的最新进展，只看最近一周的内容

使用智谱搜索查找 Amazon Bedrock 的技术文档，限定在 aws.amazon.com 域名
```

### API 调用格式

```json
{
  "query": "人工智能最新进展",
  "max_results": 10,
  "search_engine": "search_pro",
  "recency_filter": "oneWeek",
  "domain_filter": ["aws.amazon.com", "docs.aws.amazon.com"],
  "content_size": "high"
}
```

### 返回格式

```
# 智谱 Web Search 结果

**搜索意图:** 信息查询
**优化关键词:** AI 人工智能 最新进展 2025

共找到 10 个结果

## 1. 标题
**链接:** https://example.com
**来源:** 媒体名称
**发布日期:** 2025-01-10
**摘要:** 内容摘要...

## 2. 标题
...
```

## 🧪 测试

### 测试 Lambda 函数

```bash
cd providers/zhipu
./test_lambda.sh
```

### 测试 Gateway Target

```bash
cd providers/zhipu
./test_target.sh
```

### 手动测试

```bash
aws lambda invoke \
  --function-name ZhipuWebSearchFunction \
  --region us-east-1 \
  --payload '{"query": "人工智能", "max_results": 3}' \
  test_response.json

cat test_response.json
```

### 查看日志

```bash
aws logs tail /aws/lambda/ZhipuWebSearchFunction --follow --region us-east-1
```

## 🔧 维护

### 更新 API Key

```bash
aws lambda update-function-configuration \
  --function-name ZhipuWebSearchFunction \
  --environment Variables={ZHIPU_API_KEY=new-key} \
  --region us-east-1
```

### 更新 Lambda 代码

```bash
# 修改 zhipu_lambda_function.py 后
./deploy.sh
```

### 删除部署

```bash
# 删除 Lambda 函数
aws lambda delete-function \
  --function-name ZhipuWebSearchFunction \
  --region us-east-1

# 删除 IAM 角色
aws iam detach-role-policy \
  --role-name ZhipuLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name ZhipuLambdaExecutionRole

# 删除 Gateway Target（通过 AWS Console 或 API）
```

## 📊 性能指标

- 响应时间: < 3秒
- 成功率: > 99%
- 结果质量: 高（专为大模型优化）

## 💰 成本估算

基于 1000 次搜索/月:

| 搜索引擎 | API 成本 | Lambda 成本 | 总计 |
|----------|----------|-------------|------|
| search_std | ¥10 | ~$0.30 | ~¥12 |
| search_pro | ¥30 | ~$0.30 | ~¥32 |
| search_pro_sogou | ¥50 | ~$0.30 | ~¥52 |
| search_pro_quark | ¥50 | ~$0.30 | ~¥52 |

## 🔍 与其他 Provider 对比

| 特性 | 智谱 | 博查 | 秘塔 |
|------|------|------|------|
| 搜索引擎选择 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 时间过滤 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 域名过滤 | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| 摘要控制 | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| 搜索意图识别 | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ |
| 学术论文 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 新闻资讯 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 价格 | 中等 | 低 | 中等 |

### 适用场景推荐

| 场景 | 推荐 Provider |
|------|---------------|
| 需要精确时间过滤 | 智谱 |
| 需要限定特定网站 | 智谱 |
| 新闻资讯搜索 | 博查 |
| 学术论文搜索 | 秘塔 |
| 多媒体内容搜索 | 秘塔 |
| 通用网页搜索 | 智谱/博查 |

## 🐛 故障排除

### Lambda 部署失败

**检查步骤**:
1. 确认 IAM 权限
2. 检查区域设置
3. 验证 API Key 格式

### 搜索返回错误

**常见错误**:

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 401 Unauthorized | API Key 无效 | 检查 API Key 是否正确 |
| 400 Bad Request | 参数错误 | 检查参数格式 |
| 429 Too Many Requests | 请求过于频繁 | 降低请求频率 |
| 500 Internal Error | 服务端错误 | 稍后重试 |

**检查步骤**:
1. 查看 Lambda 日志
2. 验证 API Key 有效性
3. 检查 API 额度

### Target 添加失败

**检查步骤**:
1. 确认 Gateway 已创建
2. 检查 Lambda ARN
3. 查看详细错误信息

## 📚 相关文档

- [项目主 README](../../README.md)
- [Quick Suite 配置](../../docs/QUICK_SUITE_SETUP.md)
- [架构设计](../../docs/ARCHITECTURE.md)

## 🔗 外部链接

- [智谱开放平台](https://open.bigmodel.cn/)
- [智谱 Web Search API 文档](https://docs.bigmodel.cn/cn/guide/tools/web-search)

---

**版本**: 1.0  
**最后更新**: 2026年1月13日
