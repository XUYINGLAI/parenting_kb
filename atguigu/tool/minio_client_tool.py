"""
@Author:xuyinglai
@Date:2026/10/14
@DESC:
"""
import json

from minio import Minio

from atguigu.config.config import MinioConfig

# 一个项目一个client就行
minio_client=None

def get_minio_client():
    global minio_client
    if minio_client==None:
        minio_client = Minio(
            endpoint=MinioConfig.minio_endpoint,
            access_key=MinioConfig.minio_access_key,
            secret_key=MinioConfig.minio_secret_key,
            secure=False # todo minio 上传文件 flase:使用http协议
        )
        # 创建桶
        if not minio_client.bucket_exists(MinioConfig.minio_bucket_name):
            minio_client.make_bucket(MinioConfig.minio_bucket_name)

        # 对桶设置权限
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{MinioConfig.minio_bucket_name}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{MinioConfig.minio_bucket_name}/*",
                },
            ],
        }
        minio_client.set_bucket_policy(MinioConfig.minio_bucket_name, json.dumps(policy))
    return minio_client
