#!/usr/bin/env python3
"""
创建 AgentCore Gateway（不包含 Target）
Target 将由各个 Provider 的 add_target.py 单独添加
"""

import boto3
import json
import sys
import time
import os

def load_config():
    """从配置文件加载 Cognito 配置"""
    config = {}
    try:
        with open('cognito-bocha-s2s.txt', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#') and not line.startswith('='):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
        return config
    except FileNotFoundError:
        print("错误: cognito-bocha-s2s.txt 文件未找到")
        print("请先运行: ./setup_cognito.sh <region>")
        sys.exit(1)

def create_gateway_role(gateway_name, region):
    """创建 Gateway IAM 角色"""
    iam_client = boto3.client('iam', region_name=region)
    sts_client = boto3.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    
    role_name = f'agentcore-{gateway_name}-role'
    
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:*",
                "agent-credential-provider:*",
                "iam:PassRole",
                "secretsmanager:GetSecretValue",
                "lambda:InvokeFunction"
            ],
            "Resource": "*"
        }]
    }

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AssumeRolePolicy",
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": f"{account_id}"
                },
                "ArnLike": {
                    "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                }
            }
        }]
    }

    try:
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
        )
        print(f"✓ 创建 IAM 角色: {role_name}")
        time.sleep(10)  # 等待角色创建
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"⚠ 角色已存在，使用现有角色: {role_name}")
        role = iam_client.get_role(RoleName=role_name)
    
    # 附加策略
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName="AgentCoreGatewayPolicy",
        PolicyDocument=json.dumps(role_policy)
    )
    
    return role

def create_gateway():
    """创建 AgentCore Gateway（不包含 Target）"""
    
    # 加载配置
    config = load_config()
    
    required_keys = ['REGION', 'POOL_ID', 'CLIENT_ID', 'DISCOVERY_URL']
    for key in required_keys:
        if key not in config:
            print(f"错误: 配置文件中缺少 {key}")
            sys.exit(1)
    
    region = config['REGION']
    pool_id = config['POOL_ID']
    client_id = config['CLIENT_ID']
    discovery_url = config['DISCOVERY_URL']
    
    print("="*60)
    print("创建 AgentCore Gateway")
    print("="*60)
    print()
    print(f"Region: {region}")
    print(f"Cognito Pool ID: {pool_id}")
    print(f"Client ID: {client_id}")
    print()
    
    # 创建 Bedrock AgentCore Control 客户端
    try:
        client = boto3.client('bedrock-agentcore-control', region_name=region)
    except Exception as e:
        print(f"错误: 无法创建 bedrock-agentcore-control 客户端: {str(e)}")
        print("提示: 请确保 boto3 已更新到最新版本: pip install --upgrade boto3")
        sys.exit(1)
    
    # 创建 Gateway IAM 角色
    print("步骤 1: 创建 Gateway IAM 角色...")
    gateway_role = create_gateway_role('ai-search-gateway', region)
    gateway_role_arn = gateway_role['Role']['Arn']
    print(f"✓ Gateway Role ARN: {gateway_role_arn}")
    print()
    
    # 创建 Gateway
    try:
        print("步骤 2: 创建 Gateway...")
        
        # 配置 Cognito JWT 认证
        auth_config = {
            'customJWTAuthorizer': {
                'allowedClients': [client_id],
                'discoveryUrl': discovery_url
            }
        }
        
        try:
            response = client.create_gateway(
                name='AISearchGateway',
                roleArn=gateway_role_arn,
                protocolType='MCP',
                authorizerType='CUSTOM_JWT',
                authorizerConfiguration=auth_config,
                description='AI Search Gateway for multiple search providers'
            )
            
            gateway_id = response['gatewayId']
            print(f"✓ Gateway 创建成功!")
            print(f"  Gateway ID: {gateway_id}")
            print()
            
        except client.exceptions.ConflictException:
            print("⚠ Gateway 已存在，正在获取现有 Gateway 信息...")
            
            # 列出所有 Gateways
            list_response = client.list_gateways()
            all_gateways = list_response.get('gateways', [])
            
            if not all_gateways:
                print("✗ 未找到任何 Gateway")
                print("请检查 AWS 账户中的 Gateway 列表")
                raise
            
            # 打印所有找到的 Gateways
            print(f"找到 {len(all_gateways)} 个 Gateway:")
            for idx, gw in enumerate(all_gateways, 1):
                print(f"  {idx}. {gw.get('name', 'N/A')} - {gw.get('gatewayId', 'N/A')}")
            
            # 优先查找 'AISearchGateway'，否则使用任何包含 'Search' 或 'Bocha' 的
            gateway_found = None
            for gw in all_gateways:
                gw_name = gw.get('name', '')
                if gw_name == 'AISearchGateway':
                    gateway_found = gw
                    break
                elif 'Search' in gw_name or 'Bocha' in gw_name or 'Gateway' in gw_name:
                    gateway_found = gw
            
            # 如果还没找到，使用第一个
            if not gateway_found and all_gateways:
                gateway_found = all_gateways[0]
            
            if not gateway_found:
                print("✗ 无法确定使用哪个 Gateway")
                raise
            
            gateway_id = gateway_found['gatewayId']
            gateway_name = gateway_found.get('name', 'N/A')
            print(f"\n✓ 使用现有 Gateway: {gateway_name}")
            print(f"  Gateway ID: {gateway_id}")
            print()
        
        # 等待 Gateway 状态变为 AVAILABLE
        print("步骤 3: 等待 Gateway 就绪...")
        max_attempts = 30
        for attempt in range(max_attempts):
            gateway_status = client.get_gateway(gatewayIdentifier=gateway_id)
            status = gateway_status['status']
            print(f"  当前状态: {status} ({attempt + 1}/{max_attempts})")
            
            if status in ['AVAILABLE', 'READY']:
                print("✓ Gateway 已就绪!")
                break
            elif status in ['FAILED', 'DELETING']:
                print(f"✗ Gateway 状态异常: {status}")
                sys.exit(1)
            
            time.sleep(5)
        else:
            print("✗ 等待超时，Gateway 未就绪")
            sys.exit(1)
        
        print()
        
        # 获取 Gateway 详情
        print("步骤 4: 获取 Gateway 信息...")
        gateway_details = client.get_gateway(gatewayIdentifier=gateway_id)
        gateway_url = gateway_details['gatewayUrl']
        
        print(f"✓ Gateway URL: {gateway_url}")
        print()
        
        # 获取 account ID
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        gateway_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:gateway/{gateway_id}"
        
        # 保存配置到文件
        print("步骤 5: 保存配置...")
        with open('cognito-bocha-s2s.txt', 'a') as f:
            f.write(f"\n# Gateway 配置\n")
            f.write(f"GATEWAY_ARN={gateway_arn}\n")
            f.write(f"GATEWAY_ID={gateway_id}\n")
            f.write(f"GATEWAY_URL={gateway_url}\n")
        
        print("✓ 配置已保存到 cognito-bocha-s2s.txt")
        print()
        
        print("="*60)
        print("Gateway 创建完成！")
        print("="*60)
        print()
        print("Gateway 信息:")
        print(f"  ARN: {gateway_arn}")
        print(f"  ID: {gateway_id}")
        print(f"  URL: {gateway_url}")
        print()
        print("下一步:")
        print("  1. 部署 AI Search Providers（Lambda 函数）")
        print("  2. 将 Lambda 添加为 Gateway Targets")
        print("  3. 在 Amazon Quick Suite 中配置 MCP Integration")
        print()
        print("部署 Provider 示例:")
        print("  cd providers/bocha")
        print("  export BOCHA_API_KEY='your-key'")
        print("  ./deploy.sh")
        print("  python3 add_target.py")
        print()
        
        return gateway_id, gateway_url
        
    except Exception as e:
        print(f"\n✗ 创建 Gateway 失败: {str(e)}")
        print("\n可能的原因：")
        print("1. 没有足够的 IAM 权限")
        print("2. Bedrock AgentCore 服务在该区域不可用")
        print("3. boto3 版本过旧，请运行: pip install --upgrade boto3")
        print("4. Cognito 配置不正确")
        raise

if __name__ == "__main__":
    try:
        create_gateway()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
