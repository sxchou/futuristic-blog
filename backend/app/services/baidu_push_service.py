import httpx
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaiduPushService:
    BAIDU_PUSH_URL = "http://data.zz.baidu.com/urls"
    
    def __init__(self):
        self.site = getattr(settings, 'SITE_URL', 'https://zhouzhouya.top')
        self.token = getattr(settings, 'BAIDU_PUSH_TOKEN', '')
        self.enabled = bool(self.token)
    
    async def push_urls(self, urls: List[str]) -> dict:
        if not self.enabled:
            logger.info("Baidu push is disabled (no token configured)")
            return {"success": 0, "message": "Baidu push disabled"}
        
        if not urls:
            return {"success": 0, "message": "No URLs to push"}
        
        params = {
            "site": self.site,
            "token": self.token
        }
        
        headers = {
            "Content-Type": "text/plain"
        }
        
        body = "\n".join(urls)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.BAIDU_PUSH_URL,
                    params=params,
                    headers=headers,
                    content=body
                )
                
                result = response.json()
                
                if response.status_code == 200:
                    logger.info(f"Baidu push success: {result}")
                    return {
                        "success": result.get("success", 0),
                        "remain": result.get("remain", 0),
                        "not_same_site": result.get("not_same_site", []),
                        "not_valid": result.get("not_valid", [])
                    }
                else:
                    logger.error(f"Baidu push failed: {response.status_code} - {result}")
                    return {
                        "success": 0,
                        "error": result.get("error", "Unknown error"),
                        "message": result.get("message", "Push failed")
                    }
                    
        except httpx.TimeoutException:
            logger.error("Baidu push timeout")
            return {"success": 0, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Baidu push error: {str(e)}")
            return {"success": 0, "error": str(e)}
    
    async def push_article(self, slug: str) -> dict:
        url = f"{self.site}/article/{slug}"
        return await self.push_urls([url])
    
    async def push_articles(self, slugs: List[str]) -> dict:
        urls = [f"{self.site}/article/{slug}" for slug in slugs]
        return await self.push_urls(urls)


baidu_push_service = BaiduPushService()
