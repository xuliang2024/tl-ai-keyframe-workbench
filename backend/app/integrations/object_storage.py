from functools import lru_cache
from urllib.parse import quote

from app.core.config import settings


class ObjectStorageError(RuntimeError):
    pass


class ObjectStorageClient:
    def __init__(
        self,
        *,
        provider: str,
        bucket: str,
        region: str,
        endpoint: str,
        public_base_url: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> None:
        self.provider = provider
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.public_base_url = public_base_url.rstrip("/")
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key

    def public_url(self, object_key: str) -> str:
        encoded_key = quote(object_key.lstrip("/"), safe="/")
        return f"{self.public_base_url}/{encoded_key}"

    def generate_presigned_put_url(self, object_key: str, expires_in: int) -> str:
        if self.provider != "tos":
            raise ObjectStorageError("Only TOS presigned uploads are supported")
        client = self._tos_client()
        return client.generate_presigned_url(
            Method="PUT",
            Bucket=self.bucket,
            Key=object_key,
            ExpiresIn=expires_in,
        )

    def upload_bytes(self, object_key: str, data: bytes, content_type: str) -> str:
        if self.provider != "tos":
            raise ObjectStorageError("Only TOS uploads are supported")

        client = self._tos_client()
        client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        return self.public_url(object_key)

    def _tos_client(self):
        if not self.bucket or not self.region or not self.endpoint:
            raise ObjectStorageError("TOS bucket, region and endpoint must be configured")
        if not self.access_key_id or not self.secret_access_key:
            raise ObjectStorageError("TOS access key and secret key must be configured")

        try:
            import tos
        except ImportError as exc:
            raise ObjectStorageError("The tos package is required for TOS uploads") from exc

        return tos.TosClient(
            tos.Auth(self.access_key_id, self.secret_access_key, self.region),
            self.endpoint,
        )


@lru_cache
def get_object_storage_client() -> ObjectStorageClient:
    return ObjectStorageClient(
        provider=settings.storage_provider,
        bucket=settings.storage_bucket,
        region=settings.storage_region,
        endpoint=settings.storage_endpoint,
        public_base_url=settings.storage_public_base_url,
        access_key_id=settings.tos_access_key_id,
        secret_access_key=settings.tos_secret_access_key,
    )
