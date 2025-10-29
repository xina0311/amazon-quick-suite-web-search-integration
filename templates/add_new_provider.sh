#!/bin/bash
# ============================================================================
# 通用脚本：添加新的 AI Search Provider 到 AgentCore Gateway
# ============================================================================
# 
# 使用方法：
# ./add_new_provider.sh <provider_name> <lambda_arn>
#
# 示例：
# ./add_new_provider.sh metaso arn:aws:lambda:us-east-1:123456:function:MetasoSearchFunction
#
# ============================================================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================================================
# 参数检查
# ============================================================================

PROVIDER_NAME=$1
LAMBDA_ARN=$2
REGION="${3:-us-east-1}"

if [ -z "$PROVIDER_NAME" ] || [ -z "$LAMBDA_ARN" ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./add_new_provider.sh <provider_name> <lambda_arn> [region]"
    echo ""
    echo "示例:"
    echo "  ./add_new_provider.sh metaso arn:aws:lambda:us-east-1:123456:function:MetasoSearchFunction"
    echo "  ./add_new_provider.sh cloudsway arn:aws:lambda:us-west-2:123456:function:CloudswaySearchFunction us-west-2"
    echo ""
    exit 1
fi

# ============================================================================
# 加载配置
# ============================================================================

echo "================================================"
echo "添加新的 AI Search Provider"
echo "================================================"
echo ""
echo "Provider: $PROVIDER_NAME"
echo "Lambda ARN: $LAMBDA_ARN"
echo "Region: $REGION"
echo ""

# 从配置文件读取 Gateway ID
if [ -f "../cognito-bocha-s2s.txt" ]; then
    GATEWAY_ID=$(grep "GATEWAY_ID=" ../cognito-bocha-s2s.txt | cut -d'=' -f2)
elif [ -f "cognito-bocha-s2s.txt" ]; then
    GATEWAY_ID=$(grep "GATEWAY_ID=" cognito-bocha-s2s.txt | cut -d'=' -f2)
else
    echo -e "${RED}错误: 未找到配置文件 cognito-bocha-s2s.txt${NC}"
    echo "请先运行主部署脚本"
    exit 1
fi

if [ -z "$GATEWAY_ID" ]; then
    echo -e "${RED}错误: 配置文件中未找到 GATEWAY_ID${NC}"
    exit 1
fi

echo "Gateway ID: $GATEWAY_ID"
echo ""

# ============================================================================
# 确认操作
# ============================================================================

echo -e "${YELLOW}即将执行以下操作：${NC}"
echo "1. 验证 Lambda 函数存在"
echo "2. 创建 Gateway Target: ${PROVIDER_NAME}SearchTarget"
echo "3. 配置 MCP Tool: ${PROVIDER_NAME}_search"
echo ""
read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# ============================================================================
# 验证 Lambda 函数
# ============================================================================

echo ""
echo "[步骤 1/3] 验证 Lambda 函数..."

if aws lambda get-function --function-name ${LAMBDA_ARN##*:} --region $REGION > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Lambda 函数存在${NC}"
else
    echo -e "${RED}✗ Lambda 函数不存在或无权限访问${NC}"
    echo "Lambda ARN: $LAMBDA_ARN"
    exit 1
fi

# ============================================================================
# 创建 Gateway Target
# ============================================================================

echo ""
echo "[步骤 2/3] 创建 Gateway Target..."

# 定义工具 Schema（可根据需求自定义）
TOOL_SCHEMA=$(cat <<EOF
[{
  "name": "${PROVIDER_NAME}_search",
  "description": "Search using ${PROVIDER_NAME} AI. Use this tool to find information from ${PROVIDER_NAME} search engine.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return (1-50, default: 10)"
      }
    },
    "required": ["query"]
  }
}]
EOF
)

# 创建 Target 配置
TARGET_CONFIG=$(cat <<EOF
{
  "mcp": {
    "lambda": {
      "lambdaArn": "$LAMBDA_ARN",
      "toolSchema": {
        "inlinePayload": $TOOL_SCHEMA
      }
    }
  }
}
EOF
)

# 凭证配置
CREDENTIAL_CONFIG='[{
  "credentialProviderType": "GATEWAY_IAM_ROLE"
}]'

# 执行创建
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier "$GATEWAY_ID" \
  --name "${PROVIDER_NAME}SearchTarget" \
  --description "${PROVIDER_NAME} AI Search Target" \
  --target-configuration "$TARGET_CONFIG" \
  --credential-provider-configurations "$CREDENTIAL_CONFIG" \
  --region "$REGION" \
  > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Gateway Target 创建成功${NC}"
else
    echo -e "${RED}✗ Gateway Target 创建失败${NC}"
    exit 1
fi

# ============================================================================
# 验证创建
# ============================================================================

echo ""
echo "[步骤 3/3] 验证 Target 状态..."

sleep 3

# 列出 Gateway 的所有 Targets
TARGET_LIST=$(aws bedrock-agentcore-control list-gateway-targets \
  --gateway-identifier "$GATEWAY_ID" \
  --region "$REGION" \
  --query "items[?name=='${PROVIDER_NAME}SearchTarget'].{Name:name,ID:targetId,Status:status}" \
  --output table)

echo "$TARGET_LIST"

# ============================================================================
# 完成
# ============================================================================

echo ""
echo "================================================"
echo -e "${GREEN}✅ 成功添加新的 AI Search Provider！${NC}"
echo "================================================"
echo ""
echo "Provider 名称: $PROVIDER_NAME"
echo "Tool 名称: ${PROVIDER_NAME}SearchTarget___${PROVIDER_NAME}_search"
echo "Gateway ID: $GATEWAY_ID"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "1. Quick Suite 会自动发现新工具（约1-2分钟）"
echo "2. 无需重新配置认证"
echo "3. 在 Chat Agent 中测试新工具"
echo ""
echo "测试命令示例："
echo "  使用 ${PROVIDER_NAME} 搜索查找 'AI Agent' 的信息"
echo ""
