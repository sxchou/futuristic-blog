from supabase import create_client, Client
from typing import Optional, BinaryIO
import logging
import boto3
from botocore.config import Config
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.s3_client = None
        if settings.USE_SUPABASE_STORAGE and settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            project_ref = settings.SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
            s3_endpoint = f"https://{project_ref}.supabase.co/storage/v1/s3"
            self.s3_client = boto3.client(
                's3',
                endpoint_url=s3_endpoint,
                aws_access_key_id=settings.SUPABASE_KEY,
                aws_secret_access_key=settings.SUPABASE_KEY,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1'
            )
            logger.info("Supabase Storage Service initialized with S3 API")
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
            
            metadata = {
                'CacheControl': 'public, max-age=31536000'
            }
            if content_type:
                metadata['ContentType'] = content_type
            
            self.s3_client.put_object(
                Bucket=settings.SUPABASE_BUCKET,
                Key=key,
                Body=file_content,
                **metadata
            )

            public_url = self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(key)
            logger.info(f"File uploaded successfully with cache control: {key}")
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
