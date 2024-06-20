from os import getenv
from minio import Minio

class MinIO:
    def __init__(self):
        print("INITIALIZING MINIO")
        self.minio_client = Minio(
            endpoint = f"minio:{getenv('MINIO_PORT')}",
            access_key = getenv('MINIO_ACCESS_KEY'),
            secret_key = getenv('MINIO_SECRET_KEY'),
            secure = False
        )
        self.bucket_name = "test"


    def upload_file(
        self,
        object_name: str,
        file_path: str,
        content_type: str # audio/mpeg
        ):
        print("UPLOADING OBJECT")
        self.minio_client.fput_object(
            self.bucket_name, 
            object_name = object_name, 
            file_path = file_path, 
            content_type = content_type
            )    
            
            
    def download_file(
        self,
        object_name: str,
        file_path: str,
        ):
        print("UPLOADING OBJECT")
        self.minio_client.fget_object(
            self.bucket_name,
            object_name = object_name, 
            file_path = file_path
            )