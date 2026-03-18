import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Profile
from app.schemas import ProfileResponse, ProfileUpdate
from app.utils import get_current_user
from app.services.log_service import LogService
from app.utils.cache import cache

router = APIRouter(prefix="/profile", tags=["Profile"])

PROFILE_CACHE_KEY = "profile:public"
PROFILE_CACHE_TTL = 300


def get_or_create_profile(db: Session) -> Profile:
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile(
            name="Tech Explorer",
            alias="技术探索者",
            slogan="Code for Future, Share for Growth",
            tags=json.dumps(["全栈架构师", "AI 应用探索者", "开源贡献者"], ensure_ascii=False),
            bio="热爱技术，专注于构建高性能、可扩展的应用系统。在前后端开发、AI应用、DevOps等领域有丰富经验。致力于技术分享，推动开源社区发展。",
            tech_stack=json.dumps([
                {"category": "前端", "items": ["Vue 3", "TypeScript", "Vite", "TailwindCSS", "React", "Next.js"]},
                {"category": "后端", "items": ["Python", "FastAPI", "Node.js", "PostgreSQL", "Redis", "Docker"]},
                {"category": "AI/ML", "items": ["PyTorch", "LangChain", "OpenAI API", "Vector DB", "RAG"]},
                {"category": "DevOps", "items": ["Docker", "Kubernetes", "GitHub Actions", "Nginx", "AWS"]}
            ], ensure_ascii=False),
            journey=json.dumps([
                {"period": "2023 - 至今", "company": "Tech Innovation Corp", "position": "高级全栈工程师", "achievements": "主导多个核心产品架构设计，推动团队技术升级，实现系统性能提升 200%"},
                {"period": "2021 - 2023", "company": "Digital Solutions Ltd", "position": "全栈开发工程师", "achievements": "负责电商平台核心模块开发，日活用户突破 10 万，系统稳定性达 99.9%"},
                {"period": "2019 - 2021", "company": "Startup Hub", "position": "前端开发工程师", "achievements": "从零搭建前端技术栈，建立组件库和开发规范，团队效率提升 50%"}
            ], ensure_ascii=False),
            education=json.dumps({
                "period": "2015 - 2019",
                "school": "某知名大学",
                "major": "计算机科学与技术",
                "degree": "本科"
            }, ensure_ascii=False),
            exploration_areas=json.dumps([
                "大前端架构与跨端方案 (Micro-Frontends)",
                "服务端渲染 (SSR) 与静态站点生成 (SSG)",
                "AI Agent 与 RAG 应用开发",
                "高性能 Web API 设计 (GraphQL)",
                "云原生架构与微服务",
                "WebAssembly 与边缘计算"
            ], ensure_ascii=False),
            social_github="https://github.com/techexplorer",
            social_blog="https://futuristic-blog.com",
            social_email="hello@futuristic-blog.com"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        cache.delete(PROFILE_CACHE_KEY)
    return profile


def profile_to_response(profile: Profile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "alias": profile.alias,
        "slogan": profile.slogan,
        "tags": json.loads(profile.tags) if profile.tags else [],
        "avatar": profile.avatar,
        "bio": profile.bio,
        "tech_stack": json.loads(profile.tech_stack) if profile.tech_stack else [],
        "journey": json.loads(profile.journey) if profile.journey else [],
        "education": json.loads(profile.education) if profile.education else None,
        "exploration_areas": json.loads(profile.exploration_areas) if profile.exploration_areas else [],
        "social_github": profile.social_github,
        "social_blog": profile.social_blog,
        "social_email": profile.social_email,
        "updated_at": profile.updated_at
    }


@router.get("", response_model=ProfileResponse)
async def get_profile(db: Session = Depends(get_db)):
    cached = cache.get(PROFILE_CACHE_KEY)
    if cached:
        return cached
    
    profile = get_or_create_profile(db)
    result = profile_to_response(profile)
    cache.set(PROFILE_CACHE_KEY, result, PROFILE_CACHE_TTL)
    return result


@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限修改个人信息")
    
    profile = get_or_create_profile(db)
    
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["tags", "tech_stack", "journey", "education", "exploration_areas"]:
            setattr(profile, field, json.dumps(value, ensure_ascii=False))
        else:
            setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    LogService.log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="更新",
        module="个人资料",
        description="更新个人资料信息",
        target_type="个人资料",
        target_id=profile.id,
        request=request,
        status="success"
    )
    
    return profile_to_response(profile)
