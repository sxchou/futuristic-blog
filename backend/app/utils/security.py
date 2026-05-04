import re
import html
from typing import Optional, List, Any
from urllib.parse import urlparse
import bleach
from app.utils.logger import logger


class SecurityUtils:
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 's', 'span',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'hr', 'div'
    ]
    
    ALLOWED_ATTRIBUTES = {
        '*': ['class', 'id', 'style'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'pre': ['class'],
        'span': ['class', 'style']
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @staticmethod
    def sanitize_html(content: str, allow_tags: bool = True) -> str:
        if not content:
            return ""
        
        if allow_tags:
            return bleach.clean(
                content,
                tags=SecurityUtils.ALLOWED_TAGS,
                attributes=SecurityUtils.ALLOWED_ATTRIBUTES,
                protocols=SecurityUtils.ALLOWED_PROTOCOLS,
                strip=True
            )
        else:
            return html.escape(content)
    
    @staticmethod
    def strip_html(content: str) -> str:
        if not content:
            return ""
        return bleach.clean(content, tags=[], strip=True)
    
    @staticmethod
    def sanitize_url(url: str, allowed_protocols: List[str] = None) -> Optional[str]:
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            
            if allowed_protocols is None:
                allowed_protocols = SecurityUtils.ALLOWED_PROTOCOLS
            
            if parsed.scheme and parsed.scheme.lower() not in allowed_protocols:
                logger.security("Invalid URL protocol", details={"url": url})
                return None
            
            return url
        except Exception as e:
            logger.warning(f"Failed to parse URL: {str(e)}")
            return None
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        if not filename:
            return False
        
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in allowed_extensions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            return ""
        
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        filename = re.sub(r'\.{2,}', '.', filename)
        
        filename = filename.strip('. ')
        
        max_length = 255
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:max_length - len(ext) - 1] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def is_safe_redirect(url: str, allowed_hosts: List[str]) -> bool:
        if not url:
            return False
        
        if url.startswith('/') and not url.startswith('//'):
            return True
        
        try:
            parsed = urlparse(url)
            return parsed.hostname in allowed_hosts
        except Exception:
            return False
    
    @staticmethod
    def generate_csrf_token() -> str:
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, expected: str) -> bool:
        if not token or not expected:
            return False
        return secrets.compare_digest(token, expected)
    
    @staticmethod
    def check_password_strength(password: str) -> dict:
        result = {
            'valid': True,
            'score': 0,
            'messages': []
        }
        
        if len(password) < 8:
            result['valid'] = False
            result['messages'].append('密码长度至少8位')
        else:
            result['score'] += 1
        
        if len(password) >= 12:
            result['score'] += 1
        
        if re.search(r'[A-Z]', password):
            result['score'] += 1
        else:
            result['messages'].append('建议包含大写字母')
        
        if re.search(r'[a-z]', password):
            result['score'] += 1
        else:
            result['messages'].append('建议包含小写字母')
        
        if re.search(r'\d', password):
            result['score'] += 1
        else:
            result['messages'].append('建议包含数字')
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['score'] += 1
        else:
            result['messages'].append('建议包含特殊字符')
        
        common_passwords = [
            'password', '123456', '12345678', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in common_passwords:
            result['valid'] = False
            result['score'] = 0
            result['messages'].append('密码过于简单')
        
        return result
    
    @staticmethod
    def mask_email(email: str) -> str:
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 2:
            masked_local = local[0] + '***'
        else:
            masked_local = local[0] + '***' + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        if not phone:
            return phone
        
        phone = re.sub(r'[^\d]', '', phone)
        
        if len(phone) <= 7:
            return phone
        
        return phone[:3] + '****' + phone[-4:]


class InputValidator:
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    SLUG_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        if not username:
            return False, "用户名不能为空"
        
        if len(username) < 2:
            return False, "用户名至少2个字符"
        
        if len(username) > 20:
            return False, "用户名最多20个字符"
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            return False, "用户名只能包含字母、数字、下划线和中文"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        if not email:
            return False, "邮箱不能为空"
        
        if len(email) > 100:
            return False, "邮箱长度不能超过100个字符"
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            return False, "邮箱格式不正确"
        
        return True, ""
    
    @staticmethod
    def validate_slug(slug: str) -> tuple[bool, str]:
        if not slug:
            return False, "Slug不能为空"
        
        if len(slug) > 200:
            return False, "Slug长度不能超过200个字符"
        
        if not InputValidator.SLUG_PATTERN.match(slug):
            return False, "Slug只能包含字母、数字、下划线和连字符"
        
        return True, ""
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        if not query:
            return ""
        
        query = query.strip()
        
        query = re.sub(r'[<>"\'\\]', '', query)
        
        query = query[:100]
        
        return query


security_utils = SecurityUtils()
input_validator = InputValidator()


import secrets
