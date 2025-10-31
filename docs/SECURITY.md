# Security Guidelines

## 重要安全说明

本项目已配置为不包含任何硬编码的敏感信息。在部署前，请仔细阅读以下安全指南。

## 敏感信息管理

### 1. Bocha API Key 配置

**Lambda 函数不再包含硬编码的 API Key**。您必须通过 AWS Lambda 环境变量配置：

```bash
# 在 Lambda 控制台或通过 AWS CLI 设置环境变量
aws lambda update-function-configuration \
  --function-name BochaWebSearchFunction \
  --environment Variables={BOCHA_API_KEY=your-api-key-here} \
  --region us-west-2
```

或者在部署脚本中添加：

```bash
# 在 deploy_lambda.sh 中创建/更新函数时添加
aws lambda create-function \
  --function-name $LAMBDA_FUNCTION_NAME \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler bocha_lambda_function.lambda_handler \
  --zip-file fileb://bocha_lambda_function.zip \
  --environment Variables={BOCHA_API_KEY=your-bocha-api-key} \
  --timeout 30 \
  --memory-size 256 \
  --region $REGION
```

### 2. 自动生成的敏感文件

以下文件由脚本自动生成，包含敏感信息，**已添加到 .gitignore**：

- `cognito-bocha-s2s.txt` - 包含 Cognito 配置和 API 密钥
- `cleanup-cognito-bocha-s2s.sh` - 清理脚本
- `test-bocha-s2s-token.sh` - 测试脚本
- `bocha_lambda_function.zip` - Lambda 部署包
- `lambda_deployment/` - 临时部署目录

### 3. 配置文件模板

使用 `env.example` 作为模板创建您的本地配置：

```bash
cp env.example .env
# 编辑 .env 文件，填入您的实际配置
```

**注意**: `.env` 文件已添加到 .gitignore，不会被提交到版本控制。

## 部署前检查清单

在部署或提交代码前，请确认：

- [ ] 没有硬编码的 API Keys 或密钥
- [ ] 所有敏感配置都通过环境变量管理
- [ ] `.gitignore` 包含所有敏感文件
- [ ] 运行 `git status` 确认没有敏感文件被跟踪
- [ ] 检查提交历史，确保之前没有提交过敏感信息

## 检查命令

```bash
# 检查是否有敏感文件未被 ignore
git status

# 搜索可能的硬编码 API Keys（示例模式）
grep -r "sk-[a-zA-Z0-9]" --exclude-dir=.git --exclude="*.md"
grep -r "secret" --exclude-dir=.git --exclude="*.md" | grep -i "="

# 确认 .gitignore 生效
git check-ignore cognito-bocha-s2s.txt
```

## AWS IAM 权限最佳实践

### Lambda 执行角色

Lambda 函数应该只有必要的权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### Gateway 角色

Gateway 角色应限制为特定资源：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:region:account:function:BochaWebSearchFunction"
    }
  ]
}
```

## Cognito 安全配置

- 定期轮换 Client Secrets
- 使用短期访问令牌（建议 1 小时过期）
- 限制允许的 OAuth scopes
- 启用 MFA（如果需要用户身份验证）

## 应急响应

如果意外泄露了敏感信息：

1. **立即撤销泄露的凭证**
   ```bash
   # 撤销 Bocha API Key - 登录 Bocha 控制台
   # 删除 Cognito User Pool
   aws cognito-idp delete-user-pool --user-pool-id POOL_ID --region REGION
   ```

2. **从 Git 历史中移除敏感信息**
   ```bash
   # 使用 git-filter-repo 或 BFG Repo-Cleaner
   # 参考: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
   ```

3. **生成新的凭证并更新配置**

4. **通知相关团队成员**

## 监控和审计

- 启用 AWS CloudTrail 记录 API 调用
- 监控 Lambda 函数日志
- 设置异常访问警报
- 定期审查 IAM 权限

## 参考资源

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
