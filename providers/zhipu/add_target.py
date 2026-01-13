#!/usr/bin/env python3
"""
将智谱 Web Search 添加为 AgentCore Gateway Target
"""

import boto3
import json
import sys
import os

def load_config(config_file='../../config.txt'):
    """加载配置文件"""
    config = {}
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        print("请先运行基础设施部署: ./deploy_infrastructure.sh")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key] = value
    
    return config

def get_lambda_arn(region='us-east-1'):
    """获取智谱 Lambda 函数的 ARN"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    function_name = 'ZhipuWebSearchFunction'
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"错误: 无法找到 Lambda 函数 {function_name}")
        print(f"详情: {str(e)}")
        print(f"\n请先运行: cd providers/zhipu && ./deploy.sh")
        sys.exit(1)

def create_gateway_target(gateway_id, lambda_arn, region='us-east-1'):
    """创建 Gateway Target"""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    # 提取 Gateway ID（如果是完整 ARN）
    if 'gateway/' in gateway_id:
        gateway_id = gateway_id.split('gateway/')[-1]
    
    print(f"为 Gateway {gateway_id} 添加智谱 Target...")
    
    # 定义智谱搜索工具
    tool_definition = {
        'name': 'zhipu_web_search',
        'description': '智谱 Web Search - 专为大模型优化的搜索引擎，支持多种搜索引擎（基础版/高级版/搜狗/夸克）和时间范围过滤，具有增强的意图识别能力。',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': '搜索查询关键词'
                },
                'max_results': {
                    'type': 'integer',
                    'description': '返回结果数量（1-50，默认10）'
                },
                'search_engine': {
                    'type': 'string',
                    'description': '搜索引擎类型，可选值：search_std（基础版，默认）、search_pro（高级版）、search_pro_sogou（搜狗）、search_pro_quark（夸克）'
                },
                'recency_filter': {
                    'type': 'string',
                    'description': '时间范围过滤，可选值：oneDay（一天内）、oneWeek（一周内）、oneMonth（一个月内）、oneYear（一年内）、noLimit（不限制，默认）'
                },
                'domain_filter': {
                    'type': 'string',
                    'description': '域名白名单过滤，限定搜索范围（如：www.example.com）'
                },
                'content_size': {
                    'type': 'string',
                    'description': '摘要长度控制，可选值：low（简短）、medium（中等，默认）、high（详细）'
                }
            },
            'required': ['query']
        }
    }

    # 创建 Target 配置（MCP 格式）
    target_config = {
        'mcp': {
            'lambda': {
                'lambdaArn': lambda_arn,
                'toolSchema': {
                    'inlinePayload': [tool_definition]
                }
            }
        }
    }
    
    # 配置凭证提供者
    credential_config = [{
        'credentialProviderType': 'GATEWAY_IAM_ROLE'
    }]
    
    try:
        response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name='ZhipuWebSearchTarget',
            targetConfiguration=target_config,
            credentialProviderConfigurations=credential_config
        )
        
        print("✓ 智谱 Gateway Target 创建成功！")
        print(f"\nTarget ID: {response['targetId']}")
        print(f"Target Name: ZhipuWebSearchTarget")
        print(f"Tool Name: zhipu_web_search")
        print(f"\n在 Quick Suite 中使用的完整工具名称:")
        print(f"ZhipuWebSearchTarget___zhipu_web_search")
        
        return response
        
    except Exception as e:
        if 'ConflictException' in str(e) or 'already exists' in str(e):
            print("⚠ Target 已存在，尝试更新...")
            
            # 列出现有 Targets
            try:
                list_response = client.list_gateway_targets(
                    gatewayIdentifier=gateway_id
                )
                
                # 查找智谱 Target
                targets = list_response.get('items', list_response.get('gatewayTargets', []))
                zhipu_target = None
                for target in targets:
                    if target.get('name') == 'ZhipuWebSearchTarget':
                        zhipu_target = target
                        break
                
                if zhipu_target:
                    target_id = zhipu_target['targetId']
                    print(f"找到现有 Target ID: {target_id}")
                    
                    # 更新 Target
                    update_response = client.update_gateway_target(
                        gatewayIdentifier=gateway_id,
                        targetIdentifier=target_id,
                        targetConfiguration=target_config
                    )
                    
                    print("✓ 智谱 Gateway Target 更新成功！")
                    return {'targetId': target_id}
                else:
                    print("错误: 无法找到现有的智谱 Target")
                    raise e
                    
            except Exception as update_error:
                print(f"更新失败: {str(update_error)}")
                raise e
        else:
            print(f"错误: 创建 Target 失败")
            print(f"详情: {str(e)}")
            raise e

def main():
    print("=" * 60)
    print("添加智谱 Web Search 到 AgentCore Gateway")
    print("=" * 60)
    print()
    
    # 加载配置
    print("步骤 1: 加载配置...")
    config = load_config()
    
    region = config.get('REGION', 'us-east-1')
    gateway_arn = config.get('GATEWAY_ARN', '')
    
    if not gateway_arn:
        print("错误: 未找到 GATEWAY_ARN 配置")
        print("请先运行基础设施部署: ./deploy_infrastructure.sh")
        sys.exit(1)
    
    print(f"✓ 配置加载完成")
    print(f"  Region: {region}")
    print(f"  Gateway ARN: {gateway_arn}")
    print()
    
    # 获取智谱 Lambda ARN
    print("步骤 2: 获取智谱 Lambda 函数 ARN...")
    lambda_arn = get_lambda_arn(region)
    print(f"✓ Lambda ARN: {lambda_arn}")
    print()
    
    # 创建 Gateway Target
    print("步骤 3: 创建 Gateway Target...")
    result = create_gateway_target(gateway_arn, lambda_arn, region)
    print()
    
    # 保存配置
    print("步骤 4: 保存配置...")
    config_file = '../../config.txt'
    with open(config_file, 'a') as f:
        f.write(f"ZHIPU_TARGET_ID={result['targetId']}\n")
    print("✓ 配置已保存到 config.txt")
    print()
    
    print("=" * 60)
    print("部署完成！")
    print("=" * 60)
    print()
    print("现在可以在 Amazon Quick Suite 中使用智谱搜索了！")
    print()
    print("测试提示词示例:")
    print("  1. 使用智谱搜索查找关于 AWS Lambda 的最新信息")
    print("  2. 用智谱搜索一下人工智能的新闻资讯")
    print("  3. 智谱搜索 Amazon Bedrock 的相关内容")
    print()
    print("搜索引擎选项:")
    print("  - search_std: 基础版（0.01元/次）")
    print("  - search_pro: 高级版（0.03元/次）")
    print("  - search_pro_sogou: 搜狗版（0.05元/次）")
    print("  - search_pro_quark: 夸克版（0.05元/次）")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
