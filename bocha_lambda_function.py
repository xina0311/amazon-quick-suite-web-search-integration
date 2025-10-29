import json
import requests
import os

# 博查 Web Search API 配置
# IMPORTANT: Set BOCHA_API_KEY as an environment variable in Lambda configuration
BOCHA_API_KEY = os.environ.get('BOCHA_API_KEY')
if not BOCHA_API_KEY:
    raise ValueError("BOCHA_API_KEY environment variable is not set. Please configure it in Lambda environment variables.")

BOCHA_API_ENDPOINT = "https://api.bochaai.com/v1/web-search"  # 博查官方 Web Search API

def lambda_handler(event, context):
    """
    Lambda 函数处理来自 AgentCore Gateway 的请求
    支持博查 Web Search
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # AgentCore Gateway 直接传递参数，不在 body 中
        # event 本身就包含 tool 的参数
        arguments = event
        
        # 从 event 中提取工具名称（如果存在）
        tool_name = event.get('tool_name', event.get('name', ''))
        
        print(f"Tool name: {tool_name}")
        print(f"Arguments: {json.dumps(arguments)}")
        
        # Gateway 调用时，参数直接在 event 中
        # 检查是否有 query 参数（博查搜索的必需参数）
        if 'query' in arguments:
            return handle_bocha_search(arguments)
        
        # 如果有明确的 tool_name，根据名称路由
        if tool_name == 'bocha_web_search':
            return handle_bocha_search(arguments)
        
        # 默认行为：当作博查搜索请求处理
        return handle_bocha_search(arguments)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': str(type(e).__name__)
            })
        }

def handle_bocha_search(arguments):
    """
    调用博查 Web Search API
    根据博查官方文档格式：https://api.bochaai.com/v1/web-search
    """
    query = arguments.get('query', '')
    max_results = arguments.get('max_results', 10)
    
    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Query parameter is required'
            })
        }
    
    try:
        # 调用博查 API（使用官方文档格式）
        headers = {
            'Authorization': f'Bearer {BOCHA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 博查 API 请求格式
        payload = {
            'query': query,
            'count': max_results,  # 博查使用 'count' 而不是 'max_results'
            'freshness': 'noLimit',  # 时间范围：noLimit, oneDay, oneWeek, oneMonth, oneYear
            'summary': True  # 返回详细摘要
        }
        
        print(f"Calling Bocha API with query: {query}")
        print(f"Endpoint: {BOCHA_API_ENDPOINT}")
        
        response = requests.post(
            BOCHA_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        search_results = response.json()
        print(f"Response received: {len(str(search_results))} chars")
        
        # 格式化返回结果
        formatted_results = format_search_results(search_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'content': [
                    {
                        'type': 'text',
                        'text': formatted_results
                    }
                ]
            })
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Bocha API error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Bocha API error: {str(e)}',
                'details': e.response.text if hasattr(e, 'response') and e.response else 'No details'
            })
        }

def format_search_results(results):
    """
    格式化搜索结果为可读文本
    博查 API 响应格式：
    {
        "data": {
            "webPages": {
                "value": [{"name": "...", "url": "...", "summary": "..."}]
            }
        }
    }
    """
    try:
        # 检查响应格式
        if not results:
            return "未找到搜索结果。"
        
        # 博查 API 格式
        if 'data' in results and 'webPages' in results['data']:
            web_pages = results['data']['webPages'].get('value', [])
            
            if not web_pages:
                return "未找到搜索结果。"
            
            formatted = "# 博查 Web Search 结果\n\n"
            formatted += f"共找到 {len(web_pages)} 个结果\n\n"
            
            for idx, result in enumerate(web_pages, 1):
                name = result.get('name', '无标题')
                url = result.get('url', '无链接')
                summary = result.get('summary', result.get('snippet', '无摘要'))
                
                formatted += f"## {idx}. {name}\n"
                formatted += f"**链接:** {url}\n"
                formatted += f"**摘要:** {summary}\n\n"
            
            return formatted
        
        # 兼容其他可能的格式
        elif 'results' in results:
            formatted = "# 博查 Web Search 结果\n\n"
            for idx, result in enumerate(results['results'], 1):
                title = result.get('title', result.get('name', '无标题'))
                url = result.get('url', '无链接')
                snippet = result.get('snippet', result.get('summary', '无摘要'))
                
                formatted += f"## {idx}. {title}\n"
                formatted += f"**链接:** {url}\n"
                formatted += f"**摘要:** {snippet}\n\n"
            
            return formatted
        
        else:
            # 返回原始 JSON 以便调试
            return f"搜索完成，原始结果：\n```json\n{json.dumps(results, indent=2, ensure_ascii=False)}\n```"
            
    except Exception as e:
        print(f"Format error: {str(e)}")
        return f"结果格式化失败: {str(e)}\n原始数据: {str(results)[:500]}"
