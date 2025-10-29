#!/bin/bash

# Bocha Web Search - Quick Suite 集成自动化部署脚本
# 此脚本将自动完成所有部署步骤

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
REGION="${1:-us-west-2}"
BOCHA_API_KEY="${BOCHA_API_KEY:-sk-xxxxxx}"

echo "================================================"
echo "Bocha Web Search - Quick Suite Integration"
echo "自动化部署脚本"
echo "================================================"
echo ""
echo "Region: $REGION"
echo ""

# 检查必要的工具
echo "检查必要的工具..."
command -v aws >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 AWS CLI${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 jq${NC}" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 Python 3${NC}" >&2; exit 1; }
command -v pip >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 pip${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ 所有必要工具已就绪${NC}"
echo ""

# 检查 AWS 凭证
echo "检查 AWS 凭证..."
aws sts get-caller-identity > /dev/null 2>&1 || { echo -e "${RED}错误: AWS 凭证未配置${NC}" >&2; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account ID: $ACCOUNT_ID${NC}"
echo ""

# 步骤 1: 创建 Cognito S2S 认证
echo "================================================"
echo "步骤 1/4: 创建 Cognito S2S 认证"
echo "================================================"
if [ -f "cognito-bocha-s2s.txt" ]; then
    echo -e "${YELLOW}⚠ cognito-bocha-s2s.txt 已存在，跳过 Cognito 设置${NC}"
    echo "如需重新创建，请先删除该文件或运行清理脚本"
else
    ./setup_cognito_s2s_bocha.sh $REGION
fi
echo ""

# 步骤 2: 更新 Lambda 函数中的 API Key
echo "================================================"
echo "步骤 2/4: 配置 Bocha API Key"
echo "================================================"
if [ "$BOCHA_API_KEY" = "sk-xxxxxx" ]; then
    echo -e "${YELLOW}⚠ 警告: 使用默认的 API Key${NC}"
    echo "请设置环境变量: export BOCHA_API_KEY=your-actual-api-key"
    echo "或编辑 bocha_lambda_function.py 文件"
else
    echo "更新 Lambda 函数中的 API Key..."
    sed -i.bak "s/sk-xxxxxx/$BOCHA_API_KEY/g" bocha_lambda_function.py
    echo -e "${GREEN}✓ API Key 已配置${NC}"
fi
echo ""

# 步骤 3: 部署 Lambda 函数
echo "================================================"
echo "步骤 3/4: 部署 Lambda 函数"
echo "================================================"
REGION=$REGION ./deploy_lambda.sh
echo ""

# 步骤 4: 创建 AgentCore Gateway
echo "================================================"
echo "步骤 4/4: 创建 AgentCore Gateway"
echo "================================================"
python3 create_bocha_gateway.py
echo ""

# 显示配置摘要
echo ""
echo "================================================"
echo "部署完成！"
echo "================================================"
echo ""

if [ -f "cognito-bocha-s2s.txt" ]; then
    # 加载配置（只加载有效的变量定义行）
    while IFS='=' read -r key value; do
        # 只加载符合变量命名规则的行：大写字母、数字、下划线，且不包含空格
        if [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ -n "$value" ]]; then
            export "$key"="$value"
        fi
    done < cognito-bocha-s2s.txt
    
    echo -e "${GREEN}配置摘要：${NC}"
    echo "--------------------"
    echo "Region: $REGION"
    echo "Cognito User Pool ID: $POOL_ID"
    echo "Lambda Function ARN: $LAMBDA_ARN"
    echo "Gateway URL: $GATEWAY_URL"
    echo ""
    echo -e "${YELLOW}Quick Suite 配置参数：${NC}"
    echo "--------------------"
    echo "MCP Endpoint: $GATEWAY_URL"
    echo "Client ID: $CLIENT_ID"
    echo "Client Secret: $CLIENT_SECRET"
    echo "Token URL: $TOKEN_ENDPOINT"
    echo ""
    echo "完整配置已保存到: cognito-bocha-s2s.txt"
else
    echo -e "${RED}错误: 配置文件未找到${NC}"
fi

echo ""
echo "================================================"
echo "下一步："
echo "================================================"
echo "1. 登录 Amazon Quick Suite"
echo "2. 转到 Integrations > Actions > Model Context Protocol"
echo "3. 使用上述配置参数创建新的 Integration"
echo "4. 在 Chat Agent 中测试博查 Web Search 功能"
echo ""
echo "详细说明请参考: ../Bocha_Web_Search_Quick_Suite_Integration_Guide.md"
echo ""
