from fastapi import APIRouter
from app.api.v1 import auth, articles, categories, tags, resources, site_config, likes, bookmarks, comments, users, profile, files, email, notifications, logs, dashboard, user_profile, oauth, utils

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "futuristic-blog-backend"}

router.include_router(auth.router)
router.include_router(articles.router)
router.include_router(categories.router)
router.include_router(tags.router)
router.include_router(resources.router)
router.include_router(site_config.router)
router.include_router(likes.router)
router.include_router(bookmarks.router)
router.include_router(comments.router)
router.include_router(users.router)
router.include_router(profile.router)
router.include_router(files.router)
router.include_router(email.router)
router.include_router(notifications.router)
router.include_router(logs.router)
router.include_router(dashboard.router)
router.include_router(user_profile.router)
router.include_router(oauth.router)
router.include_router(utils.router)
