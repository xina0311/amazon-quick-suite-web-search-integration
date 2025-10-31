#!/usr/bin/env python3
"""
将秘塔 AI Search 添加为 AgentCore Gateway Target
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
    """获取秘塔 Lambda 函数的 ARN"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    function_name = 'MetasoWebSearchFunction'
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"错误: 无法找到 Lambda 函数 {function_name}")
        print(f"详情: {str(e)}")
        print(f"\n请先运行: ./deploy_metaso_lambda.sh")
        sys.exit(1)

def create_gateway_target(gateway_id, lambda_arn, region='us-east-1'):
    """创建 Gateway Target"""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    # 提取 Gateway ID（如果是完整 ARN）
    if 'gateway/' in gateway_id:
        gateway_id = gateway_id.split('gateway/')[-1]
    
    print(f"为 Gateway {gateway_id} 添加秘塔 Target...")
    
    # 定义秘塔搜索工具
    tool_definition = {
        'name': 'metaso_web_search',
        'description': '秘塔 AI Search - 搜索网页、文档、论文、图片、视频、播客等内容。支持多种搜索范围和高级选项。',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': '搜索查询关键词'
                },
                'scope': {
                    'type': 'string',
                    'description': '搜索范围：webpage（网页）、document（文档）、paper（论文）、image（图片）、video（视频）、podcast（播客）'
                },
                'max_results': {
                    'type': 'integer',
                    'description': '返回结果数量（1-50，默认10）'
                },
                'include_summary': {
                    'type': 'boolean',
                    'description': '通过网页摘要信息提升搜索结果的召回率'
                },
                'include_raw_content': {
                    'type': 'boolean',
                    'description': '抓取所有来源网页原文'
                },
                'concise_snippet': {
                    'type': 'boolean',
                    'description': '简洁摘要'
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
            name='MetasoWebSearchTarget',
            targetConfiguration=target_config,
            credentialProviderConfigurations=credential_config
        )
        
        print("✓ 秘塔 Gateway Target 创建成功！")
        print(f"\nTarget ID: {response['targetId']}")
        print(f"Target Name: MetasoWebSearchTarget")
        print(f"Tool Name: metaso_web_search")
        print(f"\n在 Quick Suite 中使用的完整工具名称:")
        print(f"MetasoWebSearchTarget___metaso_web_search")
        
        return response
        
    except Exception as e:
        if 'ConflictException' in str(e) or 'already exists' in str(e):
            print("⚠ Target 已存在，尝试更新...")
            
            # 列出现有 Targets
            try:
                list_response = client.list_gateway_targets(
                    gatewayIdentifier=gateway_id
                )
                
                # 查找秘塔 Target
                metaso_target = None
                for target in list_response.get('gatewayTargets', []):
                    if target.get('name') == 'MetasoWebSearchTarget':
                        metaso_target = target
                        break
                
                if metaso_target:
                    target_id = metaso_target['targetId']
                    print(f"找到现有 Target ID: {target_id}")
                    
                    # 更新 Target
                    update_response = client.update_gateway_target(
                        gatewayIdentifier=gateway_id,
                        targetIdentifier=target_id,
                        targetConfiguration=target_config
                    )
                    
                    print("✓ 秘塔 Gateway Target 更新成功！")
                    return update_response
                else:
                    print("错误: 无法找到现有的秘塔 Target")
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
    print("添加秘塔 AI Search 到 AgentCore Gateway")
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
    
    # 获取秘塔 Lambda ARN
    print("步骤 2: 获取秘塔 Lambda 函数 ARN...")
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
        f.write(f"\n# 秘塔配置\n")
        f.write(f"METASO_TARGET_ID={result['targetId']}\n")
        f.write(f"METASO_LAMBDA_ARN={lambda_arn}\n")
    print("✓ 配置已保存到 config.txt")
    print()
    
    print("=" * 60)
    print("部署完成！")
    print("=" * 60)
    print()
    print("现在可以在 Amazon Quick Suite 中使用秘塔搜索了！")
    print()
    print("测试提示词示例:")
    print("  1. 使用秘塔搜索查找关于人工智能的最新信息")
    print("  2. 用秘塔搜索一下量子计算的学术论文")
    print("  3. 搜索机器学习相关的技术文档")
    print()
    print("支持的搜索范围:")
    print("  - webpage (网页)")
    print("  - document (文档)")
    print("  - paper (论文)")
    print("  - image (图片)")
    print("  - video (视频)")
    print("  - podcast (播客)")
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
