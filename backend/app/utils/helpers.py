import re
import math
import hashlib
from typing import List, Optional
from pypinyin import lazy_pinyin, Style


def generate_slug(text: str, max_length: int = 100) -> str:
    if not text or not text.strip():
        return ''
    
    text = text.strip()
    
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if has_chinese:
        pinyin_parts = lazy_pinyin(text, style=Style.NORMAL)
        slug = '-'.join(pinyin_parts)
    else:
        slug = text.lower()
    
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]
    
    return slug.lower()


def generate_unique_slug(base_slug: str, existing_slugs: List[str], max_attempts: int = 100) -> str:
    if not base_slug:
        base_slug = 'untitled'
    
    if base_slug not in existing_slugs:
        return base_slug
    
    for i in range(1, max_attempts + 1):
        new_slug = f"{base_slug}-{i}"
        if new_slug not in existing_slugs:
            return new_slug
    
    hash_suffix = hashlib.md5(str(hash(base_slug)).encode()).hexdigest()[:6]
    return f"{base_slug}-{hash_suffix}"


def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
    words = len(content.split())
    minutes = math.ceil(words / words_per_minute)
    return max(1, minutes)


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
