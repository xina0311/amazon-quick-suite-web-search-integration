#!/bin/bash

# 智谱 Web Search Gateway Target 端到端测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
REGION="${REGION:-us-east-1}"
CONFIG_FILE="../../config.txt"

echo "================================================"
echo "测试智谱 Web Search Gateway Target"
echo "================================================"
echo ""

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 配置文件 $CONFIG_FILE 未找到${NC}"
    exit 1
fi

# 加载配置
GATEWAY_ARN=$(grep "GATEWAY_ARN=" "$CONFIG_FILE" | cut -d'=' -f2)
ZHIPU_TARGET_ID=$(grep "ZHIPU_TARGET_ID=" "$CONFIG_FILE" | cut -d'=' -f2)

if [ -z "$GATEWAY_ARN" ]; then
    echo -e "${RED}错误: 未找到 GATEWAY_ARN 配置${NC}"
    exit 1
fi

echo "Gateway ARN: $GATEWAY_ARN"
echo "Target ID: $ZHIPU_TARGET_ID"
echo ""

# 提取 Gateway ID
GATEWAY_ID=$(echo $GATEWAY_ARN | sed 's/.*gateway\///')

# 检查 Target 状态
echo "检查 Target 状态..."
TARGET_STATUS=$(aws bedrock-agentcore-control get-gateway-target \
    --gateway-identifier $GATEWAY_ID \
    --target-identifier $ZHIPU_TARGET_ID \
    --region $REGION \
    --query 'status' \
    --output text 2>/dev/null || echo "UNKNOWN")

echo "Target Status: $TARGET_STATUS"

if [ "$TARGET_STATUS" == "READY" ] || [ "$TARGET_STATUS" == "ACTIVE" ]; then
    echo -e "${GREEN}✓ Target 状态正常${NC}"
else
    echo -e "${YELLOW}⚠ Target 状态: $TARGET_STATUS${NC}"
fi
echo ""

# 列出 Gateway 的所有 Targets
echo "Gateway 中的所有 Targets:"
aws bedrock-agentcore-control list-gateway-targets \
    --gateway-identifier $GATEWAY_ID \
    --region $REGION \
    --query "items[].{Name:name,ID:targetId,Status:status}" \
    --output table

echo ""
echo "================================================"
echo -e "${GREEN}测试完成！${NC}"
echo "================================================"
echo ""
echo "在 Quick Suite 中测试智谱搜索:"
echo "  1. 打开 Quick Suite Chat Agent"
echo "  2. 输入: 使用智谱搜索查找关于 AWS Lambda 的最新信息"
echo "  3. 或者: 用智谱搜索一下人工智能的新闻"
echo ""
