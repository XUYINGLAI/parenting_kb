"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import json

from langchain.chat_models import init_chat_model
from pymilvus import DataType

from atguigu.config.config import LLMConfig, MilvusConfig
from atguigu.config.prompt import ITEM_NAME_SYSTEM_PROMPT, ITEM_NAME_USER_PROMPT_TEMPLATE
# atguigu/import_process/nodes/node_item_name_recognition.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.get_bge_embeddings import get_bge_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger
from atguigu.tool.milvus_client_tool import get_milvus_client


class NodeItemNameRecognition(NodeBase):
    """
    主体识别节点：主体识别与标签提取
    """

    name = "node_item_name_recognition"

    def process(self, state: ImportGraphState):
        # todo 获得数据
        chunks = state.get("chunks")
        file_title = state.get("file_title")
        if not chunks :
            logger.error("chunks不能为空")
            raise ValueError("chunks不能为空")
        if file_title is None:
            logger.error("file_title不能为空")
            raise ValueError("file_title不能为空")

        # todo 用前面N个chunk拼接起来形成字符串
        chunks_str = ""
        chunk_k_list = chunks[:15]
        MAX_LENGTH=10000
        for idx, chunk in enumerate(chunk_k_list):
            title = chunk.get("title")
            content = chunk.get("content")
            chunk_text = f"[切片：{idx}]\n文件名{file_title}\n标题：{title}\n内容：{content}\n\n"
            chunks_str += chunk_text
            if len(chunks_str) > MAX_LENGTH:
                break
        chunks_str = chunks_str[:MAX_LENGTH]
        # todo 调用大模型，把字符串当作prompt，总结得到‘主体名称’,即商品名
        llm=init_chat_model(
            model=LLMConfig.item_model,
            model_provider="openai",
            api_key=LLMConfig.openai_api_key,
            base_url=LLMConfig.openai_api_base,
            temperature=LLMConfig.llm_default_temperature
        )
        message=[{
            "role":"system","content":ITEM_NAME_SYSTEM_PROMPT
        },{
            "role":"user","content":ITEM_NAME_USER_PROMPT_TEMPLATE.format(file_title=file_title,context=chunks_str)
        },]
        res=llm.invoke(message)
        print(res.content)  # Brother HAK 180 烫金机
        item_name=res.content.replace("\n","").replace("\r","").replace("\t","").replace(" ","")
        if not item_name:
            item_name=file_title
        ############
        milvus_client=get_milvus_client()
        # 集合不存在时才创建，已经存在时保留其中的数据
        if not milvus_client.has_collection(collection_name=MilvusConfig.item_name_collection):
            # 没有表就创建表
            # 创建schema
            schema=milvus_client.create_schema(
                auto_id=True,# 设置的不是某个字段，而是整个 Schema（表结构）的主键 ID 自动生成规则
            )
            schema.add_field(
                field_name="id",
                datatype=DataType.INT64,
                is_primary=True,
            )
            schema.add_field(
                field_name="item_name",
                datatype=DataType.VARCHAR,
                is_unique=True,
                max_length=50,
            )
            schema.add_field(
                field_name="file_title",
                datatype=DataType.VARCHAR,
                max_length=100,
            )
            schema.add_field(
                field_name="dense_vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=1024
            )
            schema.add_field(
                field_name="sparse_vector",
                datatype=DataType.SPARSE_FLOAT_VECTOR,
            )# 现在是把表的结构规定好了，但是没有填入数据

            # 2 创建索引
            index_params=milvus_client.prepare_index_params()

            index_params.add_index(
                field_name="dense_vector",# 给这个字段创建索引
                index_name="dense_vector_index", # 起名字
                index_type="IVF_FLAT",# K_means+暴力
                metric_type="COSINE",
                params={"nlist":128,"nprobe":10}
            )
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_vector_index",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                # params={"inverted_index_algo": "SINDI"}# 可选
            )

            # 创建表
            milvus_client.create_collection(
                collection_name=MilvusConfig.item_name_collection,
                schema=schema,
                index_params=index_params
            )

        # todo 主体名向量化，存储到milvus
        # 1 先幂等性删除
        file_title=file_title.replace("\\","\\\\").replace("\'","\\'").replace('\"','\\"')
        filter=f"file_title == '{file_title}'" # 里面可能有特殊字符/或者',前一行处理一下
        milvus_client.load_collection(collection_name=MilvusConfig.item_name_collection) # 先加载某个表
        milvus_client.delete(
            collection_name=MilvusConfig.item_name_collection,
            filter=filter
        )
        # 2 item_name向量化后加入milvus
        # todo 把识别到的主题名写入每一个chunk
        embeddings=get_bge_embedding([item_name])
        res=milvus_client.insert(
            collection_name=MilvusConfig.item_name_collection,
            data={
                "item_name":item_name,
                "file_title":file_title,
                "dense_vector":embeddings.get("dense")[0],
                "sparse_vector":embeddings.get("sparse")[0],
            }
        )

        for chunk in chunks:# chunks列表在堆中的地址没有变,不过是里面的每个字典数据变了
            chunk["item_name"]=item_name

        # with open(r"D:\output\hak180产品安全手册\chunks_item_name.json", "w", encoding="utf-8") as f:
        #     f.write(json_format(chunks))


        return {
            "chunks":chunks,
            "item_name":item_name,
        }





if __name__ == '__main__':
    node = NodeItemNameRecognition()
    with open(r"D:\output\hak180产品安全手册\chunks.json", "r", encoding="utf-8") as f:
        # chunks=f.read()
        chunks = json.load(f)
    init_state = {
        # "chunks":json.loads(chunks)
        "chunks": chunks,
        "file_title": "hak180产品安全手册"
    }
    result = node(init_state)  # 对象当函数调用
    logger.info(json_format(result))
