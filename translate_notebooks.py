"""
批量翻译 Jupyter Notebook 文件为中文
使用 googletrans 库进行翻译（如果可用）
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 尝试导入翻译库
TRANSLATOR_AVAILABLE = False
translator = None
use_requests = False

# 方法1: 尝试使用googletrans
try:
    from googletrans import Translator
    translator = Translator()
    # 测试翻译是否可用
    test_result = translator.translate("test", src='en', dest='zh-cn')
    if test_result and test_result.text:
        TRANSLATOR_AVAILABLE = True
        print("✓ 使用 googletrans 翻译库")
except Exception as e:
    translator = None
    # 方法2: 尝试使用requests直接调用（备用方案）
    try:
        import requests
        import urllib.parse
        # 测试requests是否可用
        TRANSLATOR_AVAILABLE = True
        use_requests = True
        print("✓ 使用 requests 进行翻译（备用方案）")
    except ImportError:
        TRANSLATOR_AVAILABLE = False
        print("⚠ 警告: 未找到翻译库，将跳过翻译（仅复制文件）")
        print("安装命令: pip install googletrans==4.0.0rc1 或 pip install requests")

def translate_text(text: str, max_length: int = 4500) -> str:
    """
    翻译文本为中文
    """
    if not text or not text.strip():
        return text
    
    # 如果文本太长，分段翻译
    if len(text) > max_length:
        # 按段落分割
        paragraphs = text.split('\n\n')
        translated_paragraphs = []
        for para in paragraphs:
            if para.strip():
                translated_para = translate_text(para, max_length)
                translated_paragraphs.append(translated_para)
            else:
                translated_paragraphs.append(para)
        return '\n\n'.join(translated_paragraphs)
    
    if not TRANSLATOR_AVAILABLE:
        # 如果没有翻译库，返回原文
        return text
    
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用Google翻译
            if translator:
                result = translator.translate(text, src='en', dest='zh-cn')
                # 添加小延迟以避免API限制
                time.sleep(0.1)
                return result.text
            elif use_requests:
                # 使用requests备用方案
                import requests
                import urllib.parse
                url = "https://translate.googleapis.com/translate_a/single"
                params = {
                    'client': 'gtx',
                    'sl': 'en',
                    'tl': 'zh-cn',
                    'dt': 't',
                    'q': text
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result and len(result) > 0 and len(result[0]) > 0:
                        translated = ''.join([item[0] for item in result[0] if item[0]])
                        time.sleep(0.1)
                        return translated
                return text
            else:
                return text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"    翻译错误 (尝试 {attempt + 1}/{max_retries}): {str(e)[:50]}, {wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"    翻译失败，使用原文: {str(e)[:50]}")
                return text
    
    return text

def translate_markdown_cell(source: List[str]) -> List[str]:
    """
    翻译markdown单元格内容
    """
    # 如果没有翻译库，直接返回原文
    if not TRANSLATOR_AVAILABLE:
        return source
    
    # 合并所有行
    full_text = ''.join(source)
    
    # 如果文本为空，直接返回
    if not full_text.strip():
        return source
    
    # 保护代码块和链接
    code_blocks = []
    links = []
    images = []
    
    # 提取代码块
    code_block_pattern = r'```[\s\S]*?```'
    for i, match in enumerate(re.finditer(code_block_pattern, full_text)):
        placeholder = f"__CODE_BLOCK_{i}__"
        code_blocks.append((placeholder, match.group()))
        full_text = full_text.replace(match.group(), placeholder, 1)
    
    # 提取链接
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    for i, match in enumerate(re.finditer(link_pattern, full_text)):
        placeholder = f"__LINK_{i}__"
        links.append((placeholder, match.group()))
        full_text = full_text.replace(match.group(), placeholder, 1)
    
    # 提取图片标签
    img_pattern = r'<img[^>]+>'
    for i, match in enumerate(re.finditer(img_pattern, full_text)):
        placeholder = f"__IMG_{i}__"
        images.append((placeholder, match.group()))
        full_text = full_text.replace(match.group(), placeholder, 1)
    
    # 提取HTML标签
    html_pattern = r'<[^>]+>'
    html_tags = []
    for i, match in enumerate(re.finditer(html_pattern, full_text)):
        placeholder = f"__HTML_{i}__"
        html_tags.append((placeholder, match.group()))
        full_text = full_text.replace(match.group(), placeholder, 1)
    
    # 翻译文本
    translated_text = translate_text(full_text)
    
    # 恢复代码块、链接和图片
    for placeholder, original in code_blocks:
        translated_text = translated_text.replace(placeholder, original, 1)
    for placeholder, original in links:
        translated_text = translated_text.replace(placeholder, original, 1)
    for placeholder, original in images:
        translated_text = translated_text.replace(placeholder, original, 1)
    for placeholder, original in html_tags:
        translated_text = translated_text.replace(placeholder, original, 1)
    
    # 转换回列表格式（保持原有的换行结构）
    # 尝试保持原有的行结构
    lines = translated_text.split('\n')
    result = []
    for line in lines:
        result.append(line + '\n' if not line.endswith('\n') else line)
    
    # 如果最后一行没有换行符，确保格式正确
    if result and not result[-1].endswith('\n'):
        result[-1] = result[-1] + '\n'
    
    return result if result else source

def translate_code_cell(source: List[str]) -> List[str]:
    """
    翻译代码单元格中的注释
    """
    # 如果没有翻译库，直接返回原文
    if not TRANSLATOR_AVAILABLE:
        return source
    
    translated_source = []
    for line in source:
        # 只翻译注释行（以#开头的行，但排除shebang等）
        if line.strip().startswith('#'):
            # 提取注释内容
            comment_match = re.match(r'(\s*)(#+)(\s*)(.*)', line)
            if comment_match:
                indent = comment_match.group(1)
                hashes = comment_match.group(2)
                space = comment_match.group(3)
                comment_text = comment_match.group(4)
                
                if comment_text.strip():
                    # 翻译注释内容
                    translated_comment = translate_text(comment_text)
                    translated_line = f"{indent}{hashes}{space}{translated_comment}\n"
                    translated_source.append(translated_line)
                else:
                    translated_source.append(line)
            else:
                translated_source.append(line)
        else:
            # 保持代码不变
            translated_source.append(line)
    
    return translated_source

def translate_notebook(notebook_path: Path, output_path: Path) -> None:
    """
    翻译单个notebook文件
    """
    print(f"正在翻译: {notebook_path.relative_to(notebook_path.parents[3])}")
    
    try:
        # 读取原始notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # 翻译每个单元格
        for i, cell in enumerate(notebook.get('cells', [])):
            cell_type = cell.get('cell_type')
            
            if cell_type == 'markdown':
                # 翻译markdown单元格
                source = cell.get('source', [])
                if source:
                    if isinstance(source, list):
                        cell['source'] = translate_markdown_cell(source)
                    elif isinstance(source, str):
                        cell['source'] = translate_markdown_cell([source])
                        
            elif cell_type == 'code':
                # 翻译代码单元格中的注释
                source = cell.get('source', [])
                if source:
                    if isinstance(source, list):
                        cell['source'] = translate_code_cell(source)
                    elif isinstance(source, str):
                        lines = source.split('\n')
                        translated_lines = translate_code_cell([l + '\n' for l in lines])
                        cell['source'] = ''.join(translated_lines)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存翻译后的notebook
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, ensure_ascii=False, indent=1)
        
        print(f"  [完成]")
        
    except Exception as e:
        print(f"  [错误]: {e}")

def find_all_notebooks(root_dir: Path) -> List[Path]:
    """
    查找所有.ipynb文件
    """
    notebooks = []
    for notebook_path in root_dir.rglob('*.ipynb'):
        # 排除输出目录和archive目录
        path_str = str(notebook_path)
        if 'notebooks-zh' not in path_str and 'archive' not in path_str.lower():
            notebooks.append(notebook_path)
    return sorted(notebooks)

def main():
    """
    主函数：批量翻译所有notebook文件
    """
    # 项目根目录
    root_dir = Path(__file__).parent
    output_dir = root_dir / 'notebooks-zh'
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    # 查找所有notebook文件
    notebooks = find_all_notebooks(root_dir)
    
    print(f"找到 {len(notebooks)} 个notebook文件")
    print(f"输出目录: {output_dir}\n")
    
    if not TRANSLATOR_AVAILABLE:
        print("注意: 未安装翻译库，将使用简单替换。")
        print("建议安装: pip install googletrans==4.0.0rc1\n")
    
    # 翻译每个文件
    success_count = 0
    for i, notebook_path in enumerate(notebooks, 1):
        print(f"[{i}/{len(notebooks)}] ", end='')
        # 计算相对路径
        relative_path = notebook_path.relative_to(root_dir)
        output_path = output_dir / relative_path
        
        try:
            translate_notebook(notebook_path, output_path)
            success_count += 1
        except Exception as e:
            print(f"  [失败]: {e}")
    
    print(f"\n{'='*60}")
    print(f"翻译完成！")
    print(f"成功: {success_count}/{len(notebooks)} 个文件")
    print(f"输出目录: {output_dir}")

if __name__ == '__main__':
    main()
