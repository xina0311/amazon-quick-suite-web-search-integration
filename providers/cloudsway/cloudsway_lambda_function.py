"""
Cloudsway AI Search Lambda 函数
基于 Deepseek 的智能网页搜索
"""

import json
import requests
import os

# ============================================================================
# 配置部分
# ============================================================================

PROVIDER_NAME = "cloudsway"
# IMPORTANT: CLOUDSWAY_ACCESS_KEY must be set as an environment variable
CLOUDSWAY_ACCESS_KEY = os.environ.get('CLOUDSWAY_ACCESS_KEY')
if not CLOUDSWAY_ACCESS_KEY:
    raise ValueError("CLOUDSWAY_ACCESS_KEY environment variable is not set. Please configure it in Lambda environment variables.")

# Cloudsway API endpoint
CLOUDSWAY_API_ENDPOINT = "https://searchapi.xiaosuai.com/search/IWPdpjaJWCYtJYpX/smart"

# ============================================================================
# 主处理函数
# ============================================================================

def lambda_handler(event, context):
    """
    Lambda 函数主入口
    处理来自 AgentCore Gateway 的 MCP 工具调用请求
    
    Args:
        event: Gateway 传递的参数
        context: Lambda 上下文
        
    Returns:
        dict: MCP 格式的响应
    """
    print(f"[Cloudsway] Received event: {json.dumps(event)}")
    
    try:
        # 从 event 提取参数
        query = event.get('query', event.get('q', ''))
        max_results = event.get('max_results', event.get('count', 10))
        freshness = event.get('freshness', '')
        offset = event.get('offset', 0)
        
        print(f"[Cloudsway] Query: {query}")
        print(f"[Cloudsway] Max Results: {max_results}")
        
        # 参数验证
        if not query:
            return error_response('Query parameter is required')
        
        if max_results < 1 or max_results > 50:
            max_results = 10  # 使用默认值
        
        # 调用 Cloudsway API
        search_results = call_cloudsway_api(
            query=query,
            count=max_results,
            freshness=freshness,
            offset=offset
        )
        
        # 格式化结果
        formatted_results = format_results(search_results)
        
        # 返回成功响应
        return success_response(formatted_results)
        
    except requests.exceptions.Timeout:
        print(f"[Cloudsway] API timeout")
        return error_response('Search request timeout')
        
    except requests.exceptions.RequestException as e:
        print(f"[Cloudsway] API error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return error_response(f'Cloudsway API request failed: {str(e)}')
        
    except Exception as e:
        print(f"[Cloudsway] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f'Internal error: {str(e)}')

# ============================================================================
# Cloudsway API 调用函数
# ============================================================================

def call_cloudsway_api(query, count=10, freshness='', offset=0):
    """
    调用 Cloudsway Smart Search API
    
    Args:
        query: 搜索查询词
        count: 返回结果数量
        freshness: 时间筛选（Day/Week/Month）
        offset: 分页偏移
        
    Returns:
        dict: Cloudsway API 的原始响应
    """
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {CLOUDSWAY_ACCESS_KEY}',
        'Pragma': 'no-cache'  # 不使用缓存，每次独立请求
    }
    
    # 构建查询参数
    params = {
        'q': query,
        'count': count
    }
    
    if freshness:
        params['freshness'] = freshness
    
    if offset > 0:
        params['offset'] = offset
    
    print(f"[Cloudsway] Calling API: {CLOUDSWAY_API_ENDPOINT}")
    print(f"[Cloudsway] Params: {json.dumps(params)}")
    
    # 发送 GET 请求
    response = requests.get(
        CLOUDSWAY_API_ENDPOINT,
        headers=headers,
        params=params,
        timeout=30  # 30秒超时
    )
    
    print(f"[Cloudsway] Response status: {response.status_code}")
    
    # 检查响应
    response.raise_for_status()
    
    # 解析响应
    result = response.json()
    print(f"[Cloudsway] Response size: {len(str(result))} chars")
    
    return result

# ============================================================================
# 结果格式化函数
# ============================================================================

def format_results(api_response):
    """
    将 Cloudsway API 响应格式化为可读文本
    
    Args:
        api_response: Cloudsway API 的原始响应
        
    Returns:
        str: 格式化后的 Markdown 文本
    """
    
    try:
        # 检查是否有结果
        if not api_response:
            return "# Cloudsway Smart Search 结果\n\n未找到相关结果。"
        
        # Cloudsway API 响应格式
        if 'webPages' in api_response and 'value' in api_response['webPages']:
            web_pages = api_response['webPages']['value']
            
            if not web_pages:
                return "# Cloudsway Smart Search 结果\n\n未找到相关结果。"
            
            # 获取原始查询词
            original_query = api_response.get('queryContext', {}).get('originalQuery', '')
            
            formatted = "# Cloudsway Smart Search 结果\n\n"
            if original_query:
                formatted += f"搜索词: {original_query}\n"
            formatted += f"共找到 {len(web_pages)} 个结果\n\n"
            
            for idx, result in enumerate(web_pages, 1):
                name = result.get('name', '无标题')
                url = result.get('url', '无链接')
                snippet = result.get('snippet', '无摘要')
                site_name = result.get('siteName', '')
                date_published = result.get('datePublished', '')
                score = result.get('score', '')
                
                formatted += f"## {idx}. {name}\n"
                formatted += f"**链接:** {url}\n"
                if site_name:
                    formatted += f"**来源:** {site_name}\n"
                if date_published:
                    formatted += f"**发布时间:** {date_published}\n"
                if score:
                    formatted += f"**相关性:** {score}\n"
                formatted += f"**摘要:** {snippet}\n\n"
            
            return formatted
        
        # 兼容其他可能的格式
        else:
            # 返回原始 JSON 以便调试
            return f"# Cloudsway Smart Search 结果\n\n```json\n{json.dumps(api_response, indent=2, ensure_ascii=False)}\n```"
            
    except Exception as e:
        print(f"[Cloudsway] Format error: {str(e)}")
        return f"结果格式化失败: {str(e)}\n\n原始数据: {str(api_response)[:500]}"

# ============================================================================
# 响应格式化辅助函数
# ============================================================================

def success_response(text):
    """返回成功的 MCP 格式响应"""
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
    """返回错误响应"""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'error': error_message,
            'provider': 'cloudsway'
        }, ensure_ascii=False)
    }

# ============================================================================
# 测试入口（可选）
# ============================================================================

if __name__ == "__main__":
    # 本地测试
    test_event = {
        'query': '人工智能最新进展',
        'max_results': 5
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
