from supabase import create_client, Client
from typing import Optional, BinaryIO
import logging
import asyncio
import boto3
from botocore.config import Config
from app.core.config import settings

logger = logging.getLogger(__name__)


CACHE_POLICIES = {
    "image": "public, max-age=31536000, immutable",
    "avatar": "public, max-age=604800, stale-while-revalidate=2592000",
    "document": "public, max-age=31536000, immutable",
    "audio": "public, max-age=31536000, immutable",
    "video": "public, max-age=31536000, immutable",
    "default": "public, max-age=31536000, immutable",
}


def get_cache_policy(storage_key: str) -> str:
    if storage_key.startswith("avatars/"):
        return CACHE_POLICIES["avatar"]
    if storage_key.startswith("images/"):
        return CACHE_POLICIES["image"]
    if storage_key.startswith("audio/"):
        return CACHE_POLICIES["audio"]
    if storage_key.startswith("videos/"):
        return CACHE_POLICIES["video"]
    if storage_key.startswith("articles/"):
        return CACHE_POLICIES["document"]
    return CACHE_POLICIES["default"]


class SupabaseStorageService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.s3_client = None
        if settings.USE_SUPABASE_STORAGE and settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY:
                project_ref = settings.SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
                s3_endpoint = f"https://{project_ref}.storage.supabase.co/storage/v1/s3"
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=s3_endpoint,
                    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                    config=Config(
                        signature_version='s3v4',
                        s3={'addressing_style': 'path'}
                    ),
                    region_name='us-east-1'
                )
                logger.info(f"Supabase Storage Service initialized with S3 API: {s3_endpoint}")
            else:
                logger.warning("S3 credentials not configured, using SDK upload")
        else:
            logger.info("Using local file storage")

    def is_enabled(self) -> bool:
        return self.client is not None

    def get_upload_method(self) -> str:
        if self.s3_client:
            return "s3"
        return "none"

    async def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        if not self.s3_client:
            logger.error("S3 client not configured. Cache-Control requires S3 API upload. Please set S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY environment variables.")
            return None

        try:
            file_content = file_data.read()
            cache_policy = get_cache_policy(key)

            extra_args = {
                'CacheControl': cache_policy
            }
            if content_type:
                extra_args['ContentType'] = content_type

            logger.info(f"Uploading via S3 API: bucket={settings.SUPABASE_BUCKET}, key={key}, cache={cache_policy}")

            self.s3_client.put_object(
                Bucket=settings.SUPABASE_BUCKET,
                Key=key,
                Body=file_content,
                **extra_args
            )
            logger.info(f"File uploaded via S3 API with cache control: {key}")

            public_url = self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(key)
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to Supabase: {e}", exc_info=True)
            return None

    async def update_cache_control(self, key: str, cache_control: Optional[str] = None) -> bool:
        if not self.s3_client:
            logger.warning("S3 client not available, cannot update cache-control")
            return False

        try:
            if cache_control is None:
                cache_control = get_cache_policy(key)

            head = self.s3_client.head_object(
                Bucket=settings.SUPABASE_BUCKET,
                Key=key
            )

            copy_args = {
                'Bucket': settings.SUPABASE_BUCKET,
                'Key': key,
                'CopySource': {'Bucket': settings.SUPABASE_BUCKET, 'Key': key},
                'CacheControl': cache_control,
                'MetadataDirective': 'REPLACE',
                'ContentType': head.get('ContentType', 'application/octet-stream'),
            }

            self.s3_client.copy_object(**copy_args)
            logger.info(f"Updated cache-control for {key}: {cache_control}")
            return True
        except Exception as e:
            logger.error(f"Failed to update cache-control for {key}: {e}", exc_info=True)
            return False

    async def batch_update_cache_control(self, prefix: Optional[str] = None) -> dict:
        if not self.s3_client:
            logger.warning("S3 client not available, cannot batch update cache-control")
            return {"updated": 0, "failed": 0, "errors": []}

        result = {"updated": 0, "failed": 0, "errors": []}
        try:
            list_kwargs = {'Bucket': settings.SUPABASE_BUCKET, 'MaxKeys': 1000}
            if prefix:
                list_kwargs['Prefix'] = prefix

            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(**list_kwargs):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    try:
                        success = await self.update_cache_control(key)
                        if success:
                            result["updated"] += 1
                        else:
                            result["failed"] += 1
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        result["failed"] += 1
                        result["errors"].append({"key": key, "error": str(e)})

            logger.info(f"Batch update cache-control completed: {result['updated']} updated, {result['failed']} failed")
        except Exception as e:
            logger.error(f"Batch update cache-control failed: {e}", exc_info=True)
            result["errors"].append({"error": str(e)})

        return result

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
