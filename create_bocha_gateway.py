import boto3
import json
import sys
import time

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
        print("请先运行: ./setup_cognito_s2s_bocha.sh <region>")
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
        time.sleep(10)  # 等待角色创建
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"角色 {role_name} 已存在，使用现有角色")
        role = iam_client.get_role(RoleName=role_name)
    
    # 附加策略
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName="AgentCoreGatewayPolicy",
        PolicyDocument=json.dumps(role_policy)
    )
    
    return role

def create_gateway():
    """创建 AgentCore Gateway"""
    
    # 加载配置
    config = load_config()
    
    required_keys = ['REGION', 'POOL_ID', 'CLIENT_ID', 'DISCOVERY_URL', 'LAMBDA_ARN']
    for key in required_keys:
        if key not in config:
            print(f"错误: 配置文件中缺少 {key}")
            sys.exit(1)
    
    region = config['REGION']
    pool_id = config['POOL_ID']
    client_id = config['CLIENT_ID']
    discovery_url = config['DISCOVERY_URL']
    lambda_arn = config['LAMBDA_ARN']
    
    print(f"创建 AgentCore Gateway...")
    print(f"  Region: {region}")
    print(f"  Lambda ARN: {lambda_arn}")
    print(f"  Cognito Pool ID: {pool_id}")
    print()
    
    # 创建 Bedrock AgentCore Control 客户端
    try:
        client = boto3.client('bedrock-agentcore-control', region_name=region)
    except Exception as e:
        print(f"错误: 无法创建 bedrock-agentcore-control 客户端: {str(e)}")
        print("提示: 请确保 boto3 已更新到最新版本: pip install --upgrade boto3")
        sys.exit(1)
    
    # 定义 MCP 工具 Schema
    mcp_schema = [
        {
            "name": "bocha_web_search",
            "description": "Search the web using Bocha Web Search API. Use this tool when you need to find current information, news, articles, or any web content. It returns relevant search results with titles, URLs, and snippets.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific and clear about what you're looking for."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default: 10, max: 50)"
                    }
                },
                "required": ["query"]
            }
        }
    ]
    
    # 创建 Gateway IAM 角色
    print("正在创建 Gateway IAM 角色...")
    gateway_role = create_gateway_role('bocha-gateway', region)
    gateway_role_arn = gateway_role['Role']['Arn']
    print(f"✓ Gateway Role ARN: {gateway_role_arn}")
    
    # 创建 Gateway
    try:
        print("\n正在创建 Gateway...")
        
        # 配置 Cognito JWT 认证
        auth_config = {
            'customJWTAuthorizer': {
                'allowedClients': [client_id],
                'discoveryUrl': discovery_url
            }
        }
        
        response = client.create_gateway(
            name='BochaWebSearchGateway',
            roleArn=gateway_role_arn,
            protocolType='MCP',
            authorizerType='CUSTOM_JWT',
            authorizerConfiguration=auth_config,
            description='Bocha Web Search Gateway with Cognito S2S Authentication'
        )
        
        gateway_id = response['gatewayId']
        print(f"✓ Gateway 创建成功!")
        print(f"Gateway ID: {gateway_id}")
        
        # 等待 Gateway 状态变为 AVAILABLE
        print("\n等待 Gateway 状态变为 AVAILABLE...")
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
        
        # 创建 Gateway Target（添加 Lambda 作为工具）
        print("\n正在创建 Gateway Target...")
        
        # 配置 Lambda Target（MCP格式）
        lambda_target_config = {
            "mcp": {
                "lambda": {
                    "lambdaArn": lambda_arn,
                    "toolSchema": {
                        "inlinePayload": mcp_schema
                    }
                }
            }
        }
        
        # 配置凭证提供者（使用Gateway IAM角色）
        credential_config = [
            {
                "credentialProviderType": "GATEWAY_IAM_ROLE"
            }
        ]
        
        target_response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name='BochaWebSearchTarget',
            description='Bocha Web Search Lambda Target',
            targetConfiguration=lambda_target_config,
            credentialProviderConfigurations=credential_config
        )
        
        print(f"✓ Gateway Target 创建成功!")
        print(f"Target ID: {target_response['targetId']}")
        
        # 获取 Gateway 详情
        print("\n正在获取 Gateway URL...")
        gateway_details = client.get_gateway(gatewayIdentifier=gateway_id)
        gateway_url = gateway_details['gatewayUrl']
        
        print(f"Gateway URL: {gateway_url}")
        
        # 保存配置到文件
        with open('cognito-bocha-s2s.txt', 'a') as f:
            f.write(f"\nGATEWAY_ID={gateway_id}\n")
            f.write(f"GATEWAY_URL={gateway_url}\n")
        
        print("\n✓ 配置已保存到 cognito-bocha-s2s.txt")
        
        print("\n" + "="*60)
        print("Gateway 创建完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 登录 Amazon Quick Suite")
        print("2. 转到 Integrations > Actions > Model Context Protocol")
        print("3. 创建 MCP Integration，使用以下配置：")
        print(f"   - MCP Endpoint: {gateway_url}")
        print(f"   - Client ID: {client_id}")
        print(f"   - Client Secret: (从 cognito-bocha-s2s.txt 获取)")
        print(f"   - Token URL: {config.get('TOKEN_ENDPOINT', 'N/A')}")
        
        return gateway_id, gateway_url
        
    except Exception as e:
        print(f"\n✗ 创建 Gateway 失败: {str(e)}")
        print("\n可能的原因：")
        print("1. Lambda 函数不存在或 ARN 不正确")
        print("2. 没有足够的 IAM 权限")
        print("3. Bedrock AgentCore 服务在该区域不可用")
        print("4. boto3 版本过旧，请运行: pip install --upgrade boto3")
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
