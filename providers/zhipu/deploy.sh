#!/bin/bash

# 智谱 Web Search Lambda 函数部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置变量
FUNCTION_NAME="ZhipuWebSearchFunction"
REGION="${REGION:-us-east-1}"
ROLE_NAME="ZhipuLambdaExecutionRole"
ZHIPU_API_KEY="${ZHIPU_API_KEY}"

# 检查 API Key
if [ -z "$ZHIPU_API_KEY" ]; then
    echo -e "${RED}错误: ZHIPU_API_KEY 环境变量未设置${NC}"
    echo ""
    echo "请先设置 API Key:"
    echo "  export ZHIPU_API_KEY=\"your-zhipu-api-key\""
    echo ""
    echo "API Key 获取方式:"
    echo "  1. 访问 https://open.bigmodel.cn/"
    echo "  2. 注册/登录账户"
    echo "  3. 在控制台获取 API Key"
    echo ""
    echo "然后重新运行部署脚本"
    exit 1
fi

echo "================================================"
echo "智谱 Web Search Lambda 函数部署"
echo "================================================"
echo ""
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

# 检查配置文件是否存在
CONFIG_FILE="../../config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 配置文件 $CONFIG_FILE 未找到${NC}"
    echo "请先运行基础设施部署: ./deploy_infrastructure.sh"
    exit 1
fi

# 检查必要的工具
command -v aws >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 AWS CLI${NC}" >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 zip${NC}" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 Python 3${NC}" >&2; exit 1; }

# 检查 AWS 凭证
aws sts get-caller-identity > /dev/null 2>&1 || { echo -e "${RED}错误: AWS 凭证未配置${NC}" >&2; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account ID: $ACCOUNT_ID${NC}"
echo ""

# 步骤 1: 创建 IAM 角色（如果不存在）
echo "步骤 1: 检查 IAM 角色..."
if aws iam get-role --role-name $ROLE_NAME --region $REGION --no-cli-pager 2>/dev/null; then
    echo -e "${YELLOW}⚠ IAM 角色已存在，跳过创建${NC}"
else
    echo "创建 IAM 角色: $ROLE_NAME"
    
    # 创建信任策略
    cat > /tmp/trust-policy.json <<EOF
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

    # 创建角色
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --region $REGION \
        --no-cli-pager > /dev/null

    # 附加基本执行策略
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region $REGION \
        --no-cli-pager

    echo -e "${GREEN}✓ IAM 角色创建成功${NC}"
    
    # 等待角色生效
    echo "等待 IAM 角色生效..."
    sleep 10
fi
echo ""

# 步骤 2: 准备 Lambda 部署包
echo "步骤 2: 准备 Lambda 部署包..."

# 创建临时目录
rm -rf /tmp/zhipu-lambda
mkdir -p /tmp/zhipu-lambda

# 复制 Lambda 函数代码
cp zhipu_lambda_function.py /tmp/zhipu-lambda/lambda_function.py

# 安装依赖
echo "安装 Python 依赖..."
pip install requests -t /tmp/zhipu-lambda/ --quiet

# 创建 ZIP 包
cd /tmp/zhipu-lambda
zip -r /tmp/zhipu-lambda-deployment.zip . > /dev/null
cd - > /dev/null

echo -e "${GREEN}✓ 部署包创建成功${NC}"
echo ""

# 步骤 3: 部署或更新 Lambda 函数
echo "步骤 3: 部署 Lambda 函数..."

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --no-cli-pager 2>/dev/null; then
    echo "更新现有 Lambda 函数..."
    
    # 更新函数代码
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb:///tmp/zhipu-lambda-deployment.zip \
        --region $REGION \
        --no-cli-pager > /dev/null
    
    echo "✓ Lambda 函数代码已更新"
    
    # 等待代码更新完成
    echo "等待代码更新完成..."
    sleep 10
    
    # 更新函数配置
    echo "更新 Lambda 配置..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --handler lambda_function.lambda_handler \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables={ZHIPU_API_KEY=$ZHIPU_API_KEY} \
        --region $REGION \
        --no-cli-pager > /dev/null
    
    echo -e "${GREEN}✓ Lambda 函数更新成功${NC}"
else
    echo "创建新的 Lambda 函数..."
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb:///tmp/zhipu-lambda-deployment.zip \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables={ZHIPU_API_KEY=$ZHIPU_API_KEY} \
        --region $REGION \
        --no-cli-pager > /dev/null
    
    echo -e "${GREEN}✓ Lambda 函数创建成功${NC}"
fi

# 等待函数就绪
echo "等待函数就绪..."
sleep 5

# 获取函数 ARN
LAMBDA_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --no-cli-pager --query 'Configuration.FunctionArn' --output text)
echo ""
echo -e "${GREEN}Lambda Function ARN:${NC}"
echo "$LAMBDA_ARN"
echo ""

# 步骤 4: 测试 Lambda 函数
echo "步骤 4: 测试 Lambda 函数..."

# 创建测试 payload（使用 echo 确保 UTF-8 编码）
echo '{"query": "人工智能最新进展", "max_results": 3, "search_engine": "search_std"}' > /tmp/test-payload.json

echo "调用 Lambda 函数测试..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test-payload.json \
    --no-cli-pager \
    /tmp/zhipu-response.json > /dev/null 2>&1

# 检查响应
if grep -q "statusCode" /tmp/zhipu-response.json && grep -q "200" /tmp/zhipu-response.json; then
    echo -e "${GREEN}✓ Lambda 函数测试成功！${NC}"
    echo ""
    echo "测试结果预览："
    cat /tmp/zhipu-response.json | python3 -c "
import sys, json
try:
    response = json.load(sys.stdin)
    if 'body' in response:
        body = json.loads(response['body'])
        if 'content' in body and len(body['content']) > 0:
            text = body['content'][0].get('text', '')
            # 只显示前500个字符
            print(text[:500] if len(text) > 500 else text)
        else:
            print('响应格式正确，但无内容')
    else:
        print(json.dumps(response, ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print(f'解析响应时出错: {e}')
"
else
    echo -e "${YELLOW}⚠ Lambda 函数响应异常，请检查${NC}"
    echo "响应内容："
    cat /tmp/zhipu-response.json
fi
echo ""

# 保存 Lambda ARN 到配置文件
if grep -q "ZHIPU_LAMBDA_ARN=" "$CONFIG_FILE"; then
    # 更新现有的 ARN
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|ZHIPU_LAMBDA_ARN=.*|ZHIPU_LAMBDA_ARN=$LAMBDA_ARN|" "$CONFIG_FILE"
    else
        sed -i "s|ZHIPU_LAMBDA_ARN=.*|ZHIPU_LAMBDA_ARN=$LAMBDA_ARN|" "$CONFIG_FILE"
    fi
else
    # 添加新的 ARN
    echo "" >> "$CONFIG_FILE"
    echo "# 智谱配置" >> "$CONFIG_FILE"
    echo "ZHIPU_LAMBDA_ARN=$LAMBDA_ARN" >> "$CONFIG_FILE"
fi

echo "✓ Lambda ARN 已保存到 config.txt"

# 清理临时文件
rm -rf /tmp/zhipu-lambda
rm -f /tmp/zhipu-lambda-deployment.zip
rm -f /tmp/trust-policy.json
rm -f /tmp/test-payload.json
rm -f /tmp/zhipu-response.json

echo "================================================"
echo "部署完成！"
echo "================================================"
echo ""
echo "Lambda Function Name: $FUNCTION_NAME"
echo "Lambda Function ARN: $LAMBDA_ARN"
echo "Region: $REGION"
echo ""
echo "下一步:"
echo "  1. 测试 Lambda: ./test_lambda.sh"
echo "  2. 添加到 Gateway: python3 add_target.py"
echo "  3. 测试 Target: ./test_target.sh"
echo ""
