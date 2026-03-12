import re
import math
from typing import List


def generate_slug(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug


def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
    words = len(content.split())
    minutes = math.ceil(words / words_per_minute)
    return max(1, minutes)


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
