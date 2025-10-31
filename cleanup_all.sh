#!/bin/bash

# 一键清理所有 AWS 资源脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION="${1:-us-east-1}"

echo "================================================"
echo "清理 AI Search Integration 资源"
echo "================================================"
echo ""
echo -e "${YELLOW}警告: 此脚本将删除所有已部署的资源${NC}"
echo ""
read -p "确认要继续吗？(yes/NO) " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始清理资源..."
echo ""

# 加载配置
if [ -f "config.txt" ]; then
    while IFS='=' read -r key value; do
        if [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ -n "$value" ]]; then
            export "$key"="$value"
        fi
    done < config.txt
fi

# 1. 删除 Lambda 函数
echo "[1/4] 删除 Lambda 函数..."
for func in BochaWebSearchFunction MetasoWebSearchFunction CloudswayWebSearchFunction; do
    if aws lambda get-function --function-name $func --region $REGION 2>/dev/null; then
        aws lambda delete-function --function-name $func --region $REGION
        echo "  ✓ 已删除: $func"
    fi
done

# 2. 删除 IAM 角色
echo ""
echo "[2/4] 删除 IAM 角色..."
for role in BochaLambdaExecutionRole MetasoLambdaExecutionRole CloudswayLambdaExecutionRole agentcore-ai-search-gateway-role; do
    if aws iam get-role --role-name $role 2>/dev/null; then
        aws iam detach-role-policy --role-name $role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || true
        aws iam delete-role-policy --role-name $role --policy-name AgentCoreGatewayPolicy 2>/dev/null || true
        aws iam delete-role --role-name $role 2>/dev/null
        echo "  ✓ 已删除: $role"
    fi
done

# 3. 删除 Gateway（需要在 AWS Console 手动删除 Targets）
echo ""
echo "[3/4] Gateway 和 Targets..."
echo -e "${YELLOW}  注意: Gateway 和 Targets 需要在 AWS Console 中手动删除${NC}"
if [ -n "$GATEWAY_ID" ]; then
    echo "  Gateway ID: $GATEWAY_ID"
    echo "  访问 AWS Bedrock AgentCore 控制台删除"
fi

# 4. 删除 Cognito User Pool
echo ""
echo "[4/4] 删除 Cognito User Pool..."
if [ -n "$POOL_ID" ] && [ -n "$DOMAIN_PREFIX" ]; then
    aws cognito-idp delete-user-pool-domain --domain $DOMAIN_PREFIX --user-pool-id $POOL_ID --region $REGION 2>/dev/null || true
    sleep 2
    aws cognito-idp delete-user-pool --user-pool-id $POOL_ID --region $REGION 2>/dev/null || true
    echo "  ✓ 已删除 Cognito User Pool: $POOL_ID"
fi

# 5. 删除配置文件
echo ""
echo "清理配置文件..."
rm -f config.txt utils/cognito-bocha-s2s.txt utils/cleanup-cognito-bocha-s2s.sh utils/test-bocha-s2s-token.sh

echo ""
echo "================================================"
echo "清理完成！"
echo "================================================"
echo ""
echo -e "${GREEN}已删除的资源:${NC}"
echo "  - Lambda 函数 (3个)"
echo "  - IAM 角色 (4个)"
echo "  - Cognito User Pool"
echo "  - 配置文件"
echo ""
echo -e "${YELLOW}需要手动删除:${NC}"
echo "  - Gateway 和 Targets（在 AWS Console 中）"
echo ""
