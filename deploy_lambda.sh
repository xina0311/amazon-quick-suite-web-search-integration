#!/bin/bash
set -e

# 配置变量
REGION="${REGION:-us-west-2}"
LAMBDA_FUNCTION_NAME="BochaWebSearchFunction"
LAMBDA_ROLE_NAME="BochaLambdaExecutionRole"

echo "================================================"
echo "部署 Lambda 函数 - Bocha Web Search"
echo "Region: $REGION"
echo "================================================"

# 检查 cognito-bocha-s2s.txt 是否存在
if [ ! -f "cognito-bocha-s2s.txt" ]; then
    echo "错误: cognito-bocha-s2s.txt 文件未找到"
    echo "请先运行: ./setup_cognito_s2s_bocha.sh $REGION"
    exit 1
fi

# 加载配置（只加载有效的变量定义行）
while IFS='=' read -r key value; do
    # 只加载符合变量命名规则的行：大写字母、数字、下划线，且不包含空格
    if [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ -n "$value" ]]; then
        export "$key"="$value"
    fi
done < cognito-bocha-s2s.txt

echo ""
echo "[Step 1/5] 创建 Lambda 部署包..."

# 创建部署目录
rm -rf lambda_deployment
mkdir -p lambda_deployment
cd lambda_deployment

# 复制 Lambda 函数代码
cp ../bocha_lambda_function.py .

# 安装依赖
echo "安装 Python 依赖..."
pip install requests -t . -q

# 创建 ZIP 包
echo "创建部署包..."
zip -r ../bocha_lambda_function.zip . > /dev/null
cd ..

echo "✓ 部署包创建完成: bocha_lambda_function.zip"

echo ""
echo "[Step 2/5] 创建 Lambda IAM 角色..."

# 创建 Lambda 信任策略
cat > lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 检查角色是否已存在
if aws iam get-role --role-name $LAMBDA_ROLE_NAME --region $REGION > /dev/null 2>&1; then
    echo "✓ IAM 角色已存在: $LAMBDA_ROLE_NAME"
else
    # 创建 IAM 角色
    aws iam create-role \
      --role-name $LAMBDA_ROLE_NAME \
      --assume-role-policy-document file://lambda-trust-policy.json \
      --region $REGION > /dev/null
    
    echo "✓ IAM 角色创建成功"
fi

# 附加基本执行策略
aws iam attach-role-policy \
  --role-name $LAMBDA_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  > /dev/null 2>&1 || true

# 获取角色 ARN
LAMBDA_ROLE_ARN=$(aws iam get-role --role-name $LAMBDA_ROLE_NAME --query 'Role.Arn' --output text)
echo "✓ Lambda Role ARN: $LAMBDA_ROLE_ARN"

echo ""
echo "[Step 3/5] 等待 IAM 角色传播..."
sleep 10

echo ""
echo "[Step 4/5] 创建/更新 Lambda 函数..."

# 检查函数是否已存在
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "Lambda 函数已存在，更新代码..."
    aws lambda update-function-code \
      --function-name $LAMBDA_FUNCTION_NAME \
      --zip-file fileb://bocha_lambda_function.zip \
      --region $REGION > /dev/null
    echo "✓ Lambda 函数代码已更新"
    
    # 如果设置了 BOCHA_API_KEY 环境变量，更新 Lambda 配置
    if [ ! -z "$BOCHA_API_KEY" ]; then
        echo "更新 Lambda 环境变量..."
        aws lambda update-function-configuration \
          --function-name $LAMBDA_FUNCTION_NAME \
          --environment Variables={BOCHA_API_KEY="$BOCHA_API_KEY"} \
          --region $REGION > /dev/null
        echo "✓ Lambda 环境变量已更新"
    fi
else
    echo "创建新的 Lambda 函数..."
    
    # 准备环境变量参数
    ENV_VARS=""
    if [ ! -z "$BOCHA_API_KEY" ]; then
        ENV_VARS="--environment Variables={BOCHA_API_KEY=\"$BOCHA_API_KEY\"}"
        echo "✓ 将配置 BOCHA_API_KEY 环境变量"
    fi
    
    aws lambda create-function \
      --function-name $LAMBDA_FUNCTION_NAME \
      --runtime python3.11 \
      --role $LAMBDA_ROLE_ARN \
      --handler bocha_lambda_function.lambda_handler \
      --zip-file fileb://bocha_lambda_function.zip \
      --timeout 30 \
      --memory-size 256 \
      $ENV_VARS \
      --region $REGION > /dev/null
    echo "✓ Lambda 函数创建成功"
fi

echo ""
echo "[Step 5/5] 保存 Lambda ARN..."

# 获取 Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)
echo "✓ Lambda Function ARN: $LAMBDA_ARN"

# 检查 LAMBDA_ARN 是否已在配置文件中
if grep -q "LAMBDA_ARN=" cognito-bocha-s2s.txt; then
    # 更新现有的 ARN
    sed -i.bak "s|LAMBDA_ARN=.*|LAMBDA_ARN=$LAMBDA_ARN|" cognito-bocha-s2s.txt
else
    # 添加新的 ARN
    echo "LAMBDA_ARN=$LAMBDA_ARN" >> cognito-bocha-s2s.txt
fi

echo "✓ Lambda ARN 已保存到 cognito-bocha-s2s.txt"

# 清理
rm -f lambda-trust-policy.json
rm -f cognito-bocha-s2s.txt.bak

echo ""
echo "================================================"
echo "Lambda 部署完成！"
echo "================================================"
echo ""
echo "Lambda Function Name: $LAMBDA_FUNCTION_NAME"
echo "Lambda ARN: $LAMBDA_ARN"
echo ""
if [ -z "$BOCHA_API_KEY" ]; then
    echo "⚠ 重要提醒: BOCHA_API_KEY 环境变量未配置"
    echo "Lambda 函数需要此环境变量才能正常工作"
    echo ""
    echo "请运行以下命令配置："
    echo "  aws lambda update-function-configuration \\"
    echo "    --function-name $LAMBDA_FUNCTION_NAME \\"
    echo "    --environment Variables={BOCHA_API_KEY=your-api-key} \\"
    echo "    --region $REGION"
    echo ""
fi
echo "下一步: 运行 python create_bocha_gateway.py 创建 Gateway"
