from supabase import create_client, Client
from typing import Optional, BinaryIO
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    def __init__(self):
        self.client: Optional[Client] = None
        if settings.USE_SUPABASE_STORAGE and settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase Storage Service initialized")
        else:
            logger.info("Using local file storage")

    def is_enabled(self) -> bool:
        return self.client is not None

    async def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        try:
            file_content = file_data.read()
            
            storage_url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_BUCKET}/{key}"
            
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "x-upsert": "true"
            }
            
            files = {
                "file": (key, file_content, content_type or "application/octet-stream")
            }
            data = {
                "cacheControl": "31536000"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    storage_url,
                    headers=headers,
                    files=files,
                    data=data
                )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to upload file to Supabase: {response.status_code} - {response.text}")
                return None

            public_url = self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(key)
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to Supabase: {e}")
            return None

    async def delete_file(self, key: str) -> bool:
        if not self.is_enabled():
            return False

        try:
            response = self.client.storage.from_(settings.SUPABASE_BUCKET).remove([key])
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Supabase: {e}")
            return False

    async def get_file_url(self, key: str) -> Optional[str]:
        if not self.is_enabled():
            return None

        try:
            public_url = self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(key)
            return public_url
        except Exception as e:
            logger.error(f"Failed to get file URL: {e}")
            return None

    async def file_exists(self, key: str) -> bool:
        if not self.is_enabled():
            return False

        try:
            response = self.client.storage.from_(settings.SUPABASE_BUCKET).list(path=key)
            return len(response) > 0
        except Exception:
            return False


supabase_storage = SupabaseStorageService()
