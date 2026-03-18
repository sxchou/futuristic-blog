from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, UniqueConstraint, Float, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


def get_local_now():
    from app.utils.timezone import get_now
    return get_now()


article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Index('ix_article_tags_article_id', 'article_id'),
    Index('ix_article_tags_tag_id', 'tag_id')
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    avatar = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_local_now)


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    slug = Column(String(30), unique=True, nullable=False)
    color = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=get_local_now)


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    cover_image = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    is_published = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    reading_time = Column(Integer, default=5)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=get_local_now, index=True)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)
    
    __table_args__ = (
        Index('ix_articles_published_created', 'is_published', 'created_at'),
        Index('ix_articles_published_featured', 'is_published', 'is_featured'),
        Index('ix_articles_category_published', 'category_id', 'is_published'),
    )
    
    category = relationship("Category", backref="articles")
    author = relationship("User", backref="articles")
    tags = relationship("Tag", secondary=article_tags, backref="articles")


class ArticleLike(Base):
    __tablename__ = "article_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=get_local_now)


class ArticleFile(Base):
    __tablename__ = "article_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=True)
    mime_type = Column(String(100), nullable=True)
    is_image = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=True)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    
    article = relationship("Article", backref="files")
    uploader = relationship("User", backref="uploaded_files")


class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    icon = Column(String(50), nullable=True)
    category = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    resource_type = Column(String(20), default='link')
    created_at = Column(DateTime, default=get_local_now)


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    author_name = Column(String(50), nullable=True)
    author_email = Column(String(100), nullable=True)
    author_url = Column(String(255), nullable=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, index=True)
    is_approved = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_by = Column(String(20), nullable=True)
    reply_to_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(20), default='approved', index=True)
    created_at = Column(DateTime, default=get_local_now, index=True)
    
    __table_args__ = (
        Index('ix_comments_article_status_deleted', 'article_id', 'status', 'is_deleted'),
        Index('ix_comments_status_deleted', 'status', 'is_deleted'),
    )
    
    article = relationship("Article", backref="comments")
    user = relationship("User", foreign_keys=[user_id], backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    reply_to_user = relationship("User", foreign_keys=[reply_to_user_id])
    audit_logs = relationship("CommentAuditLog", back_populates="comment", order_by="desc(CommentAuditLog.created_at)")


class CommentAuditLog(Base):
    __tablename__ = "comment_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    operator_name = Column(String(50), nullable=True)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    
    comment = relationship("Comment", back_populates="audit_logs")
    operator = relationship("User")


class SiteConfig(Base):
    __tablename__ = "site_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    alias = Column(String(100), nullable=True)
    slogan = Column(String(255), nullable=True)
    tags = Column(Text, nullable=True)
    avatar = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    tech_stack = Column(Text, nullable=True)
    journey = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    exploration_areas = Column(Text, nullable=True)
    social_github = Column(String(255), nullable=True)
    social_blog = Column(String(255), nullable=True)
    social_email = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class EmailConfig(Base):
    __tablename__ = "email_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), nullable=True)
    smtp_host = Column(String(100), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_user = Column(String(100), nullable=False)
    smtp_password = Column(String(255), nullable=False)
    from_email = Column(String(100), nullable=False)
    from_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    email_type = Column(String(50), nullable=True)
    recipient_email = Column(String(100), nullable=False)
    recipient_name = Column(String(100), nullable=True)
    subject = Column(String(255), nullable=False)
    status = Column(String(20), default='pending')
    error_message = Column(Text, nullable=True)
    verification_token = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    
    user = relationship("User", backref="email_logs")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    notify_on_register = Column(Boolean, default=True)
    notify_on_comment = Column(Boolean, default=True)
    notify_on_like = Column(Boolean, default=True)
    notify_on_reply = Column(Boolean, default=True)
    require_comment_audit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)
    module = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_url = Column(String(500), nullable=True)
    request_params = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default='success')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_local_now, index=True)
    
    user = relationship("User")


class LoginLog(Base):
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(50), nullable=True)
    login_type = Column(String(20), default='login')
    ip_address = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    browser = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    device = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default='success')
    fail_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_local_now, index=True)
    
    user = relationship("User")


class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(50), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_query = Column(String(500), nullable=True)
    response_status = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referer = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=get_local_now, index=True)
    
    user = relationship("User")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    ip_address = Column(String(50), nullable=True)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=get_local_now)


class AvatarType(str, enum.Enum):
    default = "default"
    custom = "custom"


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    avatar_type = Column(SQLEnum(AvatarType), default=AvatarType.default, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    default_avatar_gradient = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)
    
    user = relationship("User", backref="profile", uselist=False)


class OAuthProvider(Base):
    __tablename__ = "oauth_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    client_id = Column(String(255), nullable=True)
    client_secret = Column(String(255), nullable=True)
    redirect_uri = Column(String(500), nullable=True)
    authorize_url = Column(String(500), nullable=True)
    token_url = Column(String(500), nullable=True)
    userinfo_url = Column(String(500), nullable=True)
    scope = Column(String(255), nullable=True)
    is_enabled = Column(Boolean, default=False)
    show_on_login = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)


class OAuthConnection(Base):
    __tablename__ = "oauth_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey('oauth_providers.id', ondelete='CASCADE'), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_local_now)
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now)
    
    user = relationship("User", backref="oauth_connections")
    provider = relationship("OAuthProvider", backref="connections")
    
    __table_args__ = (UniqueConstraint('provider_id', 'provider_user_id', name='unique_oauth_connection'),)


class OAuthTempToken(Base):
    __tablename__ = "oauth_temp_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    temp_token = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider_name = Column(String(50), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=get_local_now)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", backref="oauth_temp_tokens")
