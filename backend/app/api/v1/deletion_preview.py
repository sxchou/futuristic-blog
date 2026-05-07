from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

from app.core.database import get_db
from app.models.models import (
    User, Article, Category, Tag, Comment, ArticleLike, ArticleBookmark,
    ArticleFile, Resource, ResourceCategory, Announcement, OAuthProvider,
    OAuthConnection, Role, Permission, EmailConfig, SiteConfig, RefreshToken,
    CommentAuditLog, UserProfile, user_roles, role_permissions, article_tags
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/deletion-preview", tags=["Deletion Preview"])


class ItemType(str, Enum):
    user = "user"
    article = "article"
    category = "category"
    tag = "tag"
    comment = "comment"
    resource = "resource"
    announcement = "announcement"
    oauth_provider = "oauth_provider"
    role = "role"
    permission = "permission"
    email_config = "email_config"
    site_config = "site_config"
    file = "file"
    session = "session"


class AssociatedItem(BaseModel):
    type: str
    type_label: str
    id: Optional[int] = None
    name: str
    detail: Optional[str] = None
    action: str = "delete"
    count: int = 1


class DeletionPreviewResponse(BaseModel):
    item_type: str
    item_type_label: str
    item_id: int
    item_name: str
    can_delete: bool = True
    block_reason: Optional[str] = None
    associated_items: List[AssociatedItem] = []
    total_affected: int = 0


TYPE_LABELS = {
    "user": "用户",
    "article": "文章",
    "category": "分类",
    "tag": "标签",
    "comment": "评论",
    "resource": "资源",
    "announcement": "公告",
    "oauth_provider": "OAuth提供商",
    "role": "角色",
    "permission": "权限",
    "email_config": "邮件配置",
    "site_config": "站点配置",
    "file": "文件",
    "session": "会话",
}

ACTION_LABELS = {
    "delete": "将被删除",
    "unlink": "将解除关联",
    "nullify": "将置为空",
    "soft_delete": "将被软删除",
}


@router.get("/{item_type}/{item_id}", response_model=DeletionPreviewResponse)
async def preview_deletion(
    item_type: ItemType,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    preview = DeletionPreviewResponse(
        item_type=item_type.value,
        item_type_label=TYPE_LABELS.get(item_type.value, item_type.value),
        item_id=item_id,
        item_name="",
    )

    if item_type == ItemType.user:
        _preview_user_deletion(db, item_id, preview)
    elif item_type == ItemType.article:
        _preview_article_deletion(db, item_id, preview)
    elif item_type == ItemType.category:
        _preview_category_deletion(db, item_id, preview)
    elif item_type == ItemType.tag:
        _preview_tag_deletion(db, item_id, preview)
    elif item_type == ItemType.comment:
        _preview_comment_deletion(db, item_id, preview)
    elif item_type == ItemType.resource:
        _preview_resource_deletion(db, item_id, preview)
    elif item_type == ItemType.announcement:
        _preview_announcement_deletion(db, item_id, preview)
    elif item_type == ItemType.oauth_provider:
        _preview_oauth_provider_deletion(db, item_id, preview)
    elif item_type == ItemType.role:
        _preview_role_deletion(db, item_id, preview)
    elif item_type == ItemType.permission:
        _preview_permission_deletion(db, item_id, preview)
    elif item_type == ItemType.email_config:
        _preview_email_config_deletion(db, item_id, preview)
    elif item_type == ItemType.site_config:
        _preview_site_config_deletion(db, item_id, preview)
    elif item_type == ItemType.file:
        _preview_file_deletion(db, item_id, preview)
    elif item_type == ItemType.session:
        _preview_session_deletion(db, item_id, preview)

    preview.total_affected = sum(item.count for item in preview.associated_items)
    return preview


def _add_item(preview: DeletionPreviewResponse, type_key: str, name: str,
              detail: str = None, action: str = "delete", count: int = 1, item_id: int = None):
    preview.associated_items.append(AssociatedItem(
        type=type_key,
        type_label=TYPE_LABELS.get(type_key, type_key),
        id=item_id,
        name=name,
        detail=detail,
        action=action,
        count=count,
    ))


def _preview_user_deletion(db: Session, user_id: int, preview: DeletionPreviewResponse):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    preview.item_name = user.username

    if user_id == 1:
        preview.can_delete = False
        preview.block_reason = "不能删除超级管理员账户"
        return

    count = db.query(OAuthConnection).filter(OAuthConnection.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "oauth_provider", "OAuth连接", f"{count} 条连接记录", count=count)

    count = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "session", "登录会话", f"{count} 个活跃会话", count=count)

    count = db.query(ArticleLike).filter(ArticleLike.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "article", "点赞记录", f"{count} 条点赞记录（相关文章点赞数将减少）", count=count)

    count = db.query(ArticleBookmark).filter(ArticleBookmark.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "article", "收藏记录", f"{count} 条收藏记录（相关文章收藏数将减少）", count=count)

    count = db.query(Comment).filter(Comment.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "comment", "评论", f"{count} 条评论（将保留评论内容，作者显示为已注销）", action="unlink", count=count)

    count = db.query(Comment).filter(Comment.reply_to_user_id == user_id).count()
    if count > 0:
        _add_item(preview, "comment", "评论回复关联", f"{count} 条回复关联（将保留回复上下文）", action="unlink", count=count)

    count = db.query(Article).filter(Article.author_id == user_id).count()
    if count > 0:
        _add_item(preview, "article", "文章", f"{count} 篇文章（将保留文章内容，作者显示为已注销）", action="unlink", count=count)

    count = db.query(ArticleFile).filter(ArticleFile.uploaded_by == user_id).count()
    if count > 0:
        _add_item(preview, "file", "上传文件关联", f"{count} 个文件的上传者关联将被移除", action="unlink", count=count)

    count = db.query(user_roles).filter(user_roles.c.user_id == user_id).count()
    if count > 0:
        _add_item(preview, "role", "角色分配", f"{count} 个角色分配", count=count)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        _add_item(preview, "user", "用户资料", "个人资料将被删除")


def _preview_article_deletion(db: Session, article_id: int, preview: DeletionPreviewResponse):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    preview.item_name = article.title

    count = db.query(Comment).filter(Comment.article_id == article_id).count()
    if count > 0:
        _add_item(preview, "comment", "评论", f"{count} 条评论", count=count)

    count = db.query(ArticleLike).filter(ArticleLike.article_id == article_id).count()
    if count > 0:
        _add_item(preview, "article", "点赞记录", f"{count} 条点赞记录", count=count)

    count = db.query(ArticleBookmark).filter(ArticleBookmark.article_id == article_id).count()
    if count > 0:
        _add_item(preview, "article", "收藏记录", f"{count} 条收藏记录", count=count)

    count = db.query(ArticleFile).filter(ArticleFile.article_id == article_id).count()
    if count > 0:
        _add_item(preview, "file", "附件", f"{count} 个附件文件", count=count)

    count = db.query(article_tags).filter(article_tags.c.article_id == article_id).count()
    if count > 0:
        _add_item(preview, "tag", "标签关联", f"{count} 个标签关联", count=count)


def _preview_category_deletion(db: Session, category_id: int, preview: DeletionPreviewResponse):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    preview.item_name = category.name

    count = db.query(Article).filter(Article.category_id == category_id).count()
    if count > 0:
        preview.can_delete = False
        preview.block_reason = f"此分类被 {count} 篇文章使用，无法删除。请先重新分配文章分类。"
        _add_item(preview, "article", "文章", f"{count} 篇文章正在使用此分类", action="unlink", count=count)


def _preview_tag_deletion(db: Session, tag_id: int, preview: DeletionPreviewResponse):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    preview.item_name = tag.name

    count = db.query(article_tags).filter(article_tags.c.tag_id == tag_id).count()
    if count > 0:
        preview.can_delete = False
        preview.block_reason = f"此标签被 {count} 篇文章使用，无法删除。请先移除文章的标签关联。"
        _add_item(preview, "article", "文章", f"{count} 篇文章正在使用此标签", action="unlink", count=count)


def _preview_comment_deletion(db: Session, comment_id: int, preview: DeletionPreviewResponse):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    preview.item_name = f"评论 #{comment_id}"

    count = db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment_id).count()
    if count > 0:
        _add_item(preview, "comment", "审核日志", f"{count} 条审核日志", count=count)

    child_count = db.query(Comment).filter(Comment.parent_id == comment_id).count()
    if child_count > 0:
        _add_item(preview, "comment", "子评论", f"{child_count} 条子评论（将解除父评论关联，保留子评论）", action="unlink", count=child_count)


def _preview_resource_deletion(db: Session, resource_id: int, preview: DeletionPreviewResponse):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    preview.item_name = resource.title

    if resource.category_id:
        category = db.query(ResourceCategory).filter(ResourceCategory.id == resource.category_id).first()
        if category:
            _add_item(preview, "resource_category", "所属分类", f"将从分类「{category.name}」中移除", action="unlink")


def _preview_announcement_deletion(db: Session, announcement_id: int, preview: DeletionPreviewResponse):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    preview.item_name = announcement.title


def _preview_oauth_provider_deletion(db: Session, provider_id: int, preview: DeletionPreviewResponse):
    provider = db.query(OAuthProvider).filter(OAuthProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="OAuth提供商不存在")

    preview.item_name = provider.display_name

    count = db.query(OAuthConnection).filter(OAuthConnection.provider_id == provider_id).count()
    if count > 0:
        _add_item(preview, "user", "OAuth连接", f"{count} 个用户的OAuth连接将被删除", count=count)


def _preview_role_deletion(db: Session, role_id: int, preview: DeletionPreviewResponse):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    preview.item_name = role.name

    if role.is_system:
        preview.can_delete = False
        preview.block_reason = "系统角色不能删除"
        return

    count = db.query(user_roles).filter(user_roles.c.role_id == role_id).count()
    if count > 0:
        _add_item(preview, "user", "用户角色分配", f"{count} 个用户的角色分配将被移除", action="unlink", count=count)

    count = db.query(role_permissions).filter(role_permissions.c.role_id == role_id).count()
    if count > 0:
        _add_item(preview, "permission", "权限分配", f"{count} 个权限分配将被移除", action="unlink", count=count)


def _preview_permission_deletion(db: Session, permission_id: int, preview: DeletionPreviewResponse):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    preview.item_name = permission.name

    count = db.query(role_permissions).filter(role_permissions.c.permission_id == permission_id).count()
    if count > 0:
        _add_item(preview, "role", "角色权限分配", f"{count} 个角色的权限分配将被移除", action="unlink", count=count)


def _preview_email_config_deletion(db: Session, config_id: int, preview: DeletionPreviewResponse):
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="邮件配置不存在")

    preview.item_name = f"{config.provider} - {config.smtp_user}"


def _preview_site_config_deletion(db: Session, config_id: int, preview: DeletionPreviewResponse):
    config = db.query(SiteConfig).filter(SiteConfig.key == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="站点配置不存在")

    preview.item_name = config.key


def _preview_file_deletion(db: Session, file_id: int, preview: DeletionPreviewResponse):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    preview.item_name = db_file.original_filename

    if db_file.article_id:
        article = db.query(Article).filter(Article.id == db_file.article_id).first()
        if article:
            _add_item(preview, "article", "所属文章", f"将从文章「{article.title}」中移除", action="unlink")


def _preview_session_deletion(db: Session, session_id: int, preview: DeletionPreviewResponse):
    session = db.query(RefreshToken).filter(RefreshToken.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    preview.item_name = f"会话 #{session_id}"

    if session.user_id:
        user = db.query(User).filter(User.id == session.user_id).first()
        if user:
            _add_item(preview, "user", "所属用户", f"将终止用户「{user.username}」的此会话", action="unlink")


class DetailItem(BaseModel):
    id: Optional[int] = None
    name: str
    detail: Optional[str] = None


class DetailResponse(BaseModel):
    items: List[DetailItem] = []
    total: int = 0
    showing: int = 0


DETAIL_FETCHERS = {}


def _register_detail_fetcher(item_type: str, assoc_key: str):
    def decorator(func):
        DETAIL_FETCHERS[(item_type, assoc_key)] = func
        return func
    return decorator


@_register_detail_fetcher("user", "oauth_connection")
def _fetch_user_oauth_connections(db: Session, user_id: int, limit: int):
    query = db.query(OAuthConnection).filter(OAuthConnection.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.provider_name or "OAuth", detail=f"provider_user_id: {r.provider_user_id}") for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "session")
def _fetch_user_sessions(db: Session, user_id: int, limit: int):
    query = db.query(RefreshToken).filter(RefreshToken.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"会话 #{r.id}", detail=f"创建于 {r.created_at}" if r.created_at else None) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "article_like")
def _fetch_user_article_likes(db: Session, user_id: int, limit: int):
    query = db.query(ArticleLike).filter(ArticleLike.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        article = db.query(Article).filter(Article.id == r.article_id).first()
        items.append(DetailItem(id=r.article_id, name=article.title if article else f"文章 #{r.article_id}", detail="点赞"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "article_bookmark")
def _fetch_user_article_bookmarks(db: Session, user_id: int, limit: int):
    query = db.query(ArticleBookmark).filter(ArticleBookmark.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        article = db.query(Article).filter(Article.id == r.article_id).first()
        items.append(DetailItem(id=r.article_id, name=article.title if article else f"文章 #{r.article_id}", detail="收藏"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "comment")
def _fetch_user_comments(db: Session, user_id: int, limit: int):
    query = db.query(Comment).filter(Comment.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"评论 #{r.id}", detail=(r.content[:50] + '...') if r.content and len(r.content) > 50 else r.content) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "comment_reply")
def _fetch_user_comment_replies(db: Session, user_id: int, limit: int):
    query = db.query(Comment).filter(Comment.reply_to_user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"评论 #{r.id}", detail=(r.content[:50] + '...') if r.content and len(r.content) > 50 else r.content) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "article")
def _fetch_user_articles(db: Session, user_id: int, limit: int):
    query = db.query(Article).filter(Article.author_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.title, detail="已发布" if r.is_published else "草稿") for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "article_file")
def _fetch_user_article_files(db: Session, user_id: int, limit: int):
    query = db.query(ArticleFile).filter(ArticleFile.uploaded_by == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.original_filename or r.filename, detail=f"大小: {r.file_size} 字节" if r.file_size else None) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "user_role")
def _fetch_user_roles(db: Session, user_id: int, limit: int):
    query = db.query(user_roles).filter(user_roles.c.user_id == user_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        role = db.query(Role).filter(Role.id == r.role_id).first()
        items.append(DetailItem(id=r.role_id, name=role.name if role else f"角色 #{r.role_id}"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("article", "comment")
def _fetch_article_comments(db: Session, article_id: int, limit: int):
    query = db.query(Comment).filter(Comment.article_id == article_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"评论 #{r.id}", detail=(r.content[:50] + '...') if r.content and len(r.content) > 50 else r.content) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("article", "article_like")
def _fetch_article_likes(db: Session, article_id: int, limit: int):
    query = db.query(ArticleLike).filter(ArticleLike.article_id == article_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        user = db.query(User).filter(User.id == r.user_id).first()
        items.append(DetailItem(id=r.user_id, name=user.username if user else f"用户 #{r.user_id}", detail="点赞"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("article", "article_bookmark")
def _fetch_article_bookmarks(db: Session, article_id: int, limit: int):
    query = db.query(ArticleBookmark).filter(ArticleBookmark.article_id == article_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        user = db.query(User).filter(User.id == r.user_id).first()
        items.append(DetailItem(id=r.user_id, name=user.username if user else f"用户 #{r.user_id}", detail="收藏"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("article", "article_file")
def _fetch_article_files(db: Session, article_id: int, limit: int):
    query = db.query(ArticleFile).filter(ArticleFile.article_id == article_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.original_filename or r.filename, detail=f"大小: {r.file_size} 字节" if r.file_size else None) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("article", "article_tag")
def _fetch_article_tags(db: Session, article_id: int, limit: int):
    query = db.query(article_tags).filter(article_tags.c.article_id == article_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        tag = db.query(Tag).filter(Tag.id == r.tag_id).first()
        items.append(DetailItem(id=r.tag_id, name=tag.name if tag else f"标签 #{r.tag_id}"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("category", "article")
def _fetch_category_articles(db: Session, category_id: int, limit: int):
    query = db.query(Article).filter(Article.category_id == category_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.title, detail="已发布" if r.is_published else "草稿") for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("tag", "article")
def _fetch_tag_articles(db: Session, tag_id: int, limit: int):
    query = db.query(Article).join(article_tags, Article.id == article_tags.c.article_id).filter(article_tags.c.tag_id == tag_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=r.title, detail="已发布" if r.is_published else "草稿") for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("comment", "audit_log")
def _fetch_comment_audit_logs(db: Session, comment_id: int, limit: int):
    query = db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"审核日志 #{r.id}", detail=f"{r.old_status or '无'} → {r.new_status}" if r.old_status else r.new_status) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("comment", "child_comment")
def _fetch_comment_children(db: Session, comment_id: int, limit: int):
    query = db.query(Comment).filter(Comment.parent_id == comment_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = [DetailItem(id=r.id, name=f"评论 #{r.id}", detail=(r.content[:50] + '...') if r.content and len(r.content) > 50 else r.content) for r in rows]
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("oauth_provider", "oauth_connection")
def _fetch_oauth_provider_connections(db: Session, provider_id: int, limit: int):
    query = db.query(OAuthConnection).filter(OAuthConnection.provider_id == provider_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        user = db.query(User).filter(User.id == r.user_id).first()
        items.append(DetailItem(id=r.id, name=user.username if user else f"用户 #{r.user_id}", detail=f"provider_user_id: {r.provider_user_id}"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("role", "user_role")
def _fetch_role_user_roles(db: Session, role_id: int, limit: int):
    query = db.query(user_roles).filter(user_roles.c.role_id == role_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        user = db.query(User).filter(User.id == r.user_id).first()
        items.append(DetailItem(id=r.user_id, name=user.username if user else f"用户 #{r.user_id}"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("role", "role_permission")
def _fetch_role_permissions(db: Session, role_id: int, limit: int):
    query = db.query(role_permissions).filter(role_permissions.c.role_id == role_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        perm = db.query(Permission).filter(Permission.id == r.permission_id).first()
        items.append(DetailItem(id=r.permission_id, name=perm.name if perm else f"权限 #{r.permission_id}", detail=perm.code if perm else None))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("permission", "role_permission")
def _fetch_permission_role_permissions(db: Session, permission_id: int, limit: int):
    query = db.query(role_permissions).filter(role_permissions.c.permission_id == permission_id)
    total = query.count()
    rows = query.limit(limit).all() if limit > 0 else query.all()
    items = []
    for r in rows:
        role = db.query(Role).filter(Role.id == r.role_id).first()
        items.append(DetailItem(id=r.role_id, name=role.name if role else f"角色 #{r.role_id}"))
    return DetailResponse(items=items, total=total, showing=len(items))


@_register_detail_fetcher("user", "user_profile")
def _fetch_user_profile(db: Session, user_id: int, limit: int):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return DetailResponse(items=[], total=0, showing=0)
    items = [DetailItem(id=profile.id, name="个人资料", detail=f"头像类型: {profile.avatar_type.value if profile.avatar_type else 'default'}")]
    return DetailResponse(items=items, total=1, showing=1)


@_register_detail_fetcher("resource", "resource_category")
def _fetch_resource_category(db: Session, resource_id: int, limit: int):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource or not resource.category_id:
        return DetailResponse(items=[], total=0, showing=0)
    category = db.query(ResourceCategory).filter(ResourceCategory.id == resource.category_id).first()
    if not category:
        return DetailResponse(items=[], total=0, showing=0)
    items = [DetailItem(id=category.id, name=category.name, detail="资源将从此分类中移除")]
    return DetailResponse(items=items, total=1, showing=1)


@_register_detail_fetcher("file", "article")
def _fetch_file_article(db: Session, file_id: int, limit: int):
    db_file = db.query(ArticleFile).filter(ArticleFile.id == file_id).first()
    if not db_file or not db_file.article_id:
        return DetailResponse(items=[], total=0, showing=0)
    article = db.query(Article).filter(Article.id == db_file.article_id).first()
    if not article:
        return DetailResponse(items=[], total=0, showing=0)
    items = [DetailItem(id=article.id, name=article.title, detail="文件将从此文章中移除")]
    return DetailResponse(items=items, total=1, showing=1)


@_register_detail_fetcher("session", "session_user")
def _fetch_session_user(db: Session, session_id: int, limit: int):
    session = db.query(RefreshToken).filter(RefreshToken.id == session_id).first()
    if not session or not session.user_id:
        return DetailResponse(items=[], total=0, showing=0)
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        return DetailResponse(items=[], total=0, showing=0)
    items = [DetailItem(id=user.id, name=user.username, detail="将终止此用户的会话")]
    return DetailResponse(items=items, total=1, showing=1)


ASSOC_KEY_MAP = {
    ("user", "OAuth连接"): "oauth_connection",
    ("user", "登录会话"): "session",
    ("user", "点赞记录"): "article_like",
    ("user", "收藏记录"): "article_bookmark",
    ("user", "评论"): "comment",
    ("user", "评论回复关联"): "comment_reply",
    ("user", "文章"): "article",
    ("user", "上传文件关联"): "article_file",
    ("user", "角色分配"): "user_role",
    ("user", "用户资料"): "user_profile",
    ("article", "评论"): "comment",
    ("article", "点赞记录"): "article_like",
    ("article", "收藏记录"): "article_bookmark",
    ("article", "附件"): "article_file",
    ("article", "标签关联"): "article_tag",
    ("category", "文章"): "article",
    ("tag", "文章"): "article",
    ("comment", "审核日志"): "audit_log",
    ("comment", "子评论"): "child_comment",
    ("oauth_provider", "OAuth连接"): "oauth_connection",
    ("role", "用户角色分配"): "user_role",
    ("role", "权限分配"): "role_permission",
    ("permission", "角色权限分配"): "role_permission",
    ("resource", "所属分类"): "resource_category",
    ("file", "所属文章"): "article",
    ("session", "所属用户"): "session_user",
}


@router.get("/{item_type}/{item_id}/details", response_model=DetailResponse)
async def get_deletion_details(
    item_type: ItemType,
    item_id: int,
    assoc_type: str = Query(..., description="关联项类型"),
    assoc_name: str = Query(..., description="关联项名称"),
    limit: int = Query(5, description="返回数量，0表示全部", ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assoc_key = ASSOC_KEY_MAP.get((item_type.value, assoc_name))
    if not assoc_key:
        raise HTTPException(status_code=400, detail=f"不支持的关联项类型: {item_type.value}/{assoc_name}")

    fetcher = DETAIL_FETCHERS.get((item_type.value, assoc_key))
    if not fetcher:
        raise HTTPException(status_code=400, detail=f"暂不支持查看该关联项明细: {item_type.value}/{assoc_key}")

    return fetcher(db, item_id, limit)
