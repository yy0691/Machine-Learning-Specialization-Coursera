"""
AI翻译脚本 - 翻译Jupyter Notebook文件 (简化版)
使用指定API进行智能翻译
"""
import json
import os
import sys
import re
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

# 修复Windows编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests

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
        print(f"  -> 切换到API密钥 {self.current_key_index + 1}/{len(self.api_keys)}")
    
    def translate_text(self, text: str, max_retries: int = 3) -> str:
        """使用AI API翻译文本"""
        if not text or not text.strip():
            return text
            
        # 构建翻译提示
        system_prompt = "你是一个专业的机器学习教程翻译专家。请将英文内容翻译为简洁、准确的中文，保持原有格式和技术术语的准确性。"
        
        user_prompt = f"""请将以下英文翻译为中文：

{text}

翻译要求：
1. 保持代码、公式、链接等格式不变
2. 技术术语准确翻译
3. 保持段落结构
4. 只返回翻译结果，不要解释

翻译结果："""

        for attempt in range(max_retries):
            try:
                headers = {
                    'Authorization': f'Bearer {self.get_current_key()}',
                    'Content-Type': 'application/json',
                }
                
                data = {
                    'model': self.model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'temperature': 0.2,
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
                        
                        # 清理不必要的前缀
                        prefixes = ['翻译结果：', '翻译：', '中文翻译：', '译文：']
                        for prefix in prefixes:
                            if translated_text.startswith(prefix):
                                translated_text = translated_text[len(prefix):].strip()
                        
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
                    if len(self.api_keys) > 1:
                        self.rotate_key()
                    continue
                    
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except requests.RequestException as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"    网络错误 (尝试 {attempt + 1}/{max_retries}): {str(e)[:80]}")
                    print(f"    {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"    网络错误，使用原文: {str(e)[:80]}")
                    return text
            except Exception as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"    翻译错误 (尝试 {attempt + 1}/{max_retries}): {str(e)[:80]}")
                    print(f"    {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"    翻译失败，使用原文: {str(e)[:80]}")
                    return text
        
        return text

    def protect_content(self, text: str) -> tuple:
        """保护不应翻译的内容"""
        protected_items = []
        
        # 保护模式：代码、公式、链接等
        patterns = [
            (r'```[\s\S]*?```', 'CODE_BLOCK'),
            (r'`[^`\n]+`', 'INLINE_CODE'),
            (r'\$\$[\s\S]*?\$\$', 'MATH_BLOCK'),
            (r'\$[^$\n]+\$', 'MATH_INLINE'),
            (r'!\[[^\]]*\]\([^)]+\)', 'IMAGE_MD'),
            (r'\[[^\]]+\]\([^)]+\)', 'LINK'),
            (r'<[^>]+>', 'HTML_TAG'),
        ]
        
        # 替换保护内容
        for i, (pattern, item_type) in enumerate(patterns):
            matches = list(re.finditer(pattern, text))
            for j, match in enumerate(matches):
                placeholder = f"__PROTECT_{i}_{j}__"
                protected_items.append((placeholder, match.group()))
                text = text.replace(match.group(), placeholder, 1)
        
        return text, protected_items

    def restore_content(self, text: str, protected_items: list) -> str:
        """恢复保护的内容"""
        for placeholder, original in protected_items:
            text = text.replace(placeholder, original)
        return text

    def translate_markdown_cell(self, source: List[str]) -> List[str]:
        """翻译markdown单元格"""
        if not source:
            return source
            
        full_text = ''.join(source)
        if not full_text.strip():
            return source
        
        # 保护内容
        protected_text, protected_items = self.protect_content(full_text)
        
        # 翻译
        if protected_text.strip():
            translated_text = self.translate_text(protected_text)
        else:
            translated_text = protected_text
        
        # 恢复保护内容
        translated_text = self.restore_content(translated_text, protected_items)
        
        # 转换为列表格式
        lines = translated_text.split('\n')
        result = []
        for line in lines:
            if not line.endswith('\n') and line != lines[-1]:
                result.append(line + '\n')
            elif line == lines[-1] and line:
                result.append(line + '\n')
            else:
                result.append(line)
        
        return result if result else source

    def translate_code_cell(self, source: List[str]) -> List[str]:
        """翻译代码单元格中的注释"""
        translated_source = []
        
        for line in source:
            if line.strip().startswith('#') and not line.strip().startswith('#!/'):
                # 提取注释
                comment_match = re.match(r'(\s*)(#+)(\s*)(.*)', line)
                if comment_match:
                    indent = comment_match.group(1)
                    hashes = comment_match.group(2)
                    space = comment_match.group(3)
                    comment_text = comment_match.group(4).strip()
                    
                    # 跳过特殊注释
                    skip_keywords = ['TODO', 'FIXME', 'NOTE:', 'WARNING:', 'DEBUG', '#!']
                    if comment_text and not any(kw in comment_text for kw in skip_keywords):
                        try:
                            translated_comment = self.translate_text(comment_text)
                            translated_line = f"{indent}{hashes}{space}{translated_comment}\n"
                            translated_source.append(translated_line)
                        except:
                            translated_source.append(line)
                    else:
                        translated_source.append(line)
                else:
                    translated_source.append(line)
            else:
                translated_source.append(line)
        
        return translated_source

def find_notebooks_to_translate(source_dir: Path, target_dir: Path) -> List[tuple]:
    """查找需要翻译的notebook文件"""
    notebooks_to_translate = []
    
    for notebook_path in source_dir.rglob('*.ipynb'):
        # 跳过特定目录
        path_str = str(notebook_path)
        if any(skip in path_str.lower() for skip in ['notebooks-zh', 'archive', '.git', '__pycache__']):
            continue
            
        # 计算目标路径
        relative_path = notebook_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        
        # 检查是否需要翻译
        needs_translation = False
        if not target_path.exists():
            needs_translation = True
        else:
            # 检查文件修改时间
            source_mtime = notebook_path.stat().st_mtime
            target_mtime = target_path.stat().st_mtime
            if source_mtime > target_mtime:
                needs_translation = True
        
        if needs_translation:
            notebooks_to_translate.append((notebook_path, target_path))
    
    return notebooks_to_translate

def translate_notebook(translator: AITranslator, source_path: Path, target_path: Path) -> bool:
    """翻译单个notebook"""
    try:
        print(f"翻译: {source_path.name}")
        
        # 读取源文件
        with open(source_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # 翻译单元格
        cells = notebook.get('cells', [])
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', '')
            source = cell.get('source', [])
            
            if not source:
                continue
                
            print(f"  单元格 {i+1}/{len(cells)} ({cell_type})", end='')
            
            try:
                if cell_type == 'markdown':
                    if isinstance(source, str):
                        source = [source]
                    cell['source'] = translator.translate_markdown_cell(source)
                    print(" [MD翻译完成]")
                elif cell_type == 'code':
                    if isinstance(source, str):
                        source = source.split('\n')
                        source = [line + '\n' for line in source[:-1]] + [source[-1]]
                    cell['source'] = translator.translate_code_cell(source)
                    print(" [代码注释完成]")
                else:
                    print(" [跳过]")
            except Exception as e:
                print(f" [错误: {str(e)[:30]}]")
                # 出错时保持原内容不变
        
        # 保存文件
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, ensure_ascii=False, indent=1)
        
        print(f"  完成: {target_path.relative_to(target_path.parents[2])}")
        return True
        
    except Exception as e:
        print(f"  失败: {e}")
        return False

def main():
    """主函数"""
    print("AI翻译脚本 - Jupyter Notebook翻译器")
    print("=" * 50)
    
    # ===== 配置区域 - 请修改以下配置 =====
    API_KEYS = ["Ll55vpYJkD_eWn43rp-3eupvpCpo2Asu1fe9BZpEZho,aPPJU-ENUEh6JP_CAexo6HGaePxvpMft8BlDdVCzymk,UJAcl0NUNs9mTGcusolTLEmsjBeeBmH0jPqxaztVupI,g6dIWJ5GoYYOoraGHP2Of_QKtwUE4c2bW8VATywatLE,mZ8_Dj_FVF_-Azidopxjibl1w7dfnPu17ylRxQY6IIo,6RnfA0IEEJ8vCHilyGL7ixnx_0ZN42WveTRWbDCsxfg"]
    BASE_URL = "https://api.poe.com/v1/"
    MODEL = "GPT-5-mini"
    # =====================================
    
    # 验证配置
    if not API_KEYS or API_KEYS[0] == "your-api-key-1":
        print("错误: 请配置API密钥!")
        print("编辑脚本，将 API_KEYS 中的示例密钥替换为真实密钥")
        return
    
    # 项目路径
    root_dir = Path(__file__).parent
    target_dir = root_dir / 'notebooks-zh'
    
    print(f"源目录: {root_dir}")
    print(f"目标目录: {target_dir}")
    print(f"API密钥: {len(API_KEYS)} 个")
    print(f"模型: {MODEL}")
    print("-" * 50)
    
    # 创建翻译器
    translator = AITranslator(API_KEYS, BASE_URL, MODEL)
    
    # 查找待翻译文件
    notebooks = find_notebooks_to_translate(root_dir, target_dir)
    
    if not notebooks:
        print("所有文件都已是最新翻译!")
        return
    
    print(f"找到 {len(notebooks)} 个需要翻译的文件:")
    for i, (source, target) in enumerate(notebooks[:5], 1):
        print(f"  {i}. {source.name}")
    if len(notebooks) > 5:
        print(f"  ... 还有 {len(notebooks) - 5} 个文件")
    
    # 确认开始
    response = input("\n开始翻译? (y/N): ")
    if response.lower() != 'y':
        print("已取消")
        return
    
    print("\n开始翻译...")
    print("=" * 50)
    
    # 执行翻译
    success_count = 0
    start_time = time.time()
    
    for i, (source_path, target_path) in enumerate(notebooks, 1):
        print(f"\n[{i}/{len(notebooks)}] ", end="")
        
        if translate_notebook(translator, source_path, target_path):
            success_count += 1
        
        # 显示中间统计
        if i % 3 == 0:
            elapsed = time.time() - start_time
            print(f"进度: {success_count}/{i} 成功, 用时 {elapsed:.1f}s, 请求 {translator.request_count}")
    
    # 最终统计
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("翻译完成!")
    print(f"成功: {success_count}/{len(notebooks)} 个文件")
    print(f"用时: {total_time:.1f} 秒")
    print(f"API请求: {translator.request_count} 次")
    print(f"错误数: {translator.error_count}")
    print(f"输出: {target_dir}")

if __name__ == '__main__':
    main()