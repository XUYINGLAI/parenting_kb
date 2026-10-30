# atguigu/query_process/nodes/node_search_embedding_hyde.py
from langchain.chat_models import init_chat_model

from atguigu.config.config import LLMConfig, MilvusConfig
from atguigu.config.prompt import HYDE_PROMPT
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.get_bge_embeddings import get_bge_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger
from atguigu.tool.milvus_client_tool import get_search_reqs, hybrid_search


class NodeSearchEmbeddingHyde(NodeBase):
    """
    节点功能：HyDE (Hypothetical Document Embedding)
    先让 LLM 生成假设性答案，再对答案进行向量检索，提高召回率。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_search_embedding_hyde"

    def process(self, state: QueryGraphState):
        """
        节点逻辑
        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """
        # TODO
        logger.info(f"【{self.name}】节点逻辑")
        rewritten_query=state.get("rewritten_query")
        item_names=state.get("item_names")

        # 把重写的问题给大模型，生成假设性答案
        llm=init_chat_model(
            model=LLMConfig.llm_default_model,
            model_provider="openai",
            base_url=LLMConfig.openai_api_base,
            api_key=LLMConfig.openai_api_key,
            temperature=LLMConfig.llm_default_temperature,
        )
        messages=[
            {"role":"user","content":HYDE_PROMPT.format(rewritten_query=rewritten_query)},
        ]
        res=llm.invoke(messages)
        hyde_answer=res.content
        print(hyde_answer)
        # print(json_format(res))

        embeddings = get_bge_embedding([rewritten_query+"\n"+hyde_answer])
        dense_data = embeddings.get("dense")[0]
        sparse_data = embeddings.get("sparse")[0]

        # 混合检索
        item_names = [item_name.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')
                      for item_name in item_names]
        expr = f"item_name in {item_names}"
        reqs = get_search_reqs(  # 准备查询条件。
            dense_data=[dense_data],
            sparse_data=[sparse_data],
            dense_anns_field="dense_vector",  # Milvus 中要搜索的稠密向量字段名
            sparse_anns_field="sparse_vector",  # Milvus 中要搜索的稀疏向量字段名

            expr=expr
        )
        res = hybrid_search(
            collection_name=MilvusConfig.chunks_collection,
            reqs=reqs,
            output_fields=["id", "title", "file_title", "content", "part", "item_name"],
            ranker=(0.7, 0.3),
            limit=10
        )
        # print(json_format(res))

        chunks = []
        for item in res[0]:
            chunks.append({
                **item.get("entity"),
                "score": item.get("distance"),
                "source": "local"
            })

        # return state
        return {"hyde_embedding_chunks":chunks}



if __name__ == '__main__':
    init_state={
        "rewritten_query":"关于hak180烫金机如何使用",
        "item_names":["SCHNHAK180烫金机"]
    }
    node_search_embedding = NodeSearchEmbeddingHyde()
    result=node_search_embedding.process(init_state)
    logger.info(json_format(result))