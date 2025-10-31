#!/bin/bash

# 秘塔 Lambda 函数测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FUNCTION_NAME="MetasoWebSearchFunction"
REGION="${REGION:-us-east-1}"

echo "================================================"
echo "测试秘塔 Lambda 函数"
echo "================================================"
echo ""
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

# 检查 Lambda 函数是否存在
echo "检查 Lambda 函数..."
if ! aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo -e "${RED}✗ Lambda 函数不存在${NC}"
    echo "请先运行: ./deploy.sh"
    exit 1
fi
echo -e "${GREEN}✓ Lambda 函数存在${NC}"
echo ""

# 检查环境变量配置
echo "检查 API Key 配置..."
API_KEY_STATUS=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Environment.Variables.METASO_API_KEY' \
    --output text 2>/dev/null || echo "NOT_SET")

if [ "$API_KEY_STATUS" == "NOT_SET" ] || [ "$API_KEY_STATUS" == "None" ]; then
    echo -e "${RED}✗ METASO_API_KEY 未配置${NC}"
    echo ""
    echo "请配置 API Key:"
    echo "  aws lambda update-function-configuration \\"
    echo "    --function-name $FUNCTION_NAME \\"
    echo "    --environment Variables={METASO_API_KEY=your-api-key} \\"
    echo "    --region $REGION"
    exit 1
fi
echo -e "${GREEN}✓ METASO_API_KEY 已配置${NC}"
echo ""

# 测试 1: 基础网页搜索
echo "测试 1: 基础网页搜索"
echo "  Query: 人工智能"
echo "  Scope: webpage"
echo "  Max Results: 3"

# 使用 base64 编码来支持中文
PAYLOAD1='{"query": "人工智能", "scope": "webpage", "max_results": 3}'

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload "$PAYLOAD1" \
    /tmp/metaso_response1.json > /dev/null

# 使用 Python 检查响应并显示内容
python3 << 'PYTHON_SCRIPT'
import json
import sys

try:
    with open('/tmp/metaso_response1.json', 'r', encoding='utf-8') as f:
        response = json.load(f)
    
    if response.get('statusCode') != 200:
        print(f"\033[0;31m✗ 测试失败: HTTP {response.get('statusCode')}\033[0m")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    body = json.loads(response['body'])
    
    if 'content' not in body or not body['content']:
        print("\033[0;31m✗ 测试失败: 响应格式错误\033[0m")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    text = body['content'][0]['text']
    
    print("\033[0;32m✓ 测试 1 通过\033[0m")
    print()
    print("响应预览:")
    print("-" * 60)
    print(text[:800])
    if len(text) > 800:
        print("...")
    print("-" * 60)
    
except Exception as e:
    print(f"\033[0;31m✗ 测试失败: {e}\033[0m")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""

# 测试 2: 论文搜索
echo "测试 2: 论文搜索"
echo "  Query: 机器学习"
echo "  Scope: paper"

PAYLOAD2='{"query": "机器学习", "scope": "paper", "max_results": 2}'

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload "$PAYLOAD2" \
    /tmp/metaso_response2.json > /dev/null

# 使用 Python 检查并显示论文搜索结果
python3 << 'PYTHON_SCRIPT2'
import json
import sys

try:
    with open('/tmp/metaso_response2.json', 'r', encoding='utf-8') as f:
        response = json.load(f)
    
    if response.get('statusCode') != 200:
        print(f"\033[1;33m⚠ 测试 2 失败: HTTP {response.get('statusCode')}\033[0m")
        sys.exit(0)  # 不退出，论文搜索可能不可用
    
    body = json.loads(response['body'])
    
    if 'content' not in body or not body['content']:
        print("\033[1;33m⚠ 测试 2: 响应格式错误\033[0m")
        sys.exit(0)
    
    text = body['content'][0]['text']
    
    print("\033[0;32m✓ 测试 2 通过\033[0m")
    print()
    print("论文搜索结果预览:")
    print("-" * 60)
    print(text[:800])
    if len(text) > 800:
        print("...")
    print("-" * 60)
    
except Exception as e:
    print(f"\033[1;33m⚠ 测试 2 异常: {e}\033[0m")
    sys.exit(0)
PYTHON_SCRIPT2

echo ""
echo "================================================"
echo "测试完成"
echo "================================================"
echo ""
echo -e "${GREEN}✓ 主要测试通过！${NC}"
echo ""
echo "Lambda 函数工作正常，可以继续部署到 Gateway"
echo ""

# 清理
rm -f /tmp/metaso_response*.json
