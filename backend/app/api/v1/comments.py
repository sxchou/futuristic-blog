from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import Comment, Article, User, NotificationSettings, CommentAuditLog, UserProfile, AvatarType
from app.schemas import (
    CommentCreate, CommentResponse, CommentAuditRequest, 
    BatchAuditRequest, CommentAuditLogResponse, AdminCommentResponse,
    PaginatedResponse, ArticleListItem, CategoryResponse, TagResponse, UserResponse
)
from app.utils import get_current_user
from app.utils.permissions import require_permission
from app.services.permission_service import PermissionService
from app.services.email_service import EmailService
from app.utils.timezone import get_db_now

COMMENT_RATE_LIMIT_PER_MINUTE = 3
from app.services.log_service import LogService

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
            elif comment.reply_to_user_name:
                reply_to_user_name = comment.reply_to_user_name
            else:
                reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first()
                reply_to_user_name = reply_to_user.username if reply_to_user else None
            
            if comment.reply_to_user_id not in user_avatar_cache:
                user_avatar_cache[comment.reply_to_user_id] = get_user_avatar_info(db, comment.reply_to_user_id)
            reply_to_user_avatar = user_avatar_cache[comment.reply_to_user_id]
        elif comment.reply_to_user_name:
            reply_to_user_name = comment.reply_to_user_name
        
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


def send_comment_notification_bg(article_title: str, article_slug: str, commenter_name: str, comment_content: str, author_email: str, author_name: str, comment_id: int = None):
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
                author_email=author_email,
                author_name=author_name,
                comment_id=comment_id
            )
    except Exception as e:
        print(f"Failed to send comment notification: {e}")
    finally:
        db.close()


def send_pending_comment_notification_bg(article_title: str, article_slug: str, commenter_name: str, comment_content: str, author_email: str, author_name: str, comment_id: int = None):
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


def send_comment_rejected_notification_bg(recipient_email: str, recipient_name: str, article_title: str, comment_content: str, reason: str = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        EmailService.send_comment_rejected_notification_db(
            db=db,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            article_title=article_title,
            comment_content=comment_content,
            reason=reason
        )
    except Exception as e:
        print(f"Failed to send comment rejected notification: {e}")
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


@router.get("/article/{article_id}")
async def get_article_comments(
    article_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(5, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    root_total = db.query(func.count(Comment.id)).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved',
        Comment.parent_id == None
    ).scalar()
    
    root_comments = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.reply_to_user)
    ).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved',
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    root_ids = [c.id for c in root_comments]
    
    all_non_root = []
    if root_ids:
        all_non_root = db.query(Comment).options(
            joinedload(Comment.user),
            joinedload(Comment.reply_to_user)
        ).filter(
            Comment.article_id == article_id,
            Comment.status == 'approved',
            Comment.parent_id != None
        ).order_by(Comment.created_at.asc()).all()
    
    tree = build_comment_tree(list(root_comments) + all_non_root, db)
    
    def count_all_descendants(comment_data: dict) -> int:
        count = len(comment_data.get('replies', []))
        for reply in comment_data.get('replies', []):
            count += count_all_descendants(reply)
        return count
    
    def limit_direct_replies(comment_data: dict, limit: int) -> dict:
        direct_replies = comment_data.get('replies', [])
        if len(direct_replies) <= limit:
            return comment_data
        limited = direct_replies[:limit]
        remaining_ids = set(r['id'] for r in direct_replies[limit:])
        
        def keep_or_trim(node: dict) -> dict:
            node_replies = node.get('replies', [])
            if node['id'] in remaining_ids:
                return { **node, 'replies': [] }
            trimmed_replies = [keep_or_trim(r) for r in node_replies]
            return { **node, 'replies': trimmed_replies }
        
        trimmed_children = [keep_or_trim(r) for r in limited]
        return { **comment_data, 'replies': trimmed_children }
    
    total_all = db.query(func.count(Comment.id)).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved'
    ).scalar() or 0
    result = []
    for rc in root_comments:
        comment_data = next((c for c in tree if c['id'] == rc.id), None)
        if comment_data:
            total_descendants = count_all_descendants(comment_data)
            limited_data = limit_direct_replies(comment_data, 0)
            limited_data['reply_count'] = total_descendants
            result.append(limited_data)
    
    total_pages = max(1, (root_total + page_size - 1) // page_size)
    
    return {
        'items': result,
        'total': root_total,
        'total_all': total_all,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@router.get("/article/{article_id}/replies/{comment_id}")
async def get_comment_replies(
    article_id: int,
    comment_id: int,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(0, ge=0, description="数量限制，0表示不限制"),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    parent = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.article_id == article_id,
        Comment.status == 'approved'
    ).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    all_direct = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.reply_to_user)
    ).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved',
        Comment.parent_id == comment_id
    ).order_by(Comment.created_at.asc()).all()
    
    total_direct = len(all_direct)
    
    if offset >= total_direct:
        return {
            'items': [],
            'total': total_direct,
            'offset': offset,
            'has_more': False
        }
    
    if limit > 0:
        page_direct = all_direct[offset:offset + limit]
    else:
        page_direct = all_direct[offset:]
    
    all_descendant_ids = set(r.id for r in page_direct)
    queue = list(page_direct)
    while queue:
        current = queue.pop(0)
        children = db.query(Comment).filter(
            Comment.article_id == article_id,
            Comment.status == 'approved',
            Comment.parent_id == current.id
        ).all()
        for child in children:
            if child.id not in all_descendant_ids:
                all_descendant_ids.add(child.id)
                queue.append(child)
    
    all_related = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.reply_to_user)
    ).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved',
        Comment.id.in_(all_descendant_ids | {comment_id})
    ).order_by(Comment.created_at.asc()).all()
    
    tree = build_comment_tree(all_related, db)
    
    target_node = next((n for n in tree if n.get('id') == comment_id), None)
    page_items = target_node.get('replies', []) if target_node else []
    
    return {
        'items': page_items,
        'total': total_direct,
        'offset': offset,
        'has_more': offset + len(page_items) < total_direct
    }


@router.get("/article/{article_id}/locate/{comment_id}")
async def locate_comment_page(
    article_id: int,
    comment_id: int,
    page_size: int = Query(5, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    target_comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.article_id == article_id,
        Comment.status == 'approved'
    ).first()
    
    if not target_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    def find_root_id(cid: int) -> int:
        current_id = cid
        visited = set()
        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            c = db.query(Comment.parent_id).filter(Comment.id == current_id).first()
            if c and c[0] is not None:
                current_id = c[0]
            else:
                return current_id
        return cid
    
    root_id = find_root_id(target_comment.id) if target_comment.parent_id else target_comment.id
    
    root_ids_ordered = db.query(Comment.id).filter(
        Comment.article_id == article_id,
        Comment.status == 'approved',
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()
    
    root_ids_list = [r[0] for r in root_ids_ordered]
    
    try:
        index = root_ids_list.index(root_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Root comment not found")
    
    page = (index // page_size) + 1
    
    return {
        'page': page,
        'root_comment_id': root_id,
        'is_reply': target_comment.parent_id is not None
    }


@router.post("", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    one_minute_ago = get_db_now() - timedelta(minutes=1)
    recent_count = db.query(func.count(Comment.id)).filter(
        Comment.user_id == current_user.id,
        Comment.created_at >= one_minute_ago
    ).scalar()
    
    if recent_count >= COMMENT_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"评论过于频繁，请稍后再试（每分钟最多{COMMENT_RATE_LIMIT_PER_MINUTE}条）"
        )
    
    article = db.query(Article).filter(Article.id == comment_data.article_id, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    notification_settings = db.query(NotificationSettings).first()
    require_audit = notification_settings.require_comment_audit if notification_settings else False
    
    parent_comment = None
    reply_to_user_id = None
    reply_to_user_name = None
    
    if comment_data.parent_id:
        parent_comment = db.query(Comment).options(
            joinedload(Comment.user)
        ).filter(Comment.id == comment_data.parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        
        if parent_comment.user_id:
            reply_to_user_id = parent_comment.user_id
            reply_to_user_name = parent_comment.user.username if parent_comment.user else parent_comment.author_name
    
    initial_status = 'pending' if require_audit else 'approved'
    
    new_comment = Comment(
        content=comment_data.content,
        article_id=comment_data.article_id,
        parent_id=comment_data.parent_id,
        user_id=current_user.id,
        author_name=current_user.username,
        author_email=current_user.email,
        status=initial_status,
        reply_to_user_id=reply_to_user_id,
        reply_to_user_name=reply_to_user_name
    )
    
    db.add(new_comment)
    
    if initial_status == 'approved':
        article.comment_count = (article.comment_count or 0) + 1
    
    try:
        db.commit()
        db.refresh(new_comment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="数据保存失败，请检查输入内容")
    
    article_author = db.query(User).filter(User.id == article.author_id).first() if article.author_id else None
    author_email = article_author.email if article_author else None
    author_name = article_author.username if article_author else (article.author_name or '已注销用户')
    
    if not author_email:
        author_email = EmailService.get_admin_real_email(db)
        if article_author and not article_author.email:
            author_name = f"已注销用户"
    
    if initial_status == 'approved':
        background_tasks.add_task(
            send_comment_notification_bg,
            article.title,
            article.slug,
            current_user.username,
            comment_data.content,
            author_email,
            author_name,
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
            author_email,
            author_name,
            new_comment.id
        )
    
    reply_to_user_name = None
    reply_to_user_avatar = {'avatar_type': None, 'avatar_url': None, 'avatar_gradient': None}
    if new_comment.reply_to_user_id:
        reply_to_user = db.query(User).filter(User.id == new_comment.reply_to_user_id).first()
        reply_to_user_name = reply_to_user.username if reply_to_user else new_comment.reply_to_user_name
        reply_to_user_avatar = get_user_avatar_info(db, new_comment.reply_to_user_id)
    elif new_comment.reply_to_user_name:
        reply_to_user_name = new_comment.reply_to_user_name
    
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
        article = db.query(Article).options(
            joinedload(Article.category),
            selectinload(Article.tags),
            joinedload(Article.author)
        ).filter(Article.id == result.article_id).first()
        if article:
            articles.append(ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                summary=article.summary,
                cover_image=article.cover_image,
                view_count=article.view_count,
                like_count=article.like_count,
                bookmark_count=article.bookmark_count or 0,
                comment_count=article.comment_count,
                is_published=article.is_published,
                is_featured=article.is_featured,
                is_pinned=article.is_pinned,
                reading_time=article.reading_time,
                created_at=article.created_at,
                published_at=article.published_at,
                category=CategoryResponse.model_validate(article.category) if article.category else None,
                tags=[TagResponse.model_validate(tag) for tag in article.tags],
                author=UserResponse.model_validate(article.author) if article.author else None,
                author_name=article.author_name,
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

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="此评论已被删除，无法再次删除")

    is_owner = comment.user_id == current_user.id
    has_permission = PermissionService.has_permission_strict(db, current_user.id, "comment.delete")
    
    if not is_owner and not has_permission:
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
    current_user: User = Depends(require_permission("comment.view"))
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.audit"))
):
    comment = db.query(Comment).options(
        joinedload(Comment.article),
        joinedload(Comment.user)
    ).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="此评论已被删除，无法更新状态")

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
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="audit",
        module="comment",
        description=f"审核评论: {audit_data.status} (ID: {comment_id})",
        target_type="comment",
        target_id=comment_id,
        request=request
    )
    
    if old_status != audit_data.status and comment.author_email:
        if audit_data.status == 'approved':
            background_tasks.add_task(
                send_comment_approved_notification_bg,
                comment.author_email,
                comment.author_name,
                comment.article.title if comment.article else '',
                comment.article.slug if comment.article else '',
                comment.content,
                comment.id
            )
        elif audit_data.status == 'rejected':
            background_tasks.add_task(
                send_comment_rejected_notification_bg,
                comment.author_email,
                comment.author_name,
                comment.article.title if comment.article else '',
                comment.content,
                audit_data.reason
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.audit"))
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
        
        if old_status != audit_data.status and comment.author_email:
            if audit_data.status == 'approved':
                background_tasks.add_task(
                    send_comment_approved_notification_bg,
                    comment.author_email,
                    comment.author_name,
                    comment.article.title if comment.article else '',
                    comment.article.slug if comment.article else '',
                    comment.content,
                    comment.id
                )
            elif audit_data.status == 'rejected':
                background_tasks.add_task(
                    send_comment_rejected_notification_bg,
                    comment.author_email,
                    comment.author_name,
                    comment.article.title if comment.article else '',
                    comment.content,
                    audit_data.reason
                )
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="batch_audit",
        module="comment",
        description=f"批量审核评论: {audit_data.status} ({updated_count}条)",
        target_type="comment",
        request=request
    )
    
    return {
        "message": f"Successfully updated {updated_count} comments",
        "updated_count": updated_count
    }


@router.get("/admin/{comment_id}/logs", response_model=List[CommentAuditLogResponse])
async def get_comment_audit_logs(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.view"))
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
    request: Request,
    keep_record: bool = Query(True, description="True为保留记录(软删除), False为彻底删除"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.delete"))
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.is_deleted and keep_record:
        raise HTTPException(status_code=400, detail="此评论已被删除，无法再次软删除")

    if not comment.is_deleted and comment.status == 'approved':
        article = db.query(Article).filter(Article.id == comment.article_id).first()
        if article and article.comment_count and article.comment_count > 0:
            article.comment_count -= 1
    
    if keep_record:
        comment.is_deleted = True
        comment.deleted_by = 'admin'
        comment.content = "此评论已被管理员删除"
        db.commit()
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="soft_delete",
            module="comment",
            description=f"软删除评论 (ID: {comment_id})",
            target_type="comment",
            target_id=comment_id,
            request=request
        )
        
        return {"message": "Comment soft deleted successfully", "type": "soft"}
    else:
        child_comments = db.query(Comment).filter(Comment.parent_id == comment_id).all()
        for child in child_comments:
            if not child.reply_to_user_name and comment.author_name:
                child.reply_to_user_name = comment.author_name
            child.parent_id = None

        db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment_id).delete()
        db.delete(comment)
        db.commit()
        
        LogService.log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="permanent_delete",
            module="comment",
            description=f"永久删除评论 (ID: {comment_id})",
            target_type="comment",
            target_id=comment_id,
            request=request
        )
        
        return {"message": "Comment permanently deleted successfully", "type": "permanent"}


class BatchDeleteRequest(BaseModel):
    comment_ids: List[int]
    permanent: bool = False


@router.post("/admin/batch-delete")
async def batch_delete_comments(
    delete_data: BatchDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.delete"))
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
    skipped_count = 0
    if delete_data.permanent:
        for comment in comments:
            child_comments = db.query(Comment).filter(Comment.parent_id == comment.id).all()
            for child in child_comments:
                if not child.reply_to_user_name and comment.author_name:
                    child.reply_to_user_name = comment.author_name
                child.parent_id = None

            db.query(CommentAuditLog).filter(CommentAuditLog.comment_id == comment.id).delete()
            db.delete(comment)
            deleted_count += 1
    else:
        for comment in comments:
            if comment.is_deleted:
                skipped_count += 1
                continue
            comment.is_deleted = True
            comment.deleted_by = 'admin'
            comment.content = "此评论已被管理员删除"
            deleted_count += 1
    
    for article_id, count in article_comment_changes.items():
        article = db.query(Article).filter(Article.id == article_id).first()
        if article and article.comment_count:
            article.comment_count = max(0, article.comment_count - count)
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="batch_delete",
        module="comment",
        description=f"批量删除评论: {'永久删除' if delete_data.permanent else '软删除'} ({deleted_count}条, 跳过{skipped_count}条已删除)",
        target_type="comment",
        request=request
    )

    return {
        "message": f"Successfully deleted {deleted_count} comments" + (f", skipped {skipped_count} already deleted" if skipped_count > 0 else ""),
        "deleted_count": deleted_count,
        "skipped_count": skipped_count,
        "type": "permanent" if delete_data.permanent else "soft"
    }


@router.post("/admin/sync-comment-counts")
async def sync_comment_counts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("comment.audit"))
):
    from sqlalchemy import func
    
    articles = db.query(Article).all()
    updated_count = 0
    
    for article in articles:
        actual_count = db.query(func.count(Comment.id)).filter(
            Comment.article_id == article.id,
            Comment.status == 'approved'
        ).scalar()
        
        if article.comment_count != actual_count:
            article.comment_count = actual_count
            updated_count += 1
    
    db.commit()
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="sync_counts",
        module="comment",
        description=f"同步评论计数 (更新{updated_count}篇文章)",
        request=request
    )
    
    return {
        "message": f"Successfully synced comment counts",
        "updated_articles": updated_count,
        "total_articles": len(articles)
    }
