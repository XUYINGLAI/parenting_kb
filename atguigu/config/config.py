"""
@Author:xuyinglai
@Date:2026/10/9
@DESC:
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)# 覆盖写在环境变量里面的配置项

class MineruConfig:
    mineru_token=os.getenv("MINERU_TOKEN")


class LLMConfig:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    vl_model = os.getenv("VL_MODEL")
    llm_default_model = os.getenv("LLM_DEFAULT_MODEL")
    item_model = os.getenv("ITEM_MODEL")
    llm_default_temperature = float(os.getenv("LLM_DEFAULT_TEMPERATURE"))




# todo minio
class MinioConfig:
    # MinIO 服务端点
    minio_endpoint = os.getenv("MINIO_ENDPOINT")

    # 访问密钥
    minio_access_key = os.getenv("MINIO_ACCESS_KEY")
    # 私有密钥
    minio_secret_key = os.getenv("MINIO_SECRET_KEY")
    # 存储桶名称
    minio_bucket_name = os.getenv("MINIO_BUCKET_NAME")
    # 图片上传目录
    minio_img_dir = os.getenv("MINIO_IMG_DIR")

# todo 构建数据向量化，得到向量化的数据
class BGEM3Config:
    bge_m3_path = os.getenv("BGE_M3_PATH")
    bge_device = os.getenv("BGE_DEVICE")
    bge_fp16 = os.getenv("BGE_FP16") in ("True", "true","1")


# todo milvus数据库
class MilvusConfig:
    milvus_url=os.getenv("MILVUS_URL")
    # 知识库切片集合名
    chunks_collection=os.getenv("CHUNKS_COLLECTION")
    # 商品名称集合名
    item_name_collection=os.getenv("ITEM_NAME_COLLECTION") # 主体识别


# todo MongoDB数据库
class MongoConfig:
    mongo_url=os.getenv("MONGO_URL")
    mongo_db_name=os.getenv("MONGO_DB_NAME") # 数据库名

    mongo_host=os.getenv("MONGO_HOST")
    mongo_port=int(os.getenv("MONGO_PORT"))


# todo MCP
class MCPConfig:
    mcp_base_url = os.getenv("MCP_BASE_URL")
    mcp_api_key = os.getenv("MCP_API_KEY")


# todo reranker
class RerankConfig:
    rerank_base_url = os.getenv("RERANK_BASE_URL")
    rerank_api_key = os.getenv("RERANK_API_KEY")
    rerank_model=os.getenv("RERANK_MODEL")





