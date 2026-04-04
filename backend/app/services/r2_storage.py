import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class R2StorageService:
    def __init__(self):
        self.s3_client = None
        if settings.USE_R2_STORAGE and settings.R2_ACCESS_KEY and settings.R2_SECRET_KEY:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.R2_ENDPOINT_URL,
                aws_access_key_id=settings.R2_ACCESS_KEY,
                aws_secret_access_key=settings.R2_SECRET_KEY,
                region_name='auto'
            )
            logger.info("R2 Storage Service initialized")
        else:
            logger.info("Using local file storage")

    def is_enabled(self) -> bool:
        return self.s3_client is not None

    async def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.s3_client.upload_fileobj(
                file_data,
                settings.R2_BUCKET_NAME,
                key,
                ExtraArgs=extra_args
            )

            if settings.R2_PUBLIC_URL:
                return f"{settings.R2_PUBLIC_URL}/{key}"
            return f"{settings.R2_ENDPOINT_URL}/{settings.R2_BUCKET_NAME}/{key}"

        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            return None

    async def delete_file(self, key: str) -> bool:
        if not self.is_enabled():
            return False

        try:
            self.s3_client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from R2: {e}")
            return False

    async def get_file_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        if not self.is_enabled():
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.R2_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    async def file_exists(self, key: str) -> bool:
        if not self.is_enabled():
            return False

        try:
            self.s3_client.head_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key
            )
            return True
        except ClientError:
            return False


r2_storage = R2StorageService()
