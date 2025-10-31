"""
秘塔科技 AI Search Lambda 函数
支持网页、文档、论文、图片、视频、播客等内容搜索
"""

import json
import requests
import os

# ============================================================================
# 配置部分
# ============================================================================

PROVIDER_NAME = "metaso"
# IMPORTANT: METASO_API_KEY must be set as an environment variable in Lambda configuration
METASO_API_KEY = os.environ.get('METASO_API_KEY')
if not METASO_API_KEY:
    raise ValueError("METASO_API_KEY environment variable is not set. Please configure it in Lambda environment variables.")

METASO_API_ENDPOINT = "https://metaso.cn/api/v1/search"

# 支持的搜索范围
VALID_SCOPES = ['webpage', 'document', 'paper', 'image', 'video', 'podcast']

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
    print(f"[Metaso] Received event: {json.dumps(event)}")
    
    try:
        # 从 event 提取参数
        query = event.get('query', event.get('q', ''))
        max_results = event.get('max_results', event.get('size', 10))
        scope = event.get('scope', 'webpage')
        include_summary = event.get('include_summary', event.get('includeSummary', False))
        include_raw_content = event.get('include_raw_content', event.get('includeRawContent', False))
        concise_snippet = event.get('concise_snippet', event.get('conciseSnippet', False))
        
        print(f"[Metaso] Query: {query}")
        print(f"[Metaso] Scope: {scope}, Max Results: {max_results}")
        
        # 参数验证
        if not query:
            return error_response('Query parameter is required')
        
        if scope not in VALID_SCOPES:
            return error_response(f'Invalid scope. Must be one of: {", ".join(VALID_SCOPES)}')
        
        if max_results < 1 or max_results > 50:
            max_results = 10  # 使用默认值
        
        # 调用秘塔 API
        search_results = call_metaso_api(
            query=query,
            scope=scope,
            size=max_results,
            include_summary=include_summary,
            include_raw_content=include_raw_content,
            concise_snippet=concise_snippet
        )
        
        # 格式化结果
        formatted_results = format_results(search_results, scope)
        
        # 返回成功响应
        return success_response(formatted_results)
        
    except requests.exceptions.Timeout:
        print(f"[Metaso] API timeout")
        return error_response('Search request timeout')
        
    except requests.exceptions.RequestException as e:
        print(f"[Metaso] API error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return error_response(f'Metaso API request failed: {str(e)}')
        
    except Exception as e:
        print(f"[Metaso] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f'Internal error: {str(e)}')

# ============================================================================
# 秘塔 API 调用函数
# ============================================================================

def call_metaso_api(query, scope='webpage', size=10, include_summary=False, 
                    include_raw_content=False, concise_snippet=False):
    """
    调用秘塔 AI Search API
    
    Args:
        query: 搜索查询关键词
        scope: 搜索范围（webpage, document, paper, image, video, podcast）
        size: 返回结果数量
        include_summary: 通过网页摘要信息提升搜索结果的召回率
        include_raw_content: 抓取所有来源网页原文
        concise_snippet: 简洁摘要
        
    Returns:
        dict: 秘塔 API 的原始响应
    """
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {METASO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 构建请求体（按照秘塔 API 文档）
    payload = {
        'q': query,
        'scope': scope,
        'size': str(size),  # 秘塔 API 可能需要字符串格式
        'includeSummary': include_summary,
        'includeRawContent': include_raw_content,
        'conciseSnippet': concise_snippet
    }
    
    print(f"[Metaso] Calling API: {METASO_API_ENDPOINT}")
    print(f"[Metaso] Payload: {json.dumps(payload)}")
    
    # 发送请求
    response = requests.post(
        METASO_API_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=30  # 30秒超时
    )
    
    print(f"[Metaso] Response status: {response.status_code}")
    
    # 检查响应
    response.raise_for_status()
    
    # 解析响应
    result = response.json()
    print(f"[Metaso] Response size: {len(str(result))} chars")
    
    return result

# ============================================================================
# 结果格式化函数
# ============================================================================

def format_results(api_response, scope='webpage'):
    """
    将秘塔 API 响应格式化为可读文本
    
    Args:
        api_response: 秘塔 API 的原始响应
        scope: 搜索范围
        
    Returns:
        str: 格式化后的 Markdown 文本
    """
    
    try:
        # 获取中文搜索类型名称
        scope_names = {
            'webpage': '网页',
            'document': '文档',
            'paper': '论文',
            'image': '图片',
            'video': '视频',
            'podcast': '播客'
        }
        scope_name = scope_names.get(scope, scope)
        
        # 检查是否有结果
        if not api_response:
            return f"# 秘塔 AI Search - {scope_name}搜索结果\n\n未找到相关结果。"
        
        # 尝试多种可能的响应格式
        
        # 格式 1: 有 data 字段
        if 'data' in api_response:
            results = api_response['data']
            if isinstance(results, dict):
                # 可能有 items 或 results 字段
                results = results.get('items', results.get('results', []))
        # 格式 2: 直接是 results 数组
        elif 'results' in api_response:
            results = api_response['results']
        # 格式 3: 直接是 items 数组
        elif 'items' in api_response:
            results = api_response['items']
        # 格式 4: 响应本身就是数组
        elif isinstance(api_response, list):
            results = api_response
        else:
            # 无法识别的格式，返回原始 JSON
            return format_raw_response(api_response, scope_name)
        
        if not results:
            return f"# 秘塔 AI Search - {scope_name}搜索结果\n\n未找到相关结果。"
        
        # 开始格式化
        formatted = f"# 秘塔 AI Search - {scope_name}搜索结果\n\n"
        formatted += f"共找到 {len(results)} 个结果\n\n"
        
        # 根据不同类型格式化结果
        if scope == 'image':
            formatted += format_image_results(results)
        elif scope == 'video':
            formatted += format_video_results(results)
        elif scope == 'paper':
            formatted += format_paper_results(results)
        else:
            formatted += format_web_results(results)
        
        return formatted
        
    except Exception as e:
        print(f"[Metaso] Format error: {str(e)}")
        return format_raw_response(api_response, '未知')

def format_web_results(results):
    """格式化网页/文档结果"""
    formatted = ""
    for idx, result in enumerate(results, 1):
        # 尝试多种可能的字段名
        title = result.get('title', result.get('name', result.get('headline', '无标题')))
        url = result.get('url', result.get('link', result.get('href', '无链接')))
        snippet = result.get('snippet', result.get('description', result.get('summary', result.get('content', '无摘要'))))
        
        # 可选字段
        author = result.get('author', '')
        date = result.get('date', result.get('publishDate', ''))
        
        formatted += f"## {idx}. {title}\n"
        formatted += f"**链接:** {url}\n"
        if author:
            formatted += f"**作者:** {author}\n"
        if date:
            formatted += f"**日期:** {date}\n"
        formatted += f"**摘要:** {snippet}\n\n"
    
    return formatted

def format_paper_results(results):
    """格式化论文结果"""
    formatted = ""
    for idx, result in enumerate(results, 1):
        title = result.get('title', '无标题')
        url = result.get('url', result.get('link', '无链接'))
        authors = result.get('authors', result.get('author', []))
        abstract = result.get('abstract', result.get('snippet', '无摘要'))
        year = result.get('year', result.get('publishYear', ''))
        venue = result.get('venue', result.get('journal', ''))
        
        formatted += f"## {idx}. {title}\n"
        if authors:
            if isinstance(authors, list):
                formatted += f"**作者:** {', '.join(authors)}\n"
            else:
                formatted += f"**作者:** {authors}\n"
        if year:
            formatted += f"**年份:** {year}\n"
        if venue:
            formatted += f"**发表于:** {venue}\n"
        formatted += f"**链接:** {url}\n"
        formatted += f"**摘要:** {abstract}\n\n"
    
    return formatted

def format_image_results(results):
    """格式化图片结果"""
    formatted = ""
    for idx, result in enumerate(results, 1):
        title = result.get('title', result.get('name', '无标题'))
        image_url = result.get('imageUrl', result.get('url', result.get('src', '无图片')))
        source_url = result.get('sourceUrl', result.get('link', ''))
        description = result.get('description', result.get('snippet', ''))
        
        formatted += f"## {idx}. {title}\n"
        formatted += f"**图片链接:** {image_url}\n"
        if source_url:
            formatted += f"**来源:** {source_url}\n"
        if description:
            formatted += f"**描述:** {description}\n"
        formatted += "\n"
    
    return formatted

def format_video_results(results):
    """格式化视频结果"""
    formatted = ""
    for idx, result in enumerate(results, 1):
        title = result.get('title', '无标题')
        url = result.get('url', result.get('link', '无链接'))
        description = result.get('description', result.get('snippet', ''))
        duration = result.get('duration', '')
        channel = result.get('channel', result.get('author', ''))
        views = result.get('views', result.get('viewCount', ''))
        
        formatted += f"## {idx}. {title}\n"
        formatted += f"**链接:** {url}\n"
        if channel:
            formatted += f"**频道:** {channel}\n"
        if duration:
            formatted += f"**时长:** {duration}\n"
        if views:
            formatted += f"**播放量:** {views}\n"
        if description:
            formatted += f"**简介:** {description}\n"
        formatted += "\n"
    
    return formatted

def format_raw_response(api_response, scope_name):
    """格式化原始响应（用于调试）"""
    return f"# 秘塔 AI Search - {scope_name}搜索结果\n\n```json\n{json.dumps(api_response, indent=2, ensure_ascii=False)}\n```"

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
            'provider': 'metaso'
        }, ensure_ascii=False)
    }

# ============================================================================
# 测试入口（可选）
# ============================================================================

if __name__ == "__main__":
    # 本地测试
    test_event = {
        'query': '人工智能最新进展',
        'scope': 'webpage',
        'max_results': 5
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
