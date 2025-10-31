# Cloudsway AI Search Provider

Cloudsway Smart Search powered by Deepseek - 智能网页搜索，具有高级相关性评分和时间筛选功能。

## 📋 功能特点

- ✅ Deepseek 驱动的智能搜索
- ✅ 高级相关性评分
- ✅ 时间筛选（Day/Week/Month）
- ✅ 分页支持
- ✅ 中文搜索优化

## 🚀 部署

### 前置条件

1. ✅ 已完成基础设施部署（运行 `./deploy_infrastructure.sh`）
2. ✅ 拥有 Cloudsway Access Key

### 部署步骤

```bash
# 1. 进入 Cloudsway 目录
cd providers/cloudsway

# 2. 设置 Access Key
export CLOUDSWAY_ACCESS_KEY="R0qrtI7GQq6nMnZp1jgB"

# 3. 部署 Lambda 函数
./deploy.sh

# 4. 测试 Lambda
./test_lambda.sh

# 5. 添加到 Gateway
python3 add_target.py

# 6. 测试 Target
./test_target.sh

# 7. 返回项目根目录
cd ../..
```

## 📝 配置说明

### API 信息
- **Endpoint**: https://searchapi.xiaosuai.com/search/IWPdpjaJWCYtJYpX/smart
- **Method**: GET
- **Access Key**: 通过环境变量配置

### 环境变量
- `CLOUDSWAY_ACCESS_KEY`: Cloudsway Access Key（必需）
- `REGION`: AWS 区域（默认：us-east-1）

## 🎯 使用方式

### Quick Suite 中使用

**工具名称**: `CloudswayWebSearchTarget___cloudsway_smart_search`

**参数**:
- `query` (必填): 搜索查询词
- `max_results` (可选): 返回结果数量（1-50，默认10）
- `freshness` (可选): 时间筛选（Day/Week/Month）
- `offset` (可选): 分页偏移（默认0）

**示例提示词**:
```
使用 Cloudsway 搜索查找关于人工智能的最新信息
搜索最近一周的科技新闻
用 Cloudsway 查找相关性最高的技术文章
```

### API 调用格式

```json
{
  "query": "人工智能",
  "max_results": 10,
  "freshness": "Week"
}
```

### 返回格式

```
# Cloudsway Smart Search 结果

搜索词: 人工智能
共找到 X 个结果

## 1. 标题
**链接:** https://example.com
**来源:** 网站名
**发布时间:** 2025-10-30
**相关性:** 0.95
**摘要:** 内容摘要...
```

## 🧪 测试

### 测试 Lambda 函数

```bash
./test_lambda.sh
```

### 查看日志

```bash
aws logs tail /aws/lambda/CloudswayWebSearchFunction --follow --region us-east-1
```

## 🔧 维护

### 更新 Access Key

```bash
aws lambda update-function-configuration \
  --function-name CloudswayWebSearchFunction \
  --environment Variables={CLOUDSWAY_ACCESS_KEY=new-key} \
  --region us-east-1
```

### 更新 Lambda 代码

```bash
# 修改 cloudsway_lambda_function.py 后
./deploy.sh
```

## 📊 性能指标

- 响应时间: < 3秒
- 成功率: > 99%
- 结果质量: 高（包含相关性评分）

## 💰 成本

基于 1000 次搜索/月:
- Lambda: ~$0.20
- Cloudsway API: 根据订阅计划

## 🔍 适用场景

| 场景 | 适用性 |
|------|--------|
| 智能搜索 | ⭐⭐⭐⭐⭐ |
| 相关性排序 | ⭐⭐⭐⭐⭐ |
| 时间筛选 | ⭐⭐⭐⭐⭐ |
| 通用网页 | ⭐⭐⭐⭐ |
| 新闻资讯 | ⭐⭐⭐⭐ |

## 💡 使用建议

1. **智能搜索** - Cloudsway 使用 Deepseek 进行智能排序
2. **相关性评分** - 结果包含相关性分数，便于筛选
3. **时间筛选** - 使用 freshness 参数获取最近内容
4. **分页支持** - 使用 offset 参数进行分页

## 🆚 与其他 Provider 对比

| 特性 | 博查 | 秘塔 | Cloudsway |
|------|------|------|-----------|
| 智能排序 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 相关性评分 | ❌ | ❌ | ✅ |
| 时间筛选 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 学术论文 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 通用网页 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建议**:
- 需要智能排序 → 使用 Cloudsway
- 需要学术内容 → 使用秘塔
- 需要最新新闻 → 使用博查

## 📚 相关文档

- [项目 README](../../README.md)
- [Quick Suite 配置](../../QUICK_SUITE_CONFIGURATION.md)
- [架构设计](../../docs/ARCHITECTURE.md)

---

**版本**: 1.0  
**最后更新**: 2025年10月30日
