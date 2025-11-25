"""
AI翻译脚本 - 使用指定API翻译Jupyter Notebook文件
支持多个API密钥轮换，智能重试机制
"""
import json
import os
import sys
import re
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class AITranslator:
    def __init__(self, api_keys: List[str], base_url: str, model: str):
        self.api_keys = api_keys
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.current_key_index = 0
        self.request_count = 0
        self.error_count = 0
        
    def get_current_key(self) -> str:
        """获取当前使用的API密钥"""
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def rotate_key(self):
        """轮换到下一个API密钥"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"  → 切换到API密钥 {self.current_key_index + 1}/{len(self.api_keys)}")
    
    def translate_text(self, text: str, max_retries: int = 3) -> str:
        """
        使用AI API翻译文本
        """
        if not text or not text.strip():
            return text
            
        # 构建翻译提示
        prompt = f"""请将以下英文文本翻译为中文，保持原有的格式和结构：

原文：
{text}

翻译要求：
1. 保持所有代码块、链接、图片标签不变
2. 保持数学公式和LaTeX符号不变
3. 技术术语保持准确性
4. 保持原有的段落结构和换行
5. 只返回翻译后的文本，不要添加任何说明

翻译："""

        for attempt in range(max_retries):
            try:
                headers = {
                    'Authorization': f'Bearer {self.get_current_key()}',
                    'Content-Type': 'application/json',
                }
                
                data = {
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 2000
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                self.request_count += 1
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        translated_text = result['choices'][0]['message']['content'].strip()
                        
                        # 清理翻译结果（移除可能的前缀说明）
                        if translated_text.startswith(('翻译：', '中文翻译：', '译文：')):
                            translated_text = re.sub(r'^[^：]*：\s*', '', translated_text)
                        
                        # 添加小延迟避免API限制
                        time.sleep(random.uniform(0.5, 1.0))
                        return translated_text
                    else:
                        raise Exception("API响应格式错误")
                        
                elif response.status_code == 401:
                    print(f"    API密钥无效，尝试切换...")
                    self.rotate_key()
                    continue
                    
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"    API限制，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    self.rotate_key()
                    continue
                    
                else:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"    翻译错误 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
                    print(f"    {wait_time}秒后重试...")
                    time.sleep(wait_time)
                    if attempt >= 1:  # 第二次重试时切换密钥
                        self.rotate_key()
                else:
                    print(f"    翻译失败，使用原文: {str(e)[:100]}")
                    return text
        
        return text

    def translate_markdown_cell(self, source: List[str]) -> List[str]:
        """翻译markdown单元格内容"""
        if not source:
            return source
            
        # 合并所有行
        full_text = ''.join(source)
        
        if not full_text.strip():
            return source
            
        # 保护代码块、链接、图片等
        protected_items = []
        
        # 保护模式：代码块、链接、图片、HTML标签、数学公式
        patterns = [
            (r'```[\s\S]*?```', 'CODE_BLOCK'),
            (r'`[^`]+`', 'INLINE_CODE'),
            (r'\$\$[\s\S]*?\$\$', 'MATH_BLOCK'),
            (r'\$[^$]+\$', 'MATH_INLINE'),
            (r'\[([^\]]+)\]\(([^\)]+)\)', 'LINK'),
            (r'<img[^>]+>', 'IMAGE'),
            (r'<[^>]+>', 'HTML_TAG'),
            (r'!\[([^\]]*)\]\(([^\)]+)\)', 'IMAGE_MD'),
        ]
        
        # 替换保护项
        for i, (pattern, item_type) in enumerate(patterns):
            matches = list(re.finditer(pattern, full_text))
            for j, match in enumerate(matches):
                placeholder = f"__PROTECTED_{i}_{j}__"
                protected_items.append((placeholder, match.group()))
                full_text = full_text.replace(match.group(), placeholder, 1)
        
        # 翻译文本
        if full_text.strip():
            translated_text = self.translate_text(full_text)
        else:
            translated_text = full_text
        
        # 恢复保护项
        for placeholder, original in protected_items:
            translated_text = translated_text.replace(placeholder, original)
        
        # 转换回列表格式
        lines = translated_text.split('\n')
        result = []
        for line in lines:
            result.append(line + '\n' if not line.endswith('\n') else line)
        
        if result and not result[-1].endswith('\n'):
            result[-1] = result[-1] + '\n'
            
        return result if result else source

    def translate_code_cell(self, source: List[str]) -> List[str]:
        """翻译代码单元格中的注释"""
        translated_source = []
        
        for line in source:
            # 翻译Python注释
            if line.strip().startswith('#'):
                comment_match = re.match(r'(\s*)(#+)(\s*)(.*)', line)
                if comment_match:
                    indent = comment_match.group(1)
                    hashes = comment_match.group(2)
                    space = comment_match.group(3)
                    comment_text = comment_match.group(4)
                    
                    if comment_text.strip() and not comment_text.strip().startswith(('!', 'TODO', 'FIXME')):
                        translated_comment = self.translate_text(comment_text)
                        translated_line = f"{indent}{hashes}{space}{translated_comment}\n"
                        translated_source.append(translated_line)
                    else:
                        translated_source.append(line)
                else:
                    translated_source.append(line)
            else:
                # 翻译字符串中的用户提示（谨慎处理）
                if 'print(' in line and any(word in line.lower() for word in ['training', 'test', 'error', 'accuracy', 'loss']):
                    # 保护字符串内容的简单翻译
                    translated_source.append(line)
                else:
                    translated_source.append(line)
        
        return translated_source

def find_untranslated_notebooks(source_dir: Path, target_dir: Path) -> List[tuple]:
    """查找未翻译的notebook文件"""
    untranslated = []
    
    for notebook_path in source_dir.rglob('*.ipynb'):
        # 跳过archive目录
        if 'archive' in str(notebook_path).lower():
            continue
            
        # 计算相对路径
        relative_path = notebook_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        
        # 检查是否需要翻译
        if not target_path.exists():
            untranslated.append((notebook_path, target_path))
        else:
            # 检查源文件是否比目标文件新
            if notebook_path.stat().st_mtime > target_path.stat().st_mtime:
                untranslated.append((notebook_path, target_path))
    
    return untranslated

def translate_notebook(translator: AITranslator, source_path: Path, target_path: Path) -> bool:
    """翻译单个notebook文件"""
    try:
        print(f"正在翻译: {source_path.relative_to(source_path.parents[3])}")
        
        # 读取原始notebook
        with open(source_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # 翻译每个单元格
        total_cells = len(notebook.get('cells', []))
        for i, cell in enumerate(notebook.get('cells', [])):
            cell_type = cell.get('cell_type')
            print(f"  处理单元格 {i+1}/{total_cells} ({cell_type})", end='')
            
            if cell_type == 'markdown':
                source = cell.get('source', [])
                if source:
                    if isinstance(source, list):
                        cell['source'] = translator.translate_markdown_cell(source)
                    elif isinstance(source, str):
                        cell['source'] = translator.translate_markdown_cell([source])
                print(" ✓")
                        
            elif cell_type == 'code':
                source = cell.get('source', [])
                if source:
                    if isinstance(source, list):
                        cell['source'] = translator.translate_code_cell(source)
                    elif isinstance(source, str):
                        lines = source.split('\n')
                        translated_lines = translator.translate_code_cell([l + '\n' for l in lines])
                        cell['source'] = ''.join(translated_lines)
                print(" ✓")
            else:
                print(" (跳过)")
        
        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存翻译后的notebook
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, ensure_ascii=False, indent=1)
        
        print(f"  [完成] 请求数: {translator.request_count}, 错误数: {translator.error_count}")
        return True
        
    except Exception as e:
        print(f"  [失败]: {e}")
        return False

def main():
    """主函数"""
    # API配置 - 请在这里修改您的配置
    API_KEYS = [
        "key1",  # 替换为您的第一个API密钥
        "key2",  # 替换为您的第二个API密钥
        "key3",  # 替换为您的第三个API密钥
        # 可以添加更多密钥...
    ]
    BASE_URL = "https://api.poe.com/v1/"
    MODEL = "GPT-5-mini"
    
    # 验证配置
    if not API_KEYS or API_KEYS[0] == "key1":
        print("❌ 请在脚本中配置您的API密钥！")
        print("修改 API_KEYS 列表，将 'key1', 'key2' 等替换为实际的API密钥")
        return
    
    # 项目目录
    root_dir = Path(__file__).parent
    source_dir = root_dir
    target_dir = root_dir / 'notebooks-zh'
    
    print("🤖 AI翻译脚本启动")
    print(f"📂 源目录: {source_dir}")
    print(f"📁 目标目录: {target_dir}")
    print(f"🔑 API密钥数量: {len(API_KEYS)}")
    print(f"🌐 API地址: {BASE_URL}")
    print(f"🧠 模型: {MODEL}")
    print("-" * 60)
    
    # 创建翻译器
    translator = AITranslator(API_KEYS, BASE_URL, MODEL)
    
    # 查找未翻译的文件
    untranslated_files = find_untranslated_notebooks(source_dir, target_dir)
    
    if not untranslated_files:
        print("✅ 所有文件都已翻译完成！")
        return
    
    print(f"📊 找到 {len(untranslated_files)} 个需要翻译的文件")
    
    # 确认是否继续
    response = input("\n是否开始翻译？(y/n): ")
    if response.lower() != 'y':
        print("翻译已取消")
        return
    
    print("\n🚀 开始翻译...\n")
    
    # 翻译文件
    success_count = 0
    start_time = time.time()
    
    for i, (source_path, target_path) in enumerate(untranslated_files, 1):
        print(f"\n[{i}/{len(untranslated_files)}]", end=' ')
        
        if translate_notebook(translator, source_path, target_path):
            success_count += 1
        
        # 每5个文件显示一次进度统计
        if i % 5 == 0:
            elapsed = time.time() - start_time
            print(f"\n📈 进度统计: {success_count}/{i} 成功, 用时: {elapsed:.1f}秒")
    
    # 最终统计
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"🎉 翻译完成！")
    print(f"📊 成功: {success_count}/{len(untranslated_files)} 个文件")
    print(f"⏱️  总用时: {total_time:.1f} 秒")
    print(f"📡 总请求数: {translator.request_count}")
    print(f"❌ 错误数: {translator.error_count}")
    print(f"📁 输出目录: {target_dir}")

if __name__ == '__main__':
    main()