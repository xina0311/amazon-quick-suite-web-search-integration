"""
通用 AI Search Provider Lambda 函数模板

使用说明：
1. 复制此文件并重命名为 {provider}_lambda_function.py
2. 修改配置部分（API_KEY, API_ENDPOINT）
3. 实现 call_provider_api 函数
4. 实现 format_results 函数
5. 部署到 AWS Lambda

示例：
- metaso_lambda_function.py
- cloudsway_lambda_function.py
"""

import json
import requests
import os

# ============================================================================
# 配置部分 - 请根据实际 Provider 修改
# ============================================================================

PROVIDER_NAME = "provider"  # 修改为实际 Provider 名称，如: bocha, metaso, cloudsway
API_KEY = "your-api-key-here"  # 从环境变量或 Secrets Manager 获取
API_ENDPOINT = "https://api.provider.com/v1/search"  # 修改为实际 API endpoint

# ============================================================================
# 主处理函数
# ============================================================================

def lambda_handler(event, context):
    """
    Lambda 函数主入口
    处理来自 AgentCore Gateway 的 MCP 工具调用请求
    
    Args:
        event: Gateway 传递的参数（直接包含工具参数）
        context: Lambda 上下文
        
    Returns:
        dict: MCP 格式的响应
    """
    print(f"[{PROVIDER_NAME}] Received event: {json.dumps(event)}")
    
    try:
        # 从 event 提取参数
        query = event.get('query', '')
        max_results = event.get('max_results', 10)
        
        # 可选参数（根据 Provider 支持的功能添加）
        search_type = event.get('search_type', 'web')
        language = event.get('language', 'zh')
        
        print(f"[{PROVIDER_NAME}] Query: {query}, Max Results: {max_results}")
        
        # 参数验证
        if not query:
            return error_response('Query parameter is required')
        
        if max_results < 1 or max_results > 50:
            return error_response('max_results must be between 1 and 50')
        
        # 调用 Provider API
        search_results = call_provider_api(
            query=query,
            count=max_results,
            search_type=search_type,
            language=language
        )
        
        # 格式化结果
        formatted_results = format_results(search_results)
        
        # 返回成功响应
        return success_response(formatted_results)
        
    except requests.exceptions.Timeout:
        print(f"[{PROVIDER_NAME}] API timeout")
        return error_response('Search request timeout')
        
    except requests.exceptions.RequestException as e:
        print(f"[{PROVIDER_NAME}] API error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
        return error_response(f'API request failed: {str(e)}')
        
    except Exception as e:
        print(f"[{PROVIDER_NAME}] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f'Internal error: {str(e)}')

# ============================================================================
# API 调用函数 - 需要根据实际 Provider 实现
# ============================================================================

def call_provider_api(query, count, search_type='web', language='zh'):
    """
    调用 Provider 的搜索 API
    
    需要根据实际 Provider 的 API 文档实现此函数
    
    Args:
        query: 搜索关键词
        count: 返回结果数量
        search_type: 搜索类型（web, academic, news 等）
        language: 语言
        
    Returns:
        dict: Provider API 的原始响应
        
    示例实现（根据实际 API 修改）：
    """
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 构建请求体 - 根据 Provider API 文档修改
    payload = {
        'query': query,
        'count': count,
        # 添加 Provider 特定参数
        # 例如：
        # 'type': search_type,
        # 'language': language,
        # 'freshness': 'noLimit',
        # 'summary': True,
    }
    
    print(f"[{PROVIDER_NAME}] Calling API: {API_ENDPOINT}")
    print(f"[{PROVIDER_NAME}] Payload: {json.dumps(payload)}")
    
    # 发送请求
    response = requests.post(
        API_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=30  # 30秒超时
    )
    
    print(f"[{PROVIDER_NAME}] Response status: {response.status_code}")
    
    # 检查响应
    response.raise_for_status()
    
    # 解析响应
    result = response.json()
    print(f"[{PROVIDER_NAME}] Response size: {len(str(result))} chars")
    
    return result

# ============================================================================
# 结果格式化函数 - 需要根据实际 Provider 响应格式实现
# ============================================================================

def format_results(api_response):
    """
    将 Provider API 响应格式化为可读文本
    
    需要根据实际 Provider 的响应格式实现此函数
    
    Args:
        api_response: Provider API 的原始响应
        
    Returns:
        str: 格式化后的 Markdown 文本
        
    常见的响应格式示例：
    
    格式 1 - 博查格式:
    {
        "data": {
            "webPages": {
                "value": [
                    {"name": "...", "url": "...", "summary": "..."}
                ]
            }
        }
    }
    
    格式 2 - 通用格式:
    {
        "results": [
            {"title": "...", "url": "...", "snippet": "..."}
        ]
    }
    """
    
    try:
        # 示例实现 1: 博查格式
        if 'data' in api_response and 'webPages' in api_response['data']:
            web_pages = api_response['data']['webPages'].get('value', [])
            
            if not web_pages:
                return f"# {PROVIDER_NAME} 搜索结果\n\n未找到相关结果。"
            
            formatted = f"# {PROVIDER_NAME} 搜索结果\n\n"
            formatted += f"共找到 {len(web_pages)} 个结果\n\n"
            
            for idx, result in enumerate(web_pages, 1):
                name = result.get('name', '无标题')
                url = result.get('url', '无链接')
                summary = result.get('summary', result.get('snippet', '无摘要'))
                
                formatted += f"## {idx}. {name}\n"
                formatted += f"**链接:** {url}\n"
                formatted += f"**摘要:** {summary}\n\n"
            
            return formatted
        
        # 示例实现 2: 通用格式
        elif 'results' in api_response:
            results = api_response['results']
            
            if not results:
                return f"# {PROVIDER_NAME} 搜索结果\n\n未找到相关结果。"
            
            formatted = f"# {PROVIDER_NAME} 搜索结果\n\n"
            formatted += f"共找到 {len(results)} 个结果\n\n"
            
            for idx, result in enumerate(results, 1):
                title = result.get('title', result.get('name', '无标题'))
                url = result.get('url', '无链接')
                snippet = result.get('snippet', result.get('description', '无摘要'))
                
                formatted += f"## {idx}. {title}\n"
                formatted += f"**链接:** {url}\n"
                formatted += f"**摘要:** {snippet}\n\n"
            
            return formatted
        
        # 如果格式不匹配，返回原始 JSON（用于调试）
        else:
            return f"# {PROVIDER_NAME} 搜索结果\n\n```json\n{json.dumps(api_response, indent=2, ensure_ascii=False)}\n```"
            
    except Exception as e:
        print(f"[{PROVIDER_NAME}] Format error: {str(e)}")
        return f"结果格式化失败: {str(e)}\n\n原始数据: {str(api_response)[:500]}"

# ============================================================================
# 响应格式化辅助函数
# ============================================================================

def success_response(text):
    """
    返回成功的 MCP 格式响应
    
    Args:
        text: 格式化后的搜索结果文本
        
    Returns:
        dict: Lambda 响应（MCP 格式）
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'content': [
                {
                    'type': 'text',
                    'text': text
                }
            ]
        }, ensure_ascii=False)
    }

def error_response(error_message):
    """
    返回错误响应
    
    Args:
        error_message: 错误信息
        
    Returns:
        dict: Lambda 错误响应
    """
    return {
        'statusCode': 500,
        'body': json.dumps({
            'error': error_message,
            'provider': PROVIDER_NAME
        }, ensure_ascii=False)
    }

# ============================================================================
# 测试入口（可选）
# ============================================================================

if __name__ == "__main__":
    # 本地测试
    test_event = {
        'query': 'test query',
        'max_results': 5
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
