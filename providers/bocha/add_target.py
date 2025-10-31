#!/usr/bin/env python3
"""
将博查 Web Search 添加为 AgentCore Gateway Target
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
    """获取博查 Lambda 函数的 ARN"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    function_name = 'BochaWebSearchFunction'
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"错误: 无法找到 Lambda 函数 {function_name}")
        print(f"详情: {str(e)}")
        print(f"\n请先运行: cd providers/bocha && ./deploy.sh")
        sys.exit(1)

def create_gateway_target(gateway_id, lambda_arn, region='us-east-1'):
    """创建 Gateway Target"""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    # 提取 Gateway ID（如果是完整 ARN）
    if 'gateway/' in gateway_id:
        gateway_id = gateway_id.split('gateway/')[-1]
    
    print(f"为 Gateway {gateway_id} 添加博查 Target...")
    
    # 定义博查搜索工具
    tool_definition = {
        'name': 'bocha_web_search',
        'description': '博查 Web Search - 实时网页搜索，适合查找最新资讯、新闻和通用网页内容。',
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
            name='BochaWebSearchTarget',
            targetConfiguration=target_config,
            credentialProviderConfigurations=credential_config
        )
        
        print("✓ 博查 Gateway Target 创建成功！")
        print(f"\nTarget ID: {response['targetId']}")
        print(f"Target Name: BochaWebSearchTarget")
        print(f"Tool Name: bocha_web_search")
        print(f"\n在 Quick Suite 中使用的完整工具名称:")
        print(f"BochaWebSearchTarget___bocha_web_search")
        
        return response
        
    except Exception as e:
        if 'ConflictException' in str(e) or 'already exists' in str(e):
            print("⚠ Target 已存在，尝试更新...")
            
            # 列出现有 Targets
            try:
                list_response = client.list_gateway_targets(
                    gatewayIdentifier=gateway_id
                )
                
                # 查找博查 Target（尝试两种可能的字段名）
                targets = list_response.get('items', list_response.get('gatewayTargets', []))
                bocha_target = None
                for target in targets:
                    if target.get('name') == 'BochaWebSearchTarget':
                        bocha_target = target
                        break
                
                if bocha_target:
                    target_id = bocha_target['targetId']
                    print(f"找到现有 Target ID: {target_id}")
                    
                    # 更新 Target
                    update_response = client.update_gateway_target(
                        gatewayIdentifier=gateway_id,
                        targetIdentifier=target_id,
                        targetConfiguration=target_config
                    )
                    
                    print("✓ 博查 Gateway Target 更新成功！")
                    return update_response
                else:
                    print("错误: 无法找到现有的博查 Target")
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
    print("添加博查 Web Search 到 AgentCore Gateway")
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
    
    # 获取博查 Lambda ARN
    print("步骤 2: 获取博查 Lambda 函数 ARN...")
    lambda_arn = get_lambda_arn(region)
    print(f"✓ Lambda ARN: {lambda_arn}")
    print()
    
    # 创建 Gateway Target
    print("步骤 3: 创建 Gateway Target...")
    result = create_gateway_target(gateway_arn, lambda_arn, region)
    print()
    
    # 保存配置
    print("步骤 4: 保存配置...")
    with open('../../config.txt', 'a') as f:
        f.write(f"\n# 博查配置\n")
        f.write(f"BOCHA_TARGET_ID={result['targetId']}\n")
        f.write(f"BOCHA_LAMBDA_ARN={lambda_arn}\n")
    print("✓ 配置已保存到 config.txt")
    print()
    
    print("=" * 60)
    print("部署完成！")
    print("=" * 60)
    print()
    print("现在可以在 Amazon Quick Suite 中使用博查搜索了！")
    print()
    print("测试提示词示例:")
    print("  1. 使用博查搜索查找关于 AWS Lambda 的最新信息")
    print("  2. 搜索一下人工智能的新闻资讯")
    print("  3. 用博查查找 Amazon Bedrock 的相关内容")
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
