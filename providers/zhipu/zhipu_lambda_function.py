"""
智谱 (Zhipu) Web Search Lambda 函数
专为大模型优化的搜索引擎，支持多种搜索引擎和时间范围过滤
"""

import json
import requests
import os

# ============================================================================
# 配置部分
# ============================================================================

PROVIDER_NAME = "zhipu"

# API Key 从环境变量读取
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY')
if not ZHIPU_API_KEY:
    raise ValueError("ZHIPU_API_KEY environment variable is not set. Please configure it in Lambda environment variables.")

# 智谱 Web Search API endpoint
ZHIPU_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/web_search"

# 有效的搜索引擎类型
VALID_SEARCH_ENGINES = ['search_std', 'search_pro', 'search_pro_sogou', 'search_pro_quark']

# 有效的时间范围过滤
VALID_RECENCY_FILTERS = ['oneDay', 'oneWeek', 'oneMonth', 'oneYear', 'noLimit']

# 有效的摘要长度
VALID_CONTENT_SIZES = ['low', 'medium', 'high']

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
    print(f"[{PROVIDER_NAME}] Received event: {json.dumps(event)}")
    
    try:
        # 从 event 提取参数
        query = event.get('query', event.get('search_query', ''))
        max_results = event.get('max_results', event.get('count', 10))
        search_engine = event.get('search_engine', 'search_std')
        recency_filter = event.get('recency_filter', event.get('search_recency_filter', 'noLimit'))
        domain_filter = event.get('domain_filter', event.get('search_domain_filter', None))
        content_size = event.get('content_size', 'medium')
        
        print(f"[{PROVIDER_NAME}] Query: {query}")
        print(f"[{PROVIDER_NAME}] Search Engine: {search_engine}, Max Results: {max_results}")
        
        # 参数验证
        if not query or (isinstance(query, str) and not query.strip()):
            return error_response(400, 'Query parameter is required')
        
        # 验证并修正 max_results
        try:
            max_results = int(max_results)
            if max_results < 1 or max_results > 50:
                max_results = 10
        except (ValueError, TypeError):
            max_results = 10
        
        # 验证并修正 search_engine
        if search_engine not in VALID_SEARCH_ENGINES:
            print(f"[{PROVIDER_NAME}] Invalid search_engine '{search_engine}', using default 'search_std'")
            search_engine = 'search_std'
        
        # 验证并修正 recency_filter
        if recency_filter not in VALID_RECENCY_FILTERS:
            print(f"[{PROVIDER_NAME}] Invalid recency_filter '{recency_filter}', using default 'noLimit'")
            recency_filter = 'noLimit'
        
        # 验证并修正 content_size
        if content_size not in VALID_CONTENT_SIZES:
            print(f"[{PROVIDER_NAME}] Invalid content_size '{content_size}', using default 'medium'")
            content_size = 'medium'

        # 调用智谱 API
        search_results = call_zhipu_api(
            query=query,
            count=max_results,
            search_engine=search_engine,
            recency_filter=recency_filter,
            domain_filter=domain_filter,
            content_size=content_size
        )
        
        # 格式化结果
        formatted_results = format_results(search_results)
        
        # 返回成功响应
        return success_response(formatted_results)
        
    except requests.exceptions.Timeout:
        print(f"[{PROVIDER_NAME}] API timeout")
        return error_response(500, 'Search request timeout')
        
    except requests.exceptions.RequestException as e:
        print(f"[{PROVIDER_NAME}] API error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return error_response(500, f'Zhipu API request failed: {str(e)}')
        
    except Exception as e:
        print(f"[{PROVIDER_NAME}] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f'Internal error: {str(e)}')

# ============================================================================
# 智谱 API 调用函数
# ============================================================================

def call_zhipu_api(query, count=10, search_engine='search_std', recency_filter='noLimit',
                   domain_filter=None, content_size='medium'):
    """
    调用智谱 Web Search API
    
    Args:
        query: 搜索查询关键词
        count: 返回结果数量 (1-50)
        search_engine: 搜索引擎类型
        recency_filter: 时间范围过滤
        domain_filter: 域名白名单过滤
        content_size: 摘要长度控制
        
    Returns:
        dict: 智谱 API 的原始响应
    """
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {ZHIPU_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 构建请求体（参数名称映射到智谱 API 格式）
    payload = {
        'search_query': query,
        'search_engine': search_engine,
        'count': count,
        'search_recency_filter': recency_filter,
        'content_size': content_size
    }
    
    # 可选参数：域名过滤
    if domain_filter:
        payload['search_domain_filter'] = domain_filter
    
    print(f"[{PROVIDER_NAME}] Calling API: {ZHIPU_API_ENDPOINT}")
    print(f"[{PROVIDER_NAME}] Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    # 发送请求
    response = requests.post(
        ZHIPU_API_ENDPOINT,
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
# 结果格式化函数
# ============================================================================

def format_results(api_response):
    """
    将智谱 API 响应格式化为可读的 Markdown 文本
    
    Args:
        api_response: 智谱 API 的原始响应
        
    Returns:
        str: 格式化后的 Markdown 文本
    """
    
    try:
        # 检查是否有结果
        if not api_response:
            return "# 智谱 Web Search 结果\n\n未找到相关结果。"
        
        # 获取搜索结果
        search_results = api_response.get('search_result', [])
        
        if not search_results:
            return "# 智谱 Web Search 结果\n\n未找到相关结果。"
        
        # 开始格式化
        formatted = "# 智谱 Web Search 结果\n\n"
        
        # 显示搜索意图（如果有）
        search_intent = api_response.get('search_intent', [])
        if search_intent:
            for intent in search_intent:
                original_query = intent.get('query', '')
                intent_type = intent.get('intent', '')
                keywords = intent.get('keywords', '')
                
                if keywords and keywords != original_query:
                    formatted += f"**搜索意图:** {intent_type}\n"
                    formatted += f"**优化关键词:** {keywords}\n\n"
                    break
        
        formatted += f"共找到 {len(search_results)} 个结果\n\n"
        
        # 格式化每个结果
        for idx, result in enumerate(search_results, 1):
            title = result.get('title', '无标题')
            link = result.get('link', '无链接')
            content = result.get('content', '无摘要')
            media = result.get('media', '')
            icon = result.get('icon', '')
            publish_date = result.get('publish_date', '')
            
            formatted += f"## {idx}. {title}\n"
            formatted += f"**链接:** {link}\n"
            
            if media:
                formatted += f"**来源:** {media}\n"
            
            if publish_date:
                formatted += f"**发布日期:** {publish_date}\n"
            
            formatted += f"**摘要:** {content}\n\n"
        
        return formatted
        
    except Exception as e:
        print(f"[{PROVIDER_NAME}] Format error: {str(e)}")
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

def error_response(status_code, error_message):
    """返回错误响应"""
    return {
        'statusCode': status_code,
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
        'query': '人工智能最新进展',
        'max_results': 5,
        'search_engine': 'search_std'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
