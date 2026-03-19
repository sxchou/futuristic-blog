from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


def serialize_datetime(dt: datetime) -> Optional[str]:
    from app.utils.timezone import to_local
    if dt is None:
        return None
    local_dt = to_local(dt)
    return local_dt.isoformat()


def validate_email(email: str) -> str:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError('Invalid email format')
    return email


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    
    def validate_email_field(self):
        validate_email(self.email)
        return self


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None


class UserAdminUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_admin: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_admin: bool = False
    is_verified: bool = False
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    avatar_type: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_gradient: Optional[List[str]] = None
    bio: Optional[str] = None
    is_admin: bool = False
    is_verified: bool = False
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = "#00d4ff"


class CategoryCreate(CategoryBase):
    order: Optional[int] = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int
    order: int
    created_at: Optional[str] = None
    article_count: Optional[int] = 0
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    slug: str = Field(..., min_length=1, max_length=30)
    color: Optional[str] = "#7c3aed"


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    slug: Optional[str] = Field(None, min_length=1, max_length=30)
    color: Optional[str] = None


class TagResponse(TagBase):
    id: int
    created_at: Optional[str] = None
    article_count: Optional[int] = 0
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False
    is_pinned: bool = False
    category_id: Optional[int] = None


class ArticleCreate(ArticleBase):
    tag_ids: List[int] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_pinned: Optional[bool] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class ArticleResponse(ArticleBase):
    id: int
    view_count: int
    like_count: int
    reading_time: int
    author_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    author: Optional[UserResponse] = None
    is_liked: bool = False
    files: List["ArticleFileResponse"] = []
    
    @field_validator('created_at', 'updated_at', 'published_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class ArticleListItem(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image: Optional[str] = None
    is_published: bool
    is_featured: bool
    is_pinned: bool = False
    view_count: int
    like_count: int
    comment_count: int = 0
    reading_time: int
    created_at: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    is_liked: bool = False
    
    @field_validator('created_at', 'published_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    article_id: int
    like_count: int
    is_liked: bool


class ResourceBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    url: str = Field(..., max_length=500)
    icon: Optional[str] = None
    category: str
    is_active: bool = True
    order: Optional[int] = 0


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class ResourceResponse(ResourceBase):
    id: int
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    article_id: int
    parent_id: Optional[int] = None


class CommentResponse(CommentBase):
    id: int
    article_id: int
    parent_id: Optional[int] = None
    user_id: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_url: Optional[str] = None
    author_avatar_type: Optional[str] = None
    author_avatar_url: Optional[str] = None
    author_avatar_gradient: Optional[List[str]] = None
    status: str = 'approved'
    is_deleted: bool = False
    deleted_by: Optional[str] = None
    reply_to_user_id: Optional[int] = None
    reply_to_user_name: Optional[str] = None
    reply_to_user_avatar_type: Optional[str] = None
    reply_to_user_avatar_url: Optional[str] = None
    reply_to_user_avatar_gradient: Optional[List[str]] = None
    created_at: Optional[str] = None
    replies: List["CommentResponse"] = []
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class CommentAuditRequest(BaseModel):
    status: str = Field(..., pattern='^(pending|approved|rejected)$')
    reason: Optional[str] = None


class BatchAuditRequest(BaseModel):
    comment_ids: List[int]
    status: str = Field(..., pattern='^(pending|approved|rejected)$')
    reason: Optional[str] = None


class CommentAuditLogResponse(BaseModel):
    id: int
    comment_id: int
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    old_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class AdminCommentResponse(CommentBase):
    id: int
    article_id: int
    article_title: Optional[str] = None
    article_slug: Optional[str] = None
    parent_id: Optional[int] = None
    user_id: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_url: Optional[str] = None
    author_avatar_type: Optional[str] = None
    author_avatar_url: Optional[str] = None
    author_avatar_gradient: Optional[List[str]] = None
    status: str = 'approved'
    is_deleted: bool = False
    deleted_by: Optional[str] = None
    reply_to_user_id: Optional[int] = None
    reply_to_user_name: Optional[str] = None
    reply_to_user_avatar_type: Optional[str] = None
    reply_to_user_avatar_url: Optional[str] = None
    reply_to_user_avatar_gradient: Optional[List[str]] = None
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchQuery(BaseModel):
    query: str
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    page: int = 1
    page_size: int = 10


class SiteConfigBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SiteConfigResponse(SiteConfigBase):
    id: int
    updated_at: Optional[str] = None
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def serialize_updated_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class ProfileBase(BaseModel):
    name: str = "Tech Explorer"
    alias: Optional[str] = None
    slogan: Optional[str] = None
    tags: Optional[List[str]] = []
    avatar: Optional[str] = None
    bio: Optional[str] = None
    tech_stack: Optional[List[dict]] = []
    journey: Optional[List[dict]] = []
    education: Optional[dict] = None
    exploration_areas: Optional[List[str]] = []
    social_github: Optional[str] = None
    social_blog: Optional[str] = None
    social_email: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    slogan: Optional[str] = None
    tags: Optional[List[str]] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    tech_stack: Optional[List[dict]] = None
    journey: Optional[List[dict]] = None
    education: Optional[dict] = None
    exploration_areas: Optional[List[str]] = None
    social_github: Optional[str] = None
    social_blog: Optional[str] = None
    social_email: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    updated_at: Optional[str] = None
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def serialize_updated_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class ArticleFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: str
    is_image: bool


class ArticleFileResponse(ArticleFileBase):
    id: int
    article_id: Optional[int] = None
    download_count: int
    created_at: Optional[str] = None
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_created_at(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class EmailConfigBase(BaseModel):
    provider: str = Field(..., pattern='^(qq|gmail)$')
    smtp_user: str = Field(..., min_length=1)
    smtp_password: str = Field(..., min_length=1)
    from_email: str = Field(..., min_length=1)
    from_name: str = "Futuristic Blog"


class EmailConfigCreate(EmailConfigBase):
    pass


class EmailConfigUpdate(BaseModel):
    provider: Optional[str] = Field(None, pattern='^(qq|gmail)$')
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None


class EmailConfigResponse(BaseModel):
    id: int
    provider: str
    smtp_host: Optional[str] = None
    smtp_port: int
    smtp_user: Optional[str] = None
    from_email: Optional[str] = None
    from_name: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class EmailLogResponse(BaseModel):
    id: int
    email_type: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    verification_token: Optional[str] = None
    is_verified: bool
    verified_at: Optional[str] = None
    user_id: Optional[int] = None
    sent_at: Optional[str] = None
    created_at: Optional[str] = None
    
    @field_validator('verified_at', 'sent_at', 'created_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class EmailTestRequest(BaseModel):
    recipient_email: str


class NotificationSettingsBase(BaseModel):
    notify_on_register: bool = True
    notify_on_comment: bool = True
    notify_on_like: bool = True
    notify_on_reply: bool = True
    require_comment_audit: bool = False


class NotificationSettingsUpdate(BaseModel):
    notify_on_register: Optional[bool] = None
    notify_on_comment: Optional[bool] = None
    notify_on_like: Optional[bool] = None
    notify_on_reply: Optional[bool] = None
    require_comment_audit: Optional[bool] = None


class NotificationSettingsResponse(NotificationSettingsBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


CommentResponse.model_rebuild()
ArticleResponse.model_rebuild()


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=1)
    
    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v):
        return validate_email(v)


class PasswordResetVerify(BaseModel):
    email: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v):
        return validate_email(v)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_type: str = "default"
    avatar_url: Optional[str] = None
    oauth_avatar_url: Optional[str] = None
    default_avatar_gradient: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_datetime_field(cls, v):
        return serialize_datetime(v)
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    avatar_type: Optional[str] = Field(None, pattern='^(default|custom)$')
