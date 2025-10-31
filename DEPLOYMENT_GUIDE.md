# 部署指南 - 完整步骤

本文档提供完整的部署步骤和注意事项。

## ⚠️ 重要注意事项

### 1. API Key 管理
**所有 API Keys 必须通过环境变量配置，不要硬编码在代码中！**

```bash
# 博查 API Key
export BOCHA_API_KEY="your-bocha-api-key"

# 秘塔 API Key  
export METASO_API_KEY="your-metaso-api-key"
```

### 2. 配置文件说明
- **cognito-bocha-s2s.txt** - 在 utils/ 目录中生成（Cognito 配置）
- **config.txt** - 在项目根目录（统一配置，包含 Gateway 信息）

### 3. 当前已知问题
- setup_cognito.sh 生成的配置文件在 utils/ 目录
- deploy_infrastructure.sh 需要正确复制到根目录
- 部署脚本需要检查相对路径

## 🚀 完整部署流程

### 步骤 0: 准备工作

```bash
# 克隆项目
git clone <repository-url>
cd amazon-quick-suite-web-search-integration

# 检查前置条件
aws --version
python3 --version
jq --version

# 配置 AWS 凭证
aws configure
```

### 步骤 0.1: 创建 Python 虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python3 -c "import boto3, requests; print('✓ 依赖安装成功')"
```

**注意**: 后续所有操作都应该在激活的虚拟环境中执行。

### 步骤 1: 部署基础设施

```bash
# 给予执行权限
chmod +x deploy_infrastructure.sh

# 部署 Cognito 和 Gateway
./deploy_infrastructure.sh us-east-1
```

**预期结果**:
- ✅ Cognito User Pool 创建成功
- ✅ AgentCore Gateway 创建成功
- ✅ config.txt 文件生成在项目根目录

**如果失败**:
- 检查 utils/ 目录下是否有 cognito-bocha-s2s.txt
- 手动复制: `cp utils/cognito-bocha-s2s.txt config.txt`
- 继续下一步

### 步骤 2: 部署博查 Provider（可选）

```bash
cd providers/bocha

# 1. 设置 API Key（必需）
export BOCHA_API_KEY="your-bocha-api-key"

# 2. 给予执行权限
chmod +x deploy.sh test_lambda.sh test_target.sh add_target.py

# 3. 部署 Lambda
./deploy.sh

# 4. 测试 Lambda（推荐）
./test_lambda.sh

# 5. 添加到 Gateway
python3 add_target.py

# 6. 测试 Gateway Target（推荐）
./test_target.sh

# 返回根目录
cd ../..
```

### 步骤 3: 部署秘塔 Provider（可选）

```bash
cd providers/metaso

# 1. 设置 API Key（必需）
export METASO_API_KEY="your-metaso-api-key"

# 2. 给予执行权限
chmod +x deploy.sh test_lambda.sh test_target.sh add_target.py

# 3. 部署 Lambda
./deploy.sh

# 4. 测试 Lambda（推荐）
./test_lambda.sh

# 5. 添加到 Gateway
python3 add_target.py

# 6. 测试 Gateway Target（推荐）
./test_target.sh

# 返回根目录
cd ../..
```

### 步骤 4: 配置 Amazon Quick Suite

参考 [docs/QUICK_SUITE_SETUP.md](docs/QUICK_SUITE_SETUP.md) 进行配置。

## 📝 测试说明

### Lambda 测试
每个 Provider 都有独立的测试脚本：

**博查测试**:
```bash
cd providers/bocha
./test_lambda.sh
```

**秘塔测试**:
```bash
cd providers/metaso
./test_lambda.sh
```

**测试内容**:
1. 检查 Lambda 函数是否存在
2. 检查 API Key 是否已配置
3. 调用 Lambda 函数进行实际搜索
4. 验证响应格式

### Gateway Target 测试
确认 Lambda 已成功添加到 Gateway：

**博查 Target 测试**:
```bash
cd providers/bocha
./test_target.sh
```

**秘塔 Target 测试**:
```bash
cd providers/metaso
./test_target.sh
```

**测试内容**:
1. 检查 Gateway 状态
2. 验证 Target 已添加
3. 列出可用的工具
4. 运行集成测试

## 🔧 问题排查

### 问题 1: 基础设施部署失败

**症状**: deploy_infrastructure.sh 提示"配置文件未生成"

**解决方案**:
```bash
# 检查 utils/ 目录
ls -la utils/

# 如果存在 cognito-bocha-s2s.txt
cp utils/cognito-bocha-s2s.txt config.txt

# 继续部署 Gateway
cd utils
python3 create_gateway.py
cd ..
```

### 问题 2: Lambda 部署时提示 API Key 未设置

**解决方案**:
```bash
# 设置环境变量
export BOCHA_API_KEY="your-api-key"
export METASO_API_KEY="your-api-key"

# 重新部署
./deploy.sh
```

### 问题 3: Lambda 测试失败

**可能原因**:
- API Key 未配置
- API Key 无效
- 网络问题

**解决方案**:
```bash
# 检查 API Key 配置
aws lambda get-function-configuration \
  --function-name BochaWebSearchFunction \
  --query 'Environment.Variables.BOCHA_API_KEY'

# 查看 Lambda 日志
aws logs tail /aws/lambda/BochaWebSearchFunction --follow
```

### 问题 4: Target 测试失败

**可能原因**:
- Gateway 未创建
- Target 未添加
- config.txt 文件不存在

**解决方案**:
```bash
# 检查 config.txt
cat config.txt

# 检查 Gateway Targets
aws bedrock-agentcore-control list-gateway-targets \
  --gateway-identifier $(grep GATEWAY_ARN config.txt | cut -d'=' -f2)
```

## 📚 配置文件说明

### config.txt（项目根目录）

包含所有配置信息：
```
POOL_ID=<Cognito User Pool ID>
REGION=<AWS Region>
CLIENT_ID=<App Client ID>
CLIENT_SECRET=<App Client Secret>
TOKEN_ENDPOINT=<OAuth Token URL>
DISCOVERY_URL=<OIDC Discovery URL>
GATEWAY_ARN=<Gateway ARN>
GATEWAY_ID=<Gateway ID>
GATEWAY_URL=<Gateway Endpoint URL>

# Provider 特定配置
BOCHA_TARGET_ID=<Bocha Target ID>
BOCHA_LAMBDA_ARN=<Bocha Lambda ARN>
METASO_TARGET_ID=<Metaso Target ID>
METASO_LAMBDA_ARN=<Metaso Lambda ARN>
```

### 环境变量（不保存在文件中）

```bash
# 博查 API Key
export BOCHA_API_KEY="your-bocha-api-key"

# 秘塔 API Key
export METASO_API_KEY="your-metaso-api-key"
```

## ✅ 部署检查清单

### 基础设施
- [ ] Cognito User Pool 创建成功
- [ ] AgentCore Gateway 创建成功
- [ ] config.txt 文件存在且包含所有必需配置

### 博查 Provider（如需部署）
- [ ] BOCHA_API_KEY 环境变量已设置
- [ ] Lambda 函数部署成功
- [ ] Lambda 测试通过（test_lambda.sh）
- [ ] Gateway Target 添加成功
- [ ] Target 测试通过（test_target.sh）

### 秘塔 Provider（如需部署）
- [ ] METASO_API_KEY 环境变量已设置
- [ ] Lambda 函数部署成功
- [ ] Lambda 测试通过（test_lambda.sh）
- [ ] Gateway Target 添加成功
- [ ] Target 测试通过（test_target.sh）

### Quick Suite 配置
- [ ] MCP Integration 创建成功
- [ ] 状态显示为 Available
- [ ] 可以看到已部署的工具
- [ ] 测试提示词返回正确结果

## 🎯 最佳实践

1. **先部署基础设施，再部署 Providers**
2. **每部署一个组件后，立即测试**
3. **API Keys 通过环境变量管理，不要硬编码**
4. **使用测试脚本验证每一步**
5. **保管好 config.txt 文件，不要提交到 Git**

## 📞 获取帮助

如遇问题：
1. 查看 [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. 查看对应 Provider 的 README
3. 运行测试脚本诊断问题
4. 查看 CloudWatch 日志

---

**版本**: 2.0  
**最后更新**: 2025年10月30日
