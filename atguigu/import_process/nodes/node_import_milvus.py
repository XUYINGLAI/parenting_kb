"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import json

from pymilvus import DataType

from atguigu.config.config import MilvusConfig
# atguigu/import_process/nodes/node_import_milvus.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger
from atguigu.tool.milvus_client_tool import get_milvus_client


class NodeImportMilvus(NodeBase):
    """
    导入向量库节点：数据持久化
    """

    name = "node_import_milvus"

    def process(self, state: ImportGraphState):
        chunks = state["chunks"]
        if not chunks:
            logger.error("没有拿到chunks数据")
            raise ValueError("没有拿到chunks数据")
        file_title=chunks[0]["file_title"]

        milvus_client = get_milvus_client()
        if not milvus_client.has_collection(MilvusConfig.chunks_collection):
            schema = milvus_client.create_schema(auto_id=True)
            schema.add_field(
                field_name="id",
                datatype=DataType.INT64,
                is_primary=True,
            ).add_field(
                field_name="title",
                datatype=DataType.VARCHAR,
                max_length=100,
            ).add_field(
                field_name="file_title",
                datatype=DataType.VARCHAR,
                max_length=100,
            ).add_field(
                field_name="content",
                datatype=DataType.VARCHAR,
                max_length=3000,
            ).add_field(
                field_name="part",
                datatype=DataType.INT64
            ).add_field(
                field_name="item_name",
                datatype=DataType.VARCHAR,
                max_length=100,
            ).add_field(
                field_name="dense_vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=1024,
            ).add_field(
                field_name="sparse_vector",
                datatype=DataType.SPARSE_FLOAT_VECTOR,
            )

            index_params = milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_vector_index",
                index_type="IVF_FLAT",
                metric_type="COSINE",
                params={"nlist": 128,"nprobe": 10}
            )
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_vector_index",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                # 使用默认值优化
            )
            milvus_client.create_collection(
                collection_name=MilvusConfig.chunks_collection,
                schema=schema,
                index_params=index_params,
            )

        # todo 导入数据
        # 幂等性删除文件相同的chunk

        milvus_client.load_collection(collection_name=MilvusConfig.chunks_collection)
        file_title=file_title.replace("\\","\\\\").replace("\'","\\'").replace('\"','\\"')
        filter=f"file_title=='{file_title}'"
        milvus_client.delete(
            collection_name=MilvusConfig.chunks_collection,
            filter=filter,
        )
        # 添加chunk到milvus
        res=milvus_client.insert(
            collection_name=MilvusConfig.chunks_collection,
            data=chunks,
        )
        # print(res) # 输出字典，包含插入数据的条数和 每条的id

        # 把id回填到chunks
        for chunk in chunks:
            chunk["id"]=res.get("ids").pop(0)  # 也可以用enumerate()

        return {
            "chunks":chunks,
        }


if __name__ == '__main__':
    node = NodeImportMilvus()
    with open(r"D:\output\hak180产品安全手册\chunks_embedding.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    init_state = {
        "chunks": data,
    }

    result = node(init_state)
    # logger.info(json_format(result))
