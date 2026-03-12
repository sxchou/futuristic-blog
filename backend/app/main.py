from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import router as api_router
from app.services.init_data import init_database
from app.services.log_service import LogService
import os
import time

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Futuristic Blog API",
    description="A futuristic personal blog system API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(('/api/docs', '/api/redoc', '/api/openapi.json', '/uploads')):
            return await call_next(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000
        
        if request.url.path.startswith('/api'):
            db = SessionLocal()
            try:
                LogService.log_access(
                    db=db,
                    request=request,
                    response_status=response.status_code,
                    response_time=response_time
                )
            except Exception as e:
                print(f"Failed to log access: {e}")
            finally:
                db.close()
        
        return response


app.add_middleware(AccessLogMiddleware)

app.include_router(api_router, prefix="/api")

uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.on_event("startup")
async def startup_event():
    init_database()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Futuristic Blog API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
