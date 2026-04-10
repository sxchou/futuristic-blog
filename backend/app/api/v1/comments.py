from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models import Comment, Article, User, NotificationSettings, CommentAuditLog, UserProfile, AvatarType
from app.schemas import (
    CommentCreate, CommentResponse, CommentAuditRequest, 
    BatchAuditRequest, CommentAuditLogResponse, AdminCommentResponse,
    PaginatedResponse
)
from app.utils import get_current_user, get_current_admin_user
from app.services.email_service import EmailService

router = APIRouter(prefix="/comments", tags=["Comments"])


def get_user_avatar_info(db: Session, user_id: Optional[int]) -> Dict[str, Any]:
    if not user_id:
        return {
            'avatar_type': None,
            'avatar_url': None,
            'avatar_gradient': None
        }
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if profile:
        if profile.avatar_type == AvatarType.custom and profile.avatar_url:
            return {
                'avatar_type': 'custom',
                'avatar_url': profile.avatar_url,
                'avatar_gradient': profile.default_avatar_gradient
            }
        
        if profile.oauth_avatar_url:
            return {
                'avatar_type': 'oauth',
                'avatar_url': profile.oauth_avatar_url,
                'avatar_gradient': profile.default_avatar_gradient
            }
        
        return {
            'avatar_type': 'default',
            'avatar_url': None,
            'avatar_gradient': profile.default_avatar_gradient
        }
    
    return {
        'avatar_type': 'default',
        'avatar_url': None,
        'avatar_gradient': None
    }


def build_comment_tree(comments: List[Comment], db: Session) -> List[dict]:
    comment_dict = {}
    root_comments = []
    
    user_avatar_cache = {}
    
    for comment in comments:
        reply_to_user_name = None
        reply_to_user_avatar = {
            'avatar_type': None,
            'avatar_url': None,
            'avatar_gradient': None
        }
        
        if comment.reply_to_user_id:
            if comment.reply_to_user:
                reply_to_user_name = comment.reply_to_user.username
            else:
                reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first()
                reply_to_user_name = reply_to_user.username if reply_to_user else None
            
            if comment.reply_to_user_id not in user_avatar_cache:
                user_avatar_cache[comment.reply_to_user_id] = get_user_avatar_info(db, comment.reply_to_user_id)
            reply_to_user_avatar = user_avatar_cache[comment.reply_to_user_id]
        
        author_avatar = {
            'avatar_type': None,
            'avatar_url': None,
            'avatar_gradient': None
        }
        if comment.user_id:
            if comment.user_id not in user_avatar_cache:
                user_avatar_cache[comment.user_id] = get_user_avatar_info(db, comment.user_id)
            author_avatar = user_avatar_cache[comment.user_id]
        
        comment_data = {
            'id': comment.id,
            'content': comment.content,
            'article_id': comment.article_id,
            'parent_id': comment.parent_id,
            'user_id': comment.user_id,
            'author_name': comment.author_name,
            'author_email': comment.author_email,
            'author_url': comment.author_url,
            'author_avatar_type': author_avatar['avatar_type'],
            'author_avatar_url': author_avatar['avatar_url'],
            'author_avatar_gradient': author_avatar['avatar_gradient'],
            'status': comment.status,
            'is_deleted': comment.is_deleted,
            'deleted_by': comment.deleted_by,
            'reply_to_user_id': comment.reply_to_user_id,
            'reply_to_user_name': reply_to_user_name,
            'reply_to_user_avatar_type': reply_to_user_avatar['avatar_type'],
            'reply_to_user_avatar_url': reply_to_user_avatar['avatar_url'],
            'reply_to_user_avatar_gradient': reply_to_user_avatar['avatar_gradient'],
            'created_at': comment.created_at,
            'replies': []
        }
        comment_dict[comment.id] = comment_data
    
    for comment_id, comment_data in comment_dict.items():
        if comment_data['parent_id'] is None:
            root_comments.append(comment_data)
        else:
            parent = comment_dict.get(comment_data['parent_id'])
            if parent:
                parent['replies'].append(comment_data)
    
    return root_comments


def send_comment_notification_bg(article_title: str, article_slug: str, commenter_name: str, comment_content: str, comment_id: int = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        notification_settings = db.query(NotificationSettings).first()
        if notification_settings and notification_settings.notify_on_comment:
            EmailService.send_new_comment_notification_db(
                db=db,
                commenter_name=commenter_name,
                article_title=article_title,
                article_slug=article_slug,
                comment_content=comment_content,
                comment_id=comment_id
            )
    except Exception as e:
        print(f"Failed to send comment notification: {e}")
    finally:
        db.close()


def send_pending_comment_notification_bg(article_title: str, article_slug: str, commenter_name: str, comment_content: str, comment_id: int = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        notification_settings = db.query(NotificationSettings).first()
        if notification_settings and notification_settings.notify_on_comment:
            EmailService.send_pending_comment_notification_db(
                db=db,
                commenter_name=commenter_name,
                article_title=article_title,
                article_slug=article_slug,
                comment_content=comment_content,
                comment_id=comment_id
            )
    except Exception as e:
        print(f"Failed to send pending comment notification: {e}")
    finally:
        db.close()


def send_comment_approved_notification_bg(recipient_email: str, recipient_name: str, article_title: str, article_slug: str, comment_content: str, comment_id: int = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        EmailService.send_comment_approved_notification_db(
            db=db,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            article_title=article_title,
            article_slug=article_slug,
            comment_content=comment_content,
            comment_id=comment_id
        )
    except Exception as e:
        print(f"Failed to send comment approved notification: {e}")
    finally:
        db.close()


def send_reply_notification_bg(
    recipient_email: str,
    recipient_name: str,
    article_title: str,
    article_slug: str,
    reply_content: str,
    commenter_name: str,
    comment_id: int = None,
    parent_comment_id: int = None
):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        notification_settings = db.query(NotificationSettings).first()
        if notification_settings and notification_settings.notify_on_reply:
            EmailService.send_reply_notification_db(
                db=db,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                article_title=article_title,
                article_slug=article_slug,
                reply_content=reply_content,
                commenter_name=commenter_name,
                comment_id=comment_id,
                parent_comment_id=parent_comment_id
            )
    except Exception as e:
        print(f"Failed to send reply notification: {e}")
    finally:
        db.close()


@router.get("/article/{article_id}", response_model=List[CommentResponse])
async def get_article_comments(
    article_id: int,
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    comments = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.reply_to_user)
    ).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved'
    ).order_by(Comment.created_at.desc()).all()
    
    return build_comment_tree(comments, db)


@router.post("", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == comment_data.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    notification_settings = db.query(NotificationSettings).first()
    require_audit = notification_settings.require_comment_audit if notification_settings else False
    
    parent_comment = None
    reply_to_user_id = None
    
    if comment_data.parent_id:
        parent_comment = db.query(Comment).options(
            joinedload(Comment.user)
        ).filter(Comment.id == comment_data.parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        
        if parent_comment.user_id:
            reply_to_user_id = parent_comment.user_id
    
    initial_status = 'pending' if require_audit else 'approved'
    
    new_comment = Comment(
        content=comment_data.content,
        article_id=comment_data.article_id,
        parent_id=comment_data.parent_id,
        user_id=current_user.id,
        author_name=current_user.username,
        author_email=current_user.email,
        status=initial_status,
        reply_to_user_id=reply_to_user_id
    )
    
    db.add(new_comment)
    
    if initial_status == 'approved':
        article.comment_count = (article.comment_count or 0) + 1
    
    db.commit()
    db.refresh(new_comment)
    
    if initial_status == 'approved':
        background_tasks.add_task(
            send_comment_notification_bg,
            article.title,
            article.slug,
            current_user.username,
            comment_data.content,
            new_comment.id
        )
        
        if parent_comment and parent_comment.user_id != current_user.id:
            parent_user = db.query(User).filter(User.id == parent_comment.user_id).first()
            if parent_user and parent_user.email:
                background_tasks.add_task(
                    send_reply_notification_bg,
                    parent_user.email,
                    parent_user.username,
                    article.title,
                    article.slug,
                    comment_data.content,
                    current_user.username,
                    new_comment.id,
                    parent_comment.id
                )
    else:
        background_tasks.add_task(
            send_pending_comment_notification_bg,
            article.title,
            article.slug,
            current_user.username,
            comment_data.content,
            new_comment.id
        )
    
    reply_to_user_name = None
    reply_to_user_avatar = {'avatar_type': None, 'avatar_url': None, 'avatar_gradient': None}
    if new_comment.reply_to_user_id:
        reply_to_user = db.query(User).filter(User.id == new_comment.reply_to_user_id).first()
        reply_to_user_name = reply_to_user.username if reply_to_user else None
        reply_to_user_avatar = get_user_avatar_info(db, new_comment.reply_to_user_id)
    
    author_avatar = get_user_avatar_info(db, current_user.id)
    
    return CommentResponse(
        id=new_comment.id,
        content=new_comment.content,
        article_id=new_comment.article_id,
        parent_id=new_comment.parent_id,
        user_id=new_comment.user_id,
        author_name=new_comment.author_name,
        author_email=new_comment.author_email,
        author_url=new_comment.author_url,
        author_avatar_type=author_avatar['avatar_type'],
        author_avatar_url=author_avatar['avatar_url'],
        author_avatar_gradient=author_avatar['avatar_gradient'],
        status=new_comment.status,
        is_deleted=new_comment.is_deleted,
        reply_to_user_id=new_comment.reply_to_user_id,
        reply_to_user_name=reply_to_user_name,
        reply_to_user_avatar_type=reply_to_user_avatar['avatar_type'],
        reply_to_user_avatar_url=reply_to_user_avatar['avatar_url'],
        reply_to_user_avatar_gradient=reply_to_user_avatar['avatar_gradient'],
        created_at=new_comment.created_at,
        replies=[]
    )


@router.get("/user/commented", response_model=PaginatedResponse)
async def get_user_commented_articles(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import func
    from app.schemas import ArticleListItem
    
    subquery = db.query(
        Comment.article_id,
        func.max(Comment.created_at).label('last_comment_at')
    ).filter(
        Comment.user_id == current_user.id,
        Comment.is_deleted == False,
        Comment.status == 'approved'
    ).group_by(Comment.article_id).subquery()
    
    total = db.query(subquery).count()
    
    results = db.query(
        subquery.c.article_id,
        subquery.c.last_comment_at
    ).order_by(
        subquery.c.last_comment_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    articles = []
    for result in results:
        article = db.query(Article).filter(Article.id == result.article_id).first()
        if article:
            articles.append(ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                summary=article.summary,
                cover_image=article.cover_image,
                view_count=article.view_count,
                like_count=article.like_count,
                comment_count=article.comment_count,
                is_published=article.is_published,
                is_featured=article.is_featured,
                is_pinned=article.is_pinned,
                reading_time=article.reading_time,
                created_at=article.created_at,
                published_at=article.published_at,
                category=article.category,
                tags=article.tags,
                commented_at=result.last_comment_at
            ))
    
    return PaginatedResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    if not comment.is_deleted and comment.status == 'approved':
        article = db.query(Article).filter(Article.id == comment.article_id).first()
        if article and article.comment_count and article.comment_count > 0:
            article.comment_count -= 1
    
    comment.is_deleted = True
    comment.deleted_by = 'user'
    comment.content = "此评论已被用户删除"
    db.commit()
    
    return {"message": "Comment deleted successfully"}


@router.get("/admin", response_model=PaginatedResponse)
async def get_admin_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern='^(pending|approved|rejected)$'),
    article_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Comment).options(
        joinedload(Comment.article),
        joinedload(Comment.user),
        joinedload(Comment.reply_to_user)
    )
    
    if status:
        query = query.filter(Comment.status == status)
    
    if article_id:
        query = query.filter(Comment.article_id == article_id)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    comments = query.order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    user_avatar_cache = {}
    
    items = []
    for comment in comments:
        reply_to_user_name = None
        reply_to_user_avatar = {'avatar_type': None, 'avatar_url': None, 'avatar_gradient': None}
        if comment.reply_to_user_id:
            reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first()
            reply_to_user_name = reply_to_user.username if reply_to_user else None
            if comment.reply_to_user_id not in user_avatar_cache:
                user_avatar_cache[comment.reply_to_user_id] = get_user_avatar_info(db, comment.reply_to_user_id)
            reply_to_user_avatar = user_avatar_cache[comment.reply_to_user_id]
        
        author_avatar = {'avatar_type': None, 'avatar_url': None, 'avatar_gradient': None}
        if comment.user_id:
            if comment.user_id not in user_avatar_cache:
                user_avatar_cache[comment.user_id] = get_user_avatar_info(db, comment.user_id)
            author_avatar = user_avatar_cache[comment.user_id]
        
        items.append(AdminCommentResponse(
            id=comment.id,
            content=comment.content,
            article_id=comment.article_id,
            article_title=comment.article.title if comment.article else None,
            article_slug=comment.article.slug if comment.article else None,
            parent_id=comment.parent_id,
            user_id=comment.user_id,
            author_name=comment.author_name,
            author_email=comment.author_email,
            author_url=comment.author_url,
            author_avatar_type=author_avatar['avatar_type'],
            author_avatar_url=author_avatar['avatar_url'],
            author_avatar_gradient=author_avatar['avatar_gradient'],
            status=comment.status,
            is_deleted=comment.is_deleted,
            reply_to_user_id=comment.reply_to_user_id,
            reply_to_user_name=reply_to_user_name,
            reply_to_user_avatar_type=reply_to_user_avatar['avatar_type'],
            reply_to_user_avatar_url=reply_to_user_avatar['avatar_url'],
            reply_to_user_avatar_gradient=reply_to_user_avatar['avatar_gradient'],
            created_at=comment.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.put("/admin/{comment_id}/audit", response_model=AdminCommentResponse)
async def audit_comment(
    comment_id: int,
    audit_data: CommentAuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    comment = db.query(Comment).options(
        joinedload(Comment.article),
        joinedload(Comment.user)
    ).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    old_status = comment.status
    comment.status = audit_data.status
    
    if old_status != 'approved' and audit_data.status == 'approved':
        if comment.article:
            comment.article.comment_count = (comment.article.comment_count or 0) + 1
    elif old_status == 'approved' and audit_data.status != 'approved':
        if comment.article and comment.article.comment_count and comment.article.comment_count > 0:
            comment.article.comment_count -= 1
    
    db.commit()
    
    audit_log = CommentAuditLog(
        comment_id=comment_id,
        operator_id=current_user.id,
        operator_name=current_user.username,
        old_status=old_status,
        new_status=audit_data.status,
        reason=audit_data.reason
    )
    db.add(audit_log)
    db.commit()
    
    if old_status == 'pending' and audit_data.status == 'approved':
        if comment.author_email:
            background_tasks.add_task(
                send_comment_approved_notification_bg,
                comment.author_email,
                comment.author_name,
                comment.article.title if comment.article else '',
                comment.article.slug if comment.article else '',
                comment.content,
                comment.id
            )
    
    reply_to_user_name = None
    reply_to_user_avatar = {'avatar_type': None, 'avatar_url': None, 'avatar_gradient': None}
    if comment.reply_to_user_id:
        reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first()
        reply_to_user_name = reply_to_user.username if reply_to_user else None
        reply_to_user_avatar = get_user_avatar_info(db, comment.reply_to_user_id)
    
    author_avatar = get_user_avatar_info(db, comment.user_id)
    
    return AdminCommentResponse(
        id=comment.id,
        content=comment.content,
        article_id=comment.article_id,
        article_title=comment.article.title if comment.article else None,
        parent_id=comment.parent_id,
        user_id=comment.user_id,
        author_name=comment.author_name,
        author_email=comment.author_email,
        author_url=comment.author_url,
        author_avatar_type=author_avatar['avatar_type'],
        author_avatar_url=author_avatar['avatar_url'],
        author_avatar_gradient=author_avatar['avatar_gradient'],
        status=comment.status,
        is_deleted=comment.is_deleted,
        reply_to_user_id=comment.reply_to_user_id,
        reply_to_user_name=reply_to_user_name,
        reply_to_user_avatar_type=reply_to_user_avatar['avatar_type'],
        reply_to_user_avatar_url=reply_to_user_avatar['avatar_url'],
        reply_to_user_avatar_gradient=reply_to_user_avatar['avatar_gradient'],
        created_at=comment.created_at
    )


@router.post("/admin/batch-audit")
async def batch_audit_comments(
    audit_data: BatchAuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    comments = db.query(Comment).options(
        joinedload(Comment.article)
    ).filter(Comment.id.in_(audit_data.comment_ids)).all()
    
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")
    
    updated_count = 0
    for comment in comments:
        old_status = comment.status
        comment.status = audit_data.status
        
        audit_log = CommentAuditLog(
            comment_id=comment.id,
            operator_id=current_user.id,
            operator_name=current_user.username,
            old_status=old_status,
            new_status=audit_data.status,
            reason=audit_data.reason
        )
        db.add(audit_log)
        updated_count += 1
        
        if old_status == 'pending' and audit_data.status == 'approved':
            if comment.author_email:
                background_tasks.add_task(
                    send_comment_approved_notification_bg,
                    comment.author_email,
                    comment.author_name,
                    comment.article.title if comment.article else '',
                    comment.article.slug if comment.article else '',
                    comment.content,
                    comment.id
                )
    
    db.commit()
    
    return {
        "message": f"Successfully updated {updated_count} comments",
        "updated_count": updated_count
    }


@router.get("/admin/{comment_id}/logs", response_model=List[CommentAuditLogResponse])
async def get_comment_audit_logs(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    logs = db.query(CommentAuditLog).options(
        joinedload(CommentAuditLog.operator)
    ).filter(CommentAuditLog.comment_id == comment_id).order_by(CommentAuditLog.created_at.desc()).all()
    
    return [CommentAuditLogResponse(
        id=log.id,
        comment_id=log.comment_id,
        operator_id=log.operator_id,
        operator_name=log.operator_name,
        old_status=log.old_status,
        new_status=log.new_status,
        reason=log.reason,
        created_at=log.created_at
    ) for log in logs]


@router.delete("/admin/{comment_id}")
async def admin_delete_comment(
    comment_id: int,
    keep_record: bool = Query(True, description="True为保留记录(软删除), False为彻底删除"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if not comment.is_deleted and comment.status == 'approved':
        article = db.query(Article).filter(Article.id == comment.article_id).first()
        if article and article.comment_count and article.comment_count > 0:
            article.comment_count -= 1
    
    if keep_record:
        comment.is_deleted = True
        comment.deleted_by = 'admin'
        comment.content = "此评论已被管理员删除"
        db.commit()
        return {"message": "Comment soft deleted successfully", "type": "soft"}
    else:
        db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment_id).delete()
        db.delete(comment)
        db.commit()
        return {"message": "Comment permanently deleted successfully", "type": "permanent"}


class BatchDeleteRequest(BaseModel):
    comment_ids: List[int]
    permanent: bool = False


@router.post("/admin/batch-delete")
async def batch_delete_comments(
    delete_data: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    comments = db.query(Comment).filter(Comment.id.in_(delete_data.comment_ids)).all()
    
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")
    
    article_comment_changes = {}
    
    for comment in comments:
        if not comment.is_deleted and comment.status == 'approved':
            if comment.article_id not in article_comment_changes:
                article_comment_changes[comment.article_id] = 0
            article_comment_changes[comment.article_id] += 1
    
    deleted_count = 0
    if delete_data.permanent:
        for comment in comments:
            db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment.id).delete()
            db.delete(comment)
            deleted_count += 1
    else:
        for comment in comments:
            comment.is_deleted = True
            comment.deleted_by = 'admin'
            comment.content = "此评论已被管理员删除"
            deleted_count += 1
    
    for article_id, count in article_comment_changes.items():
        article = db.query(Article).filter(Article.id == article_id).first()
        if article and article.comment_count:
            article.comment_count = max(0, article.comment_count - count)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} comments",
        "deleted_count": deleted_count,
        "type": "permanent" if delete_data.permanent else "soft"
    }


@router.post("/admin/sync-comment-counts")
async def sync_comment_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from sqlalchemy import func
    
    articles = db.query(Article).all()
    updated_count = 0
    
    for article in articles:
        actual_count = db.query(func.count(Comment.id)).filter(
            Comment.article_id == article.id,
            Comment.status == 'approved',
            Comment.is_deleted == False
        ).scalar()
        
        if article.comment_count != actual_count:
            article.comment_count = actual_count
            updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully synced comment counts",
        "updated_articles": updated_count,
        "total_articles": len(articles)
    }
