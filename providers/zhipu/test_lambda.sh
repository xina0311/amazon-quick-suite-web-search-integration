#!/bin/bash

# 智谱 Web Search Lambda 函数测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
FUNCTION_NAME="ZhipuWebSearchFunction"
REGION="${REGION:-us-east-1}"

echo "================================================"
echo "测试智谱 Web Search Lambda 函数"
echo "================================================"
echo ""
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

# 检查 Lambda 函数是否存在
if ! aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --no-cli-pager > /dev/null 2>&1; then
    echo -e "${RED}错误: Lambda 函数 $FUNCTION_NAME 不存在${NC}"
    echo "请先运行: ./deploy.sh"
    exit 1
fi

# 测试 1: 基本搜索
echo "测试 1: 基本搜索..."
echo '{"query": "人工智能最新进展", "max_results": 3}' > /tmp/test-basic.json

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test-basic.json \
    --no-cli-pager \
    /tmp/response-basic.json > /dev/null 2>&1

echo "响应:"
cat /tmp/response-basic.json | python3 -c "
import sys, json
try:
    response = json.load(sys.stdin)
    if response.get('statusCode') == 200:
        body = json.loads(response['body'])
        print(body['content'][0]['text'][:1000])
        print('...(截断)')
    else:
        print(f'错误: {response}')
except Exception as e:
    print(f'解析错误: {e}')
"
echo ""

# 测试 2: 带时间过滤的搜索
echo "测试 2: 带时间过滤的搜索（一周内）..."
echo '{"query": "AWS new features", "max_results": 3, "recency_filter": "oneWeek"}' > /tmp/test-recency.json

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test-recency.json \
    --no-cli-pager \
    /tmp/response-recency.json > /dev/null 2>&1

echo "响应状态码:"
cat /tmp/response-recency.json | python3 -c "
import sys, json
response = json.load(sys.stdin)
print(f'Status: {response.get(\"statusCode\", \"unknown\")}')
"
echo ""

# 测试 3: 空查询（应返回错误）
echo "测试 3: 空查询（应返回 400 错误）..."
echo '{"query": "", "max_results": 3}' > /tmp/test-empty.json

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test-empty.json \
    --no-cli-pager \
    /tmp/response-empty.json > /dev/null 2>&1

echo "响应:"
cat /tmp/response-empty.json | python3 -c "
import sys, json
response = json.load(sys.stdin)
status = response.get('statusCode', 'unknown')
if status == 400:
    print(f'✓ 正确返回 400 错误')
else:
    print(f'⚠ 预期 400，实际返回 {status}')
body = json.loads(response.get('body', '{}'))
if 'error' in body:
    print(f'错误信息: {body[\"error\"]}')
"
echo ""

# 清理
rm -f /tmp/test-basic.json /tmp/test-recency.json /tmp/test-empty.json
rm -f /tmp/response-basic.json /tmp/response-recency.json /tmp/response-empty.json

echo "================================================"
echo -e "${GREEN}测试完成！${NC}"
echo "================================================"
