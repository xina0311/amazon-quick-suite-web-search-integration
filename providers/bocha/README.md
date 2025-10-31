# 博查 Web Search Provider

博查 (Bocha) 是一个实时网页搜索服务，特别适合查找最新资讯和新闻内容。

## 📋 功能特点

- ✅ 实时网页搜索
- ✅ 新闻资讯覆盖全面
- ✅ 中文搜索优化
- ✅ 快速响应
- ✅ 结果质量高

## 🚀 部署

### 前置条件

1. ✅ 已完成基础设施部署（运行 `./deploy_infrastructure.sh`）
2. ✅ 拥有博查 API Key

### 部署步骤

```bash
# 1. 进入博查目录
cd providers/bocha

# 2. 设置 API Key
export BOCHA_API_KEY="your-bocha-api-key"

# 3. 部署 Lambda 函数
./deploy.sh

# 4. 添加到 Gateway
python3 add_target.py

# 5. 返回项目根目录
cd ../..
```

## 📝 配置说明

### API Key 获取

1. 访问博查开放平台
2. 注册账户并创建应用
3. 获取 API Key

### 环境变量

- `BOCHA_API_KEY`: 博查 API Key（必需）
- `REGION`: AWS 区域（默认：us-east-1）

## 🎯 使用方式

### Quick Suite 中使用

**工具名称**: `BochaWebSearchTarget___bocha_web_search`

**参数**:
- `query` (必填): 搜索关键词
- `max_results` (可选): 返回结果数量 (1-50，默认 10)

**示例提示词**:
```
使用博查搜索查找关于 AWS Lambda 的最新信息
搜索一下人工智能的新闻资讯
用博查查找 Amazon Bedrock 的相关内容
```

### API 调用格式

```json
{
  "query": "搜索关键词",
  "max_results": 10
}
```

### 返回格式

```
# 博查 Web Search 结果

共找到 X 个结果

## 1. 标题
**链接:** https://example.com
**摘要:** 内容摘要...

## 2. 标题
...
```

## 🧪 测试

### 测试 Lambda 函数

```bash
aws lambda invoke \
  --function-name BochaWebSearchFunction \
  --region us-east-1 \
  --payload '{"query": "测试", "max_results": 3}' \
  test_response.json

cat test_response.json
```

### 查看日志

```bash
aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-east-1
```

## 🔧 维护

### 更新 API Key

```bash
aws lambda update-function-configuration \
  --function-name BochaWebSearchFunction \
  --environment Variables={BOCHA_API_KEY=new-key} \
  --region us-east-1
```

### 更新 Lambda 代码

```bash
# 修改 bocha_lambda_function.py 后
./deploy.sh
```

### 删除部署

```bash
# 删除 Lambda 函数
aws lambda delete-function \
  --function-name BochaWebSearchFunction \
  --region us-east-1

# 删除 IAM 角色
aws iam detach-role-policy \
  --role-name BochaLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name BochaLambdaExecutionRole

# 删除 Gateway Target
# 需要通过 AWS Console 或 API 手动删除
```

## 📊 性能指标

- 响应时间: < 3秒
- 成功率: > 99%
- 结果质量: 高

## 💰 成本

基于 1000 次搜索/月:
- Lambda: ~$0.20
- 博查 API: 根据订阅计划

## 🔍 适用场景

| 场景 | 适用性 |
|------|--------|
| 新闻资讯 | ⭐⭐⭐⭐⭐ |
| 最新动态 | ⭐⭐⭐⭐⭐ |
| 通用网页 | ⭐⭐⭐⭐ |
| 学术论文 | ⭐⭐ |
| 技术文档 | ⭐⭐⭐ |

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

- [博查开放平台](https://open.bochaai.com/)
- [博查 API 文档](https://aq6ky2b8nql.feishu.cn/wiki/HmtOw1z6vik14Fkdu5uc9VaInBb)

---

**版本**: 1.0  
**最后更新**: 2025年10月30日
