#!/usr/bin/env python3
"""
测试 Bocha Web Search Gateway
验证 Gateway 可以正确响应 MCP 请求
"""

import boto3
import json
import sys
import requests
import base64

def load_config():
    """加载配置文件"""
    config = {}
    with open('cognito-bocha-s2s.txt', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#') and not line.startswith('='):
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config

def get_token(client_id, client_secret, token_endpoint, scopes):
    """从 Cognito 获取 access token"""
    print("步骤 1: 从 Cognito 获取 Access Token...")
    
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': scopes
    }
    
    response = requests.post(token_endpoint, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    access_token = token_data['access_token']
    
    print(f"✓ Token 获取成功")
    print(f"  Token (前50字符): {access_token[:50]}...")
    print()
    
    return access_token

def test_list_tools(gateway_url, token):
    """测试 MCP ListTools API"""
    print("步骤 2: 调用 MCP ListTools API...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # MCP ListTools 请求
    payload = {
        'jsonrpc': '2.0',
        'method': 'tools/list',
        'id': 1
    }
    
    response = requests.post(gateway_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    
    if 'result' in result and 'tools' in result['result']:
        tools = result['result']['tools']
        print(f"✓ 成功获取工具列表")
        print(f"  可用工具数量: {len(tools)}")
        
        for tool in tools:
            print(f"\n  工具名称: {tool['name']}")
            print(f"  描述: {tool['description']}")
            if 'inputSchema' in tool:
                properties = tool['inputSchema'].get('properties', {})
                print(f"  参数: {list(properties.keys())}")
        print()
        return tools
    else:
        print(f"✗ 工具列表获取失败")
        print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return []

def test_invoke_tool(gateway_url, token, tool_name, arguments):
    """测试 MCP InvokeTool API"""
    print(f"步骤 3: 调用 MCP Tool - {tool_name}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # MCP CallTool 请求
    payload = {
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': arguments
        },
        'id': 2
    }
    
    print(f"  请求参数: {json.dumps(arguments, ensure_ascii=False)}")
    
    response = requests.post(gateway_url, headers=headers, json=payload, timeout=60)
    
    print(f"  HTTP 状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 工具调用成功")
        
        if 'result' in result:
            tool_result = result['result']
            if 'content' in tool_result:
                for content in tool_result['content']:
                    if content.get('type') == 'text':
                        text = content.get('text', '')
                        # 只显示前500字符
                        print(f"\n  结果预览:")
                        print(f"  {text[:500]}...")
            else:
                print(f"\n  完整结果:")
                print(f"  {json.dumps(tool_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"\n  响应:")
            print(f"  {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    else:
        print(f"✗ 工具调用失败")
        print(f"  错误: {response.text}")
        return None

def main():
    """主测试流程"""
    print("="*60)
    print("Bocha Web Search Gateway 测试")
    print("="*60)
    print()
    
    try:
        # 加载配置
        config = load_config()
        
        # 检查必要的配置
        required_keys = ['CLIENT_ID', 'CLIENT_SECRET', 'TOKEN_ENDPOINT', 'SCOPES', 'GATEWAY_URL']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"错误: 配置文件缺少以下参数: {', '.join(missing_keys)}")
            print("请确保已完整运行部署脚本")
            sys.exit(1)
        
        client_id = config['CLIENT_ID']
        client_secret = config['CLIENT_SECRET']
        token_endpoint = config['TOKEN_ENDPOINT']
        scopes = config['SCOPES']
        gateway_url = config['GATEWAY_URL']
        
        print(f"Gateway URL: {gateway_url}")
        print(f"Client ID: {client_id[:20]}...")
        print()
        
        # 步骤 1: 获取 Token
        token = get_token(client_id, client_secret, token_endpoint, scopes)
        
        # 步骤 2: 列出可用工具
        tools = test_list_tools(gateway_url, token)
        
        if not tools:
            print("⚠ 警告: 未找到可用工具")
            print("这可能是因为 Gateway Target 尚未完全就绪")
            print("请等待几分钟后重试")
            sys.exit(1)
        
        # 步骤 3: 调用博查搜索工具
        print("="*60)
        
        # 找到博查搜索工具
        tool_name = None
        for tool in tools:
            if 'bocha_web_search' in tool['name']:
                tool_name = tool['name']
                break
        
        if tool_name:
            test_arguments = {
                'query': 'Amazon Bedrock AgentCore',
                'max_results': 3
            }
            
            result = test_invoke_tool(gateway_url, token, tool_name, test_arguments)
            
            if result:
                print()
                print("="*60)
                print("✅ 测试完全成功！")
                print("="*60)
                print()
                print("Gateway 已就绪并可以正常使用！")
                print("现在可以在 Amazon Quick Suite 中配置此 Integration。")
            else:
                print()
                print("⚠ 工具调用返回了错误")
                print("请检查:")
                print("1. Lambda 函数是否正确部署")
                print("2. 博查 API Key 是否正确")
                print("3. Lambda 日志: aws logs tail /aws/lambda/BochaWebSearchFunction --follow --region us-east-1")
        else:
            print(f"⚠ 未找到博查搜索工具")
            print(f"可用工具: {[t['name'] for t in tools]}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ HTTP 请求失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
