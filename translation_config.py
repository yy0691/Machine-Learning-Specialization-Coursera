# AI翻译脚本配置文件

# 请在这里配置您的API密钥，用逗号分隔多个密钥
api_keys = [
    "your-api-key-1",
    "your-api-key-2", 
    "your-api-key-3",
    # 可以添加更多密钥以提高稳定性
]

# API配置
base_url = "https://api.poe.com/v1/"
model = "GPT-5-mini"

# 翻译设置
max_retries = 3              # 最大重试次数
request_delay = (0.5, 1.0)   # 请求间隔（秒），随机范围
timeout = 30                 # 请求超时时间（秒）
temperature = 0.3            # 翻译创造性（0-1，越低越保守）
max_tokens = 2000            # 最大生成令牌数

# 并发设置
max_workers = 2              # 最大并发线程数（建议不超过2避免API限制）

# 文件过滤设置
skip_patterns = [
    "archive",               # 跳过archive目录
    ".git",                  # 跳过git目录
    "__pycache__",          # 跳过缓存目录
]

# 翻译质量设置
preserve_patterns = [
    r'```[\s\S]*?```',       # 代码块
    r'`[^`]+`',              # 行内代码
    r'\$\$[\s\S]*?\$\$',     # 数学公式块
    r'\$[^$]+\$',            # 行内数学公式
    r'<[^>]+>',              # HTML标签
    r'!\[.*?\]\(.*?\)',      # 图片链接
    r'\[.*?\]\(.*?\)',       # 普通链接
]