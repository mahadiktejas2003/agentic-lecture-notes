import os, boto3, logging
from botocore.config import Config

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        self.endpoint_url = os.getenv("R2_ENDPOINT_URL")
        self.key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.app_key = os.getenv("R2_SECRET_ACCESS_KEY")
        
        if not all([self.bucket_name, self.endpoint_url, self.key_id, self.app_key]):
            logger.warning("R2 credentials missing. StorageManager disabled.")
            self.s3 = None
            return

        self.s3 = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.app_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

    def upload_file(self, local_path, remote_key):
        if not self.s3: return False
        try:
            self.s3.upload_file(local_path, self.bucket_name, remote_key)
            logger.info(f"Uploaded {local_path} to {remote_key}")
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def download_file(self, remote_key, local_path):
        if not self.s3: return False
        try:
            self.s3.download_file(self.bucket_name, remote_key, local_path)
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def generate_presigned_url(self, key, expiration=900):
        if not self.s3: return None
        try:
            return self.s3.generate_presigned_url('get_object', 
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration)
        except Exception as e:
            logger.error(f"URL generation failed: {e}")
            return None
