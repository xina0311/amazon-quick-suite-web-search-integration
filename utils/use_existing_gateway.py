#!/usr/bin/env python3
"""
使用现有的 Gateway 并保存配置
"""

import boto3
import json
import sys

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
        sys.exit(1)

def main():
    # 加载配置
    config = load_config()
    region = config.get('REGION', 'us-east-1')
    
    print("="*60)
    print("使用现有 Gateway")
    print("="*60)
    print()
    
    # 创建客户端
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    
    # 列出所有 Gateways
    print("列出所有 Gateway...")
    list_response = client.list_gateways()
    all_gateways = list_response.get('items', [])
    
    if not all_gateways:
        print("✗ 未找到任何 Gateway")
        sys.exit(1)
    
    print(f"\n找到 {len(all_gateways)} 个 Gateway:")
    for idx, gw in enumerate(all_gateways, 1):
        print(f"  {idx}. {gw.get('name')} ({gw.get('gatewayId')}) - Status: {gw.get('status')}")
    
    # 使用第一个 READY 状态的 Gateway
    gateway = None
    for gw in all_gateways:
        if gw.get('status') in ['READY', 'AVAILABLE']:
            gateway = gw
            break
    
    if not gateway:
        print("\n✗ 未找到 READY 状态的 Gateway")
        sys.exit(1)
    
    gateway_id = gateway['gatewayId']
    gateway_name = gateway['name']
    
    print(f"\n✓ 使用 Gateway: {gateway_name}")
    print(f"  ID: {gateway_id}")
    print(f"  Status: {gateway['status']}")
    
    # 获取完整信息
    print("\n获取 Gateway 详细信息...")
    gateway_details = client.get_gateway(gatewayIdentifier=gateway_id)
    gateway_url = gateway_details['gatewayUrl']
    gateway_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:gateway/{gateway_id}"
    
    print(f"✓ Gateway URL: {gateway_url}")
    print(f"✓ Gateway ARN: {gateway_arn}")
    
    # 保存到配置文件
    print("\n保存配置...")
    
    # 检查是否已有 Gateway 配置
    if 'GATEWAY_ARN' in config:
        print("⚠ 配置文件中已有 Gateway 配置，将更新")
    
    # 读取文件，更新或添加 Gateway 配置
    with open('cognito-bocha-s2s.txt', 'r') as f:
        lines = f.readlines()
    
    # 移除旧的 Gateway 配置
    filtered_lines = []
    skip_gateway_section = False
    for line in lines:
        if line.strip().startswith('# Gateway'):
            skip_gateway_section = True
        elif line.strip().startswith('#') and skip_gateway_section:
            skip_gateway_section = False
        elif not skip_gateway_section and not line.startswith('GATEWAY_'):
            filtered_lines.append(line)
    
    # 添加新的 Gateway 配置
    with open('cognito-bocha-s2s.txt', 'w') as f:
        f.writelines(filtered_lines)
        f.write(f"\n# Gateway 配置\n")
        f.write(f"GATEWAY_ARN={gateway_arn}\n")
        f.write(f"GATEWAY_ID={gateway_id}\n")
        f.write(f"GATEWAY_URL={gateway_url}\n")
    
    print("✓ 配置已保存到 cognito-bocha-s2s.txt")
    
    # 同时更新到根目录的 config.txt（如果存在）
    try:
        with open('../config.txt', 'r') as f:
            lines = f.readlines()
        
        filtered_lines = []
        for line in lines:
            if not line.startswith('GATEWAY_'):
                filtered_lines.append(line)
        
        with open('../config.txt', 'w') as f:
            f.writelines(filtered_lines)
            f.write(f"\n# Gateway 配置\n")
            f.write(f"GATEWAY_ARN={gateway_arn}\n")
            f.write(f"GATEWAY_ID={gateway_id}\n")
            f.write(f"GATEWAY_URL={gateway_url}\n")
        
        print("✓ 配置已更新到 ../config.txt")
    except FileNotFoundError:
        print("⚠ ../config.txt 不存在，仅更新了 cognito-bocha-s2s.txt")
    
    print()
    print("="*60)
    print("配置完成！")
    print("="*60)
    print()
    print("Gateway 信息:")
    print(f"  名称: {gateway_name}")
    print(f"  ID: {gateway_id}")
    print(f"  ARN: {gateway_arn}")
    print(f"  URL: {gateway_url}")
    print()
    print("现在可以添加 Providers 到 Gateway:")
    print("  cd ../providers/bocha")
    print("  python3 add_target.py")
    print()

if __name__ == "__main__":
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
