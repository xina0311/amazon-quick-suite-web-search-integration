#!/bin/bash

# Amazon Quick Suite AI Search Integration
# 基础设施部署脚本 - 部署 Cognito 和 AgentCore Gateway

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
REGION="${1:-us-east-1}"

echo "================================================"
echo "AI Search Integration - 基础设施部署"
echo "================================================"
echo ""
echo "Region: $REGION"
echo ""

# 检查必要的工具
echo "检查必要的工具..."
command -v aws >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 AWS CLI${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 jq${NC}" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}错误: 需要安装 Python 3${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ 所有必要工具已就绪${NC}"
echo ""

# 检查 AWS 凭证
echo "检查 AWS 凭证..."
aws sts get-caller-identity > /dev/null 2>&1 || { echo -e "${RED}错误: AWS 凭证未配置${NC}" >&2; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account ID: $ACCOUNT_ID${NC}"
echo ""

# 检查配置文件是否已存在
if [ -f "config.txt" ]; then
    echo -e "${YELLOW}⚠ 配置文件已存在${NC}"
    read -p "是否继续并覆盖现有配置？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi
    rm config.txt
fi

# 步骤 1: 创建 Cognito S2S 认证
echo "================================================"
echo "步骤 1/2: 创建 Cognito S2S 认证"
echo "================================================"
echo ""

cd utils
./setup_cognito.sh $REGION

# 复制配置文件到项目根目录
if [ -f "cognito-bocha-s2s.txt" ]; then
    cp cognito-bocha-s2s.txt ../config.txt
    echo "✓ 配置文件已复制到 config.txt"
elif [ -f "cognito-config.txt" ]; then
    cp cognito-config.txt ../config.txt
    echo "✓ 配置文件已复制到 config.txt"
else
    cd ..
    echo -e "${RED}错误: Cognito 配置文件未生成${NC}"
    exit 1
fi

cd ..

echo ""

# 步骤 2: 创建 AgentCore Gateway
echo "================================================"
echo "步骤 2/2: 创建 AgentCore Gateway"
echo "================================================"
echo ""

cd utils
python3 create_gateway.py
cd ..

echo ""

# 显示配置摘要
echo "================================================"
echo "基础设施部署完成！"
echo "================================================"
echo ""

if [ -f "config.txt" ]; then
    # 加载配置
    while IFS='=' read -r key value; do
        if [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ -n "$value" ]]; then
            export "$key"="$value"
        fi
    done < config.txt
    
    echo -e "${GREEN}配置摘要：${NC}"
    echo "--------------------"
    echo "Region: $REGION"
    echo "Cognito User Pool ID: $POOL_ID"
    echo "Gateway URL: $GATEWAY_URL"
    echo ""
    echo "完整配置已保存到: config.txt"
else
    echo -e "${RED}错误: 配置文件未找到${NC}"
fi

echo ""
echo "================================================"
echo "下一步："
echo "================================================"
echo ""
echo "现在可以部署 AI Search Providers："
echo ""
echo "1. 部署博查搜索："
echo "   cd providers/bocha"
echo "   ./deploy.sh"
echo "   python3 add_target.py"
echo ""
echo "2. 部署秘塔搜索："
echo "   cd providers/metaso"
echo "   ./deploy.sh"
echo "   python3 add_target.py"
echo ""
echo "3. 配置 Amazon Quick Suite："
echo "   参考 docs/QUICK_SUITE_SETUP.md"
echo ""
