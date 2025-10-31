# 秘塔 AI Search Provider

秘塔 (Metaso) 是一个强大的多类型搜索引擎，特别擅长学术论文和技术文档搜索。

## 📋 功能特点

- ✅ 6 种搜索类型（网页、文档、论文、图片、视频、播客）
- ✅ 学术论文搜索优化
- ✅ 技术文档专项搜索
- ✅ 多媒体内容支持
- ✅ 高级搜索选项

## 🎯 搜索范围

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| webpage | 网页搜索 | 通用信息查询、新闻资讯 |
| document | 文档搜索 | 技术文档、说明书、报告 |
| paper | 论文搜索 | 学术研究、科研资料 ⭐ |
| image | 图片搜索 | 图像资源、视觉内容 |
| video | 视频搜索 | 视频教程、演示内容 |
| podcast | 播客搜索 | 音频内容、访谈节目 |

## 🚀 部署

### 前置条件

1. ✅ 已完成基础设施部署（运行 `./deploy_infrastructure.sh`）
2. ✅ 拥有秘塔 API Key

### 部署步骤

```bash
# 1. 进入秘塔目录
cd providers/metaso

# 2. 设置 API Key
export METASO_API_KEY="your-metaso-api-key"

# 3. 部署 Lambda 函数
./deploy.sh

# 4. 添加到 Gateway
python3 add_target.py

# 5. 返回项目根目录
cd ../..
```

## 📝 配置说明

### API Key 获取

1. 访问秘塔 AI 官网
2. 注册账户并创建应用
3. 获取 API Key

### 环境变量

- `METASO_API_KEY`: 秘塔 API Key（必需）
- `REGION`: AWS 区域（默认：us-east-1）

## 🎯 使用方式

### Quick Suite 中使用

**工具名称**: `MetasoWebSearchTarget___metaso_web_search`

**参数**:
- `query` (必填): 搜索关键词
- `scope` (可选): 搜索范围，可选值：
  - `webpage` - 网页（默认）
  - `document` - 文档
  - `paper` - 论文
  - `image` - 图片
  - `video` - 视频
  - `podcast` - 播客
- `max_results` (可选): 返回结果数量 (1-50，默认 10)
- `include_summary` (可选): 提升召回率（布尔值，默认 false）
- `include_raw_content` (可选): 获取原文（布尔值，默认 false）
- `concise_snippet` (可选): 简洁摘要（布尔值，默认 false）

**示例提示词**:

基础搜索：
```
使用秘塔搜索查找关于人工智能的最新信息
```

论文搜索：
```
用秘塔搜索一下量子计算的学术论文
```

文档搜索：
```
搜索机器学习相关的技术文档
```

多媒体搜索：
```
用秘塔搜索深度学习的教学视频
```

### API 调用格式

**基本网页搜索**:
```json
{
  "query": "人工智能最新进展",
  "scope": "webpage",
  "max_results": 10
}
```

**学术论文搜索**:
```json
{
  "query": "quantum computing algorithms",
  "scope": "paper",
  "max_results": 5,
  "include_summary": true
}
```

**技术文档搜索**:
```json
{
  "query": "Python async programming",
  "scope": "document",
  "max_results": 10,
  "concise_snippet": true
}
```

### 返回格式

```
# 秘塔 AI Search - [类型]搜索结果

共找到 X 个结果

## 1. 标题
**链接:** https://example.com
**作者:** 作者名（如适用）
**日期:** 日期（如适用）
**摘要:** 内容摘要...

## 2. 标题
...
```

## 🧪 测试

### 测试 Lambda 函数

**网页搜索**:
```bash
aws lambda invoke \
  --function-name MetasoWebSearchFunction \
  --region us-east-1 \
  --payload '{"query": "人工智能", "scope": "webpage", "max_results": 3}' \
  webpage_response.json
```

**论文搜索**:
```bash
aws lambda invoke \
  --function-name MetasoWebSearchFunction \
  --region us-east-1 \
  --payload '{"query": "deep learning", "scope": "paper", "max_results": 3}' \
  paper_response.json
```

### 查看日志

```bash
aws logs tail /aws/lambda/MetasoWebSearchFunction --follow --region us-east-1
```

## 🔧 维护

### 更新 API Key

```bash
aws lambda update-function-configuration \
  --function-name MetasoWebSearchFunction \
  --environment Variables={METASO_API_KEY=new-key} \
  --region us-east-1
```

### 更新 Lambda 代码

```bash
# 修改 metaso_lambda_function.py 后
./deploy.sh
```

### 删除部署

```bash
# 删除 Lambda 函数
aws lambda delete-function \
  --function-name MetasoWebSearchFunction \
  --region us-east-1

# 删除 IAM 角色
aws iam detach-role-policy \
  --role-name MetasoLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name MetasoLambdaExecutionRole

# 删除 Gateway Target
# 需要通过 AWS Console 或 API 手动删除
```

## 📊 性能指标

- 响应时间: < 3秒
- 成功率: > 99%
- 结果质量: 非常高（特别是学术内容）

## 💰 成本

基于 1000 次搜索/月:
- Lambda: ~$0.20
- 秘塔 API: 根据订阅计划

## 🔍 适用场景

| 场景 | 适用性 |
|------|--------|
| 学术论文 | ⭐⭐⭐⭐⭐ |
| 技术文档 | ⭐⭐⭐⭐⭐ |
| 通用网页 | ⭐⭐⭐⭐ |
| 新闻资讯 | ⭐⭐⭐ |
| 图片/视频 | ⭐⭐⭐⭐ |

## 💡 使用建议

### 选择合适的搜索范围

1. **学术研究** → 使用 `paper`
   - 返回作者、年份、期刊等信息
   - 学术资源质量高

2. **技术学习** → 使用 `document`
   - 专门的文档类型筛选
   - 技术内容准确

3. **多媒体内容** → 使用 `video` 或 `image`
   - 专门的类型筛选
   - 内容更加精准

4. **通用查询** → 使用 `webpage`
   - 覆盖面广
   - 适合一般信息查询

### 优化搜索结果

- 使用 `include_summary=true` 提升召回率
- 使用 `concise_snippet=true` 获取简洁摘要
- 合理设置 `max_results` 数量

## 🐛 故障排除

### Lambda 部署失败

**检查步骤**:
1. 确认 IAM 权限
2. 检查区域设置
3. 验证 API Key

### 搜索返回错误

**检查步骤**:
1. 查看 Lambda 日志
2. 验证 API Key 有效性
3. 检查 scope 参数是否正确
4. 确认 API 额度

### Target 添加失败

**检查步骤**:
1. 确认 Gateway 已创建
2. 检查 Lambda ARN
3. 查看详细错误信息

### 响应格式异常

**可能原因**:
- 秘塔 API 响应格式变化
- Lambda 函数需要更新

**解决方案**:
1. 查看 Lambda 日志中的原始响应
2. 更新 `metaso_lambda_function.py` 中的格式化逻辑
3. 重新部署

## 📚 相关文档

- [项目主 README](../../README.md)
- [Quick Suite 配置](../../docs/QUICK_SUITE_SETUP.md)
- [架构设计](../../docs/ARCHITECTURE.md)
- [完整集成指南](../../METASO_INTEGRATION.md)

## 🔗 外部链接

- [秘塔 AI 官网](https://metaso.cn/)
- 秘塔 API 文档（请联系秘塔获取）

## 🆚 与博查对比

| 特性 | 博查 | 秘塔 |
|------|------|------|
| 通用网页搜索 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 学术论文搜索 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 技术文档搜索 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 图片/视频搜索 | ❌ | ⭐⭐⭐⭐ |
| 搜索范围选项 | 单一 | 6种类型 |
| 高级选项 | 有限 | 丰富 |

**建议**:
- 新闻资讯 → 使用博查
- 学术研究 → 使用秘塔
- 技术文档 → 使用秘塔
- 通用查询 → 两者均可

---

**版本**: 1.0  
**最后更新**: 2025年10月30日
