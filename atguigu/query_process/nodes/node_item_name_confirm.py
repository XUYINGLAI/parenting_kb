# atguigu/query_process/nodes/node_item_name_confirm.py

import json

from langchain.chat_models import init_chat_model

from atguigu.config.config import LLMConfig, MilvusConfig
from atguigu.config.prompt import ITEM_NAME_EXTRACT_SYSTEM_PROMPT, ITEM_NAME_EXTRACT_TEMPLATE
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.get_bge_embeddings import get_bge_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger
from atguigu.tool.milvus_client_tool import get_search_reqs, hybrid_search
# from atguigu.tool.milvus_client_tool import get_search_reqs, hybrid_search
from atguigu.tool.mongo_tool import save_chat_message, get_recent_messages, update_history_item_names


class NodeItemNameConfirm(NodeBase):
    """
    节点功能：确认用户问题中的核心商品名称。
    """
    name:str="node_item_name_confirm"
    def process(self, state: QueryGraphState):
        original_query=state.get("original_query")
        session_id = state.get("session_id")
        if original_query is None:
            logger.error(f"原始问题不能为空")
            raise ValueError(f"原始问题不能为空")
        if not session_id:
            logger.error(f"会话ID不能为空")
            raise ValueError(f"会话ID不能为空")

        history_list=get_recent_messages(session_id)
        # 当前的问题已经问了，把这个问题也要保存历史
        message_id=save_chat_message(session_id,"user",original_query)

        # 把历史上的role和text拼接起来，送入LLM
        history_str=""
        for history in history_list:
            role=history["role"]
            text=history["text"]
            history_str+=f"{role}:{text}\n"

        # todo 初始化llm
        llm=init_chat_model(
            model=LLMConfig.llm_default_model,
            model_provider="openai",
            base_url=LLMConfig.openai_api_base,
            api_key=LLMConfig.openai_api_key,
            temperature=LLMConfig.llm_default_temperature,
        )
        messages=[
            {"role":"system","content":ITEM_NAME_EXTRACT_SYSTEM_PROMPT},
            {"role":"user","content":ITEM_NAME_EXTRACT_TEMPLATE.format(history_text=history_str,original_query=original_query)},
        ]
        res=llm.invoke(messages)
        # print(json_format(res))
        res_json=res.content
        res_data=json.loads(res_json)
        # print(res_data,type(res_data))

        item_names=res_data.get("item_names",[]) # llm生成的商品名。后面要用它来找milvus的主体识别的名字 求相似度
        item_names=[item.replace("\n","").replace("\t","").replace(" ","") for item in item_names ]
        rewritten_query=res_data.get("rewritten_query",original_query)

        # todo 向量化llm生成的商品名  相似度
        final_item_names=[]
        answer = "暂时无法匹配到相关育儿主题，请补充孩子的年龄、具体表现或发生场景。" # 默认值
        if item_names:
            # 有llm生成的商品名

            embeddings=get_bge_embedding(item_names) # [[],[]] [{},{}]
            search_item_name_list=[]

            # 注意：embeddings 是 dict（dense/sparse 两个 key），enumerate 它拿到的是 key 名，
            # 必须按 item_names 的下标取向量
            for idx, item_name in enumerate(item_names):
                dense_data=embeddings.get("dense")[idx]
                sparse_data=embeddings.get("sparse")[idx]

                # 混合检索
                reqs=get_search_reqs(
                    dense_data=[dense_data],
                    dense_anns_field="dense_vector",
                    sparse_data=[sparse_data],
                    sparse_anns_field="sparse_vector",
                )
                res=hybrid_search(
                    collection_name=MilvusConfig.item_name_collection,
                    reqs=reqs,
                    ranker=(0.8, 0.2),
                    output_fields=["item_name","file_title" ],
                    limit=10,

                )
                print(json_format(res))
                # print(item_name)
                if not res : # 表中没找到
                    continue
                for search_item_name_dict in res[0]:
                    search_item_name_list.append({
                        "original_item_name": item_name, # llm识别的名字
                        "search_item_name": search_item_name_dict.get("entity").get("item_name"), # milvus表中存在的名字
                        "score": search_item_name_dict.get("distance",0) # 二者的相似度得分
                    }
                    )

            # todo 商品对齐，设置一个阈值，对score筛选
            confirm_item_names=[item.get("search_item_name")
                                for item in search_item_name_list
                                if item.get("score")>=0.75 ]
            option_item_names=[item.get("search_item_name")
                               for item in search_item_name_list
                               if item.get("score")<0.75 and item.get("score")>=0.6]

            if confirm_item_names:
                # 有可以确定的名字
                final_item_names=confirm_item_names
                answer=""
            elif option_item_names:
                # 有多个可选的名字
                final_item_names=option_item_names
                answer = f"你想咨询的是以下哪个育儿主题：{'、'.join(option_item_names)}？请补充说明。"
            else:
                # 全是噪声
                final_item_names=[]
                answer=answer # 默认值
        # todo 记录一下历史记录
        if answer:
            # 保存一下历史
            message_id=save_chat_message(
                session_id=session_id,
                role="assistant",
                text=answer,
            )
        # 回填
        history_list=get_recent_messages(session_id)
        history_ids=[history.get("_id") for history in history_list] #最近的上下文都带上同一个商品主题和重写问题
        update_history_item_names(ids=history_ids,
                                  item_names=final_item_names,
                                  rewritten_query=rewritten_query) # 已经修改数据库的记录



        # 必须返回 state 增量，否则上游拿到 None
        return {
            "message_id": str(message_id),  # ObjectId 不能直接进 state，转成字符串
            "original_query": original_query,
            "answer": answer,
            "item_names": final_item_names,
            "rewritten_query": rewritten_query,
            "history": get_recent_messages(session_id), # 获得最新的数据库
        }

if __name__ == "__main__":

    # 模拟会话历史
    session_id = "test_001"
    # save_chat_message(session_id, "user", "咨询下烫金机。")
    # save_chat_message(session_id, "assistant", "您好。请问是哪个型号")
    # save_chat_message(session_id, "user", "hak180")
    # save_chat_message(session_id, "assistant", "具体有什么问题呢？")

    # 初始化图状态
    init_state = {
        "session_id": "test_001",
        "original_query": "咋用？"
    }

    # 创建节点对象
    node_item_name_confirm = NodeItemNameConfirm()
    # 执行节点的单元测试
    result = node_item_name_confirm(init_state)
    # 将返回的图状态进行json序列化
    logger.info(json_format(result))
