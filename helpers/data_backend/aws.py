import boto3
import fnmatch, logging
from pathlib import PosixPath
from helpers.data_backend.base import BaseDataBackend

boto_logger = logging.getLogger('botocore.hooks')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.auth')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.httpsession')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.parsers')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.retryhandler')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.loaders')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.regions')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.utils')
boto_logger.setLevel('WARNING')
boto_logger = logging.getLogger('botocore.client')
boto_logger.setLevel('WARNING')

class S3DataBackend(BaseDataBackend):
    def __init__(
        self,
        bucket_name,
        region_name="us-east-1",
        endpoint_url: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ):
        self.bucket_name = bucket_name
        # AWS buckets might use a region.
        extra_args = {
            "region_name": region_name,
        }
        # If using an endpoint_url, we do not use the region.
        if endpoint_url:
            extra_args = {
                "endpoint_url": endpoint_url,
            }
        self.client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            **extra_args
        )

    def exists(self, s3_key) -> bool:
        """Determine whether a file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=self._convert_path_to_key(str(s3_key)))
            return True
        except:
            return False

    def read(self, s3_key):
        """Retrieve and return the content of the file from S3."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=self._convert_path_to_key(str(s3_key)))
        return response["Body"].read()
    
    def open_file(self, s3_key, mode):
        """Open the file in the specified mode."""
        return self.read(s3_key)

    def write(self, s3_key, data):
        """Upload data to the specified S3 key."""
        self.client.put_object(Body=data, Bucket=self.bucket_name, Key=self._convert_path_to_key(str(s3_key)))

    def delete(self, s3_key):
        """Delete the specified file from S3."""
        self.client.delete_object(Bucket=self.bucket_name, Key=self._convert_path_to_key(str(s3_key)))

    def list_by_prefix(self, prefix=""):
        """List all files under a specific path (prefix) in the S3 bucket."""
        response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        return [item["Key"] for item in response.get("Contents", [])]

    def list_files(self, str_pattern: str, instance_data_root=None):
        files = self.list_by_prefix()  # List all files
        return [file for file in files if fnmatch.fnmatch(file, str_pattern)]

    def _convert_path_to_key(self, path: str) -> str:
        """
        Turn a /path/to/img.png into img.png

        Args:
            path (str): Full path, or just the base name.

        Returns:
            str: extracted basename, or input filename if already stripped.
        """
        return path.split("/")[-1]

    def read_image(self, s3_key):
        from PIL import Image
        from io import BytesIO
        return Image.open(BytesIO(self.read(s3_key)))

    def create_directory(self, directory_path):
        # Since S3 doesn't have a traditional directory structure, this is just a pass-through
        pass

    def torch_load(self, s3_key):
        import torch
        from io import BytesIO
        return torch.load(BytesIO(self.read(s3_key)))

    def torch_save(self, data, s3_key):
        import torch
        from io import BytesIO
        buffer = BytesIO()
        torch.save(data, buffer)
        self.write(s3_key, buffer.getvalue())