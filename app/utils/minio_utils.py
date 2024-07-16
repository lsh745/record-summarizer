from os import getenv
from minio import Minio, notificationconfig, commonconfig


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


    def list_object(
        self,
        prefix: str,
        recursive: bool = True
        ):
        objects = self.minio_client.list_objects(
            bucket_name=self.bucket_name,
            prefix=prefix,
            recursive=recursive
        )
        return objects


    def upload_object(
        self,
        object_name: str,
        file_path: str,
        # content_type: str # audio/mpeg
        ):
        print("UPLOADING OBJECT")
        self.minio_client.fput_object(
            self.bucket_name, 
            object_name = object_name, 
            file_path = file_path, 
            # content_type = content_type
            ) 


    def upload_object_raw(
        self,
        object_name: str,
        data: bytes,
        length: int,
        # content_type: str # audio/mpeg
        ):
        print("UPLOADING RAW OBJECT")
        self.minio_client.put_object(
            self.bucket_name, 
            object_name = object_name, 
            data = data,
            length = length 
            # content_type = content_type
            )    
            
            
    def download_object(
        self,
        object_name: str,
        file_path: str,
        ):
        print("DOWNLOADING OBJECT")
        self.minio_client.fget_object(
            self.bucket_name,
            object_name = object_name, 
            file_path = file_path
            )

    def move_object(
            self, 
            source_bucket: str,
            source_object: str, 
            target_bucket: str,
            target_object: str
        ):
        print("COPYING OBJECT")
        self.minio_client.copy_object(
            target_bucket, 
            target_object, 
            commonconfig.CopySource(
                source_bucket, 
                source_object
            ),
        )
        self.minio_client.remove_object(
            source_bucket, 
            source_object)


    def create_bucket(self, bucket_name: str):
        print("CREATING BUCKET")
        self.minio_client.make_bucket(bucket_name)


    def set_notification(self):
        config = notificationconfig.NotificationConfig(
            queue_config_list=[
                QueueConfig(
                    f"arn:minio:sqs::whisper_api:webhook",
                    ["s3:ObjectCreated:Put"],
                    config_id="1",
                    prefix_filter_rule=PrefixFilterRule("abc"),
                ),
            ],
        )
        client.set_bucket_notification("my-bucket", config)