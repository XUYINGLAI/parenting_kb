"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import json

# atguigu/import_process/nodes/node_bge_embedding.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.get_bge_embeddings import get_bge_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger


class NodeBGEEmbedding(NodeBase):
    """
    混合向量化节点：使用 BGE-M3 模型将文本转换为向量
    """

    name = "node_bge_embedding"

    def process(self, state: ImportGraphState):
        # todo 从state当中获得chunks
        chunks=state.get("chunks")
        if not chunks:
            logger.error("没有获取到chunks数据，无法进行向量化")
            raise ValueError("没有获取到chunks数据，无法进行向量化")
        # todo 对chunks向量化   将所有字符串组成列表，一次性传给 BGE-M3 模型进行向量化。
        # get_bge_embedding([f"{item.get("item_name")}\n{item.get("content")}" for item in chunks])
        # 手动实现批处理
        for i in range(0,len(chunks),3):
            chunk_k_list=chunks[i:i+3]
            # 拿到拼接后的字符串列表
            chunk_k_str_list=[f"{item.get("item_name")}\n{item.get("content")}" for item in chunk_k_list]
            embeddings=get_bge_embedding(chunk_k_str_list)
            # 向量化结束后，把每个chunk得到的两个向量再回填的chunks
            for idx,chunk in enumerate(chunk_k_list):
                chunk["dense_vector"]=embeddings.get("dense")[idx]
                chunk["sparse_vector"]=embeddings.get("sparse")[idx]


        #
        # with open(r"D:\output\hak180产品安全手册\chunks_embedding.json","w",encoding="utf-8") as f:
        #     f.write(json_format(chunks))


        return {
            "chunks":chunks, # 浅拷贝
        }



if __name__ == '__main__':
    node=NodeBGEEmbedding()
    with open(r"D:\output\hak180产品安全手册\chunks_item_name.json","r",encoding="utf-8") as f:
        data=json.load(f)
    init_state={
        "chunks":data,# 拿到列表

    }
    result=node(init_state)
    logger.info(json_format(result))