#!/bin/bash

# 博查 Lambda 函数测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FUNCTION_NAME="BochaWebSearchFunction"
REGION="${REGION:-us-east-1}"

echo "================================================"
echo "测试博查 Lambda 函数"
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
    --query 'Environment.Variables.BOCHA_API_KEY' \
    --output text 2>/dev/null || echo "NOT_SET")

if [ "$API_KEY_STATUS" == "NOT_SET" ] || [ "$API_KEY_STATUS" == "None" ]; then
    echo -e "${RED}✗ BOCHA_API_KEY 未配置${NC}"
    echo ""
    echo "请配置 API Key:"
    echo "  aws lambda update-function-configuration \\"
    echo "    --function-name $FUNCTION_NAME \\"
    echo "    --environment Variables={BOCHA_API_KEY=your-api-key} \\"
    echo "    --region $REGION"
    exit 1
fi
echo -e "${GREEN}✓ BOCHA_API_KEY 已配置${NC}"
echo ""

# 测试 1: 基础搜索测试
echo "测试 1: 基础搜索"
echo "  Query: 人工智能"
echo "  Max Results: 3"

# 使用 base64 编码来支持中文
PAYLOAD='{"query": "人工智能", "max_results": 3}'

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload "$PAYLOAD" \
    /tmp/bocha_response.json > /dev/null

# 使用 Python 检查响应并显示内容
python3 << 'PYTHON_SCRIPT'
import json
import sys

try:
    # 读取响应文件
    with open('/tmp/bocha_response.json', 'r', encoding='utf-8') as f:
        response = json.load(f)
    
    # 检查状态码
    if response.get('statusCode') != 200:
        print(f"\033[0;31m✗ 测试失败: HTTP {response.get('statusCode')}\033[0m")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # 解析 body
    body = json.loads(response['body'])
    
    # 检查 content 结构
    if 'content' not in body or not body['content']:
        print("\033[0;31m✗ 测试失败: 响应格式错误\033[0m")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # 获取搜索结果文本
    text = body['content'][0]['text']
    
    # 测试通过
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
echo "================================================"
echo "测试完成"
echo "================================================"
echo ""
echo -e "${GREEN}✓ 所有测试通过！${NC}"
echo ""
echo "Lambda 函数工作正常，可以继续部署到 Gateway"
echo ""

# 清理
rm -f /tmp/bocha_test_payload.json /tmp/bocha_response.json
