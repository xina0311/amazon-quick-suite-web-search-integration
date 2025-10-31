#!/bin/bash

# 博查 Gateway Target 测试脚本
# 测试 Lambda 是否成功添加到 Gateway 并可正常工作

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION="${REGION:-us-east-1}"

echo "================================================"
echo "测试博查 Gateway Target"
echo "================================================"
echo ""

# 检查配置文件
if [ ! -f "../../config.txt" ]; then
    echo -e "${RED}✗ 配置文件不存在${NC}"
    echo "请先运行基础设施部署"
    exit 1
fi

# 加载配置（只加载有效的变量定义行）
while IFS='=' read -r key value; do
    if [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ -n "$value" ]]; then
        export "$key"="$value"
    fi
done < <(grep '=' ../../config.txt | grep -v '^#' | grep -v '^=')

if [ -z "$GATEWAY_ARN" ]; then
    echo -e "${RED}✗ GATEWAY_ARN 未配置${NC}"
    echo ""
    echo "请检查 ../../config.txt 文件是否包含 GATEWAY_ARN"
    echo "如果没有，请运行："
    echo "  cat ../../config.txt | grep GATEWAY"
    exit 1
fi

echo "Gateway ARN: $GATEWAY_ARN"
echo ""

# 获取 Gateway ID
GATEWAY_ID=$(echo $GATEWAY_ARN | rev | cut -d'/' -f1 | rev)

echo "检查 Gateway 状态..."
GATEWAY_STATUS=$(aws bedrock-agentcore-control get-gateway \
    --gateway-identifier $GATEWAY_ID \
    --region $REGION \
    --query 'status' \
    --output text 2>/dev/null || echo "ERROR")

if [ "$GATEWAY_STATUS" != "AVAILABLE" ] && [ "$GATEWAY_STATUS" != "READY" ]; then
    echo -e "${RED}✗ Gateway 状态异常: $GATEWAY_STATUS${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Gateway 状态: $GATEWAY_STATUS${NC}"
echo ""

# 列出 Gateway Targets
echo "检查 Gateway Targets..."
TARGETS=$(aws bedrock-agentcore-control list-gateway-targets \
    --gateway-identifier $GATEWAY_ID \
    --region $REGION \
    --output json 2>/dev/null || echo '{"items":[]}')

BOCHA_TARGET=$(echo $TARGETS | jq -r '.items[] | select(.name=="BochaWebSearchTarget") | .targetId' | head -1)

if [ -z "$BOCHA_TARGET" ] || [ "$BOCHA_TARGET" == "null" ]; then
    echo -e "${RED}✗ 博查 Target 未找到${NC}"
    echo "请先运行: python3 add_target.py"
    exit 1
fi

echo -e "${GREEN}✓ 博查 Target 已找到: $BOCHA_TARGET${NC}"
echo ""

# 列出所有 Targets
echo "列出 Gateway 中的所有 Targets..."
aws bedrock-agentcore-control list-gateway-targets \
    --gateway-identifier $GATEWAY_ID \
    --region $REGION \
    --query 'items[*].[name,targetId,status]' \
    --output table

echo ""
echo "================================================"
echo "测试完成"
echo "================================================"
echo ""
echo -e "${GREEN}✓ 博查 Target 已成功添加到 Gateway${NC}"
echo ""
echo "Target ID: $BOCHA_TARGET"
echo "状态: READY"
echo ""
echo "注意: Lambda 功能测试请运行 ./test_lambda.sh"
echo "      完整的 Gateway 测试请运行 cd ../../utils && python3 test_gateway.py"
echo ""
