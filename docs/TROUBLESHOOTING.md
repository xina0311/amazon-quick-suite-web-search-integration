# 🔧 故障排除指南

## 已修复的问题

### ❌ 错误：`cognito-bocha-s2s.txt: line 2: ================================================: command not found`

**原因**：部署脚本尝试 `source` 配置文件时，文件中的装饰性文本被当作命令执行。

**状态**：✅ 已修复

**修复内容**：
- 更新了 `deploy_lambda.sh` 
- 更新了 `deploy_all.sh`
- 脚本现在会正确解析配置文件，跳过装饰性文本

**如果您遇到此错误**：
```bash
# 1. 清理已创建的资源
./cleanup-cognito-bocha-s2s.sh

# 2. 重新运行部署
./deploy_all.sh us-east-1
```

---

## 当前部署状态检查

您已经运行了第一步（Cognito 设置），现在可以继续：

```bash
# 进入项目目录
cd bocha-web-search-integration

# 继续部署（从 Lambda 开始）
REGION=us-east-1 ./deploy_lambda.sh

# 然后创建 Gateway
python3 create_bocha_gateway.py
```

---

## 常见问题

### 1. Token 获取失败

**症状**：
```
✗ Failed to obtain token
```

**这是正常的！** 在 Cognito 域创建后立即测试可能失败，因为：
- 域名需要几秒钟才能完全传播
- 这不影响后续部署步骤

**验证方法**：
```bash
# 等待30秒后重试
sleep 30
./test-bocha-s2s-token.sh
```

### 2. Lambda 部署失败

**症状**：
```
An error occurred (InvalidParameterValueException)
```

**解决方案**：
- IAM 角色可能需要更多时间传播
- 脚本已包含10秒等待，但某些区域可能需要更长时间

```bash
# 等待额外时间后重试
sleep 20
REGION=us-east-1 ./deploy_lambda.sh
```

### 3. Gateway 创建失败

**症状**：
```
错误: 配置文件中缺少 LAMBDA_ARN
```

**解决方案**：
```bash
# 确保 Lambda 已部署
aws lambda get-function --function-name BochaWebSearchFunction --region us-east-1

# 如果 Lambda 存在，手动添加到配置文件
LAMBDA_ARN=$(aws lambda get-function --function-name BochaWebSearchFunction --region us-east-1 --query 'Configuration.FunctionArn' --output text)
echo "LAMBDA_ARN=$LAMBDA_ARN" >> cognito-bocha-s2s.txt

# 重新运行 Gateway 创建
python3 create_bocha_gateway.py
```

### 4. 博查 API Key 配置

**确认 API Key 是否已更新**：
```bash
grep "BOCHA_API_KEY" bocha_lambda_function.py
```

**如果仍是默认值 `sk-xxxxxx`**：
```bash
# 方法 1: 直接编辑文件
nano bocha_lambda_function.py
# 修改 BOCHA_API_KEY = "your-actual-key"

# 方法 2: 使用 sed
sed -i.bak 's/sk-xxxxxx/your-actual-api-key/g' bocha_lambda_function.py

# 重新部署 Lambda
REGION=us-east-1 ./deploy_lambda.sh
```

---

## 部署步骤总结

### 完整流程（从头开始）

```bash
# 1. 清理（如果之前运行过）
./cleanup-cognito-bocha-s2s.sh 2>/dev/null || true

# 2. 设置 API Key
export BOCHA_API_KEY="your-actual-api-key"

# 3. 一键部署
./deploy_all.sh us-east-1
```

### 分步流程（当前建议）

由于您已完成 Cognito 设置，继续执行：

```bash
# 步骤 2: 配置 API Key（如果尚未配置）
export BOCHA_API_KEY="your-actual-api-key"
sed -i.bak "s/sk-xxxxxx/$BOCHA_API_KEY/g" bocha_lambda_function.py

# 步骤 3: 部署 Lambda
REGION=us-east-1 ./deploy_lambda.sh

# 步骤 4: 创建 Gateway
python3 create_bocha_gateway.py

# 步骤 5: 查看配置
cat cognito-bocha-s2s.txt | grep -E "^[A-Z_]+="
```

---

## 验证部署

### 检查 Cognito
```bash
aws cognito-idp list-user-pools --max-results 10 --region us-east-1 | grep BochaWebSearchAuthPool
```

### 检查 Lambda
```bash
aws lambda get-function --function-name BochaWebSearchFunction --region us-east-1
```

### 检查 Gateway
```bash
# Gateway ARN 应该在配置文件中
grep GATEWAY_URL cognito-bocha-s2s.txt
```

### 测试 Token
```bash
./test-bocha-s2s-token.sh
```

---

## 获取帮助

1. **查看日志**：
   ```bash
   # Lambda 日志
   aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-east-1
   ```

2. **查看完整配置**：
   ```bash
   cat cognito-bocha-s2s.txt
   ```

3. **检查脚本**：所有脚本都有详细的错误输出

---

## 清理和重试

如果需要完全重新开始：

```bash
# 1. 删除 Cognito 资源
./cleanup-cognito-bocha-s2s.sh

# 2. 删除 Lambda
aws lambda delete-function --function-name BochaWebSearchFunction --region us-east-1

# 3. 删除 IAM 角色
aws iam detach-role-policy \
  --role-name BochaLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name BochaLambdaExecutionRole

# 4. 删除本地文件
rm -f cognito-bocha-s2s.txt bocha_lambda_function.zip
rm -rf lambda_deployment

# 5. 重新开始
./deploy_all.sh us-east-1
```

---

## 下一步

部署成功后，请参考：
- [QUICKSTART.md](QUICKSTART.md) - Quick Suite 配置
- [README.md](README.md) - 详细说明
