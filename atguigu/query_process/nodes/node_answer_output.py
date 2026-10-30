# atguigu/query_process/nodes/node_answer_output.py
from langchain.chat_models import init_chat_model

from atguigu.config.config import LLMConfig
from atguigu.config.prompt import ANSWER_PROMPT
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.logger import logger
from atguigu.tool.mongo_tool import save_chat_message
from atguigu.tool.task_utils import put_data
import re

class NodeAnswerOutput(NodeBase):
    """
    节点功能: 答案生成
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_answer_output"

    def process(self, state: QueryGraphState):
        """
        节点逻辑
        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """

        # TODO
        logger.info(f"【{self.name}】节点逻辑")
        answer=state.get("answer","")
        task_id=state.get("task_id")
        rechunks=state.get("reranked_docs")
        history=state.get("history")
        item_names=state.get("item_names")
        rewritten_query=state.get("rewritten_query")
        session_id=state.get("session_id")
        if answer:
            # 没有确定的名字
            put_data(task_id,event="final",data={"answer":answer})
        else:
            # chunks教给大模型，生成答案
            context=""
            for idx, chunk in enumerate(rechunks,start=1):
                title=chunk.get("title")
                content=chunk.get("content")
                url=chunk.get("url")
                source=chunk.get("source")
                chunk_str=f"[切片:{idx}\n][标题:{title}]\n[内容:{content}]\n[来源:{source}]\n[连接:{url}]\n\n"
                context += chunk_str

            history_str="\n".join([f"{h.get('role')}:{h.get('text')}" for h in history])

            item_names_str=",".join(item_names)

            question=rewritten_query

  
            answer_prompt=ANSWER_PROMPT.format(context=context,history=history,item_names=item_names,question=question)

            answer_prompt=answer_prompt[:10000]

            llm=init_chat_model(
                model=LLMConfig.llm_default_model,
                model_provider="openai",
                base_url=LLMConfig.openai_api_base,
                api_key=LLMConfig.openai_api_key,
                temperature=LLMConfig.llm_default_temperature,
            )
            messages=[
                {"role":"user","content":answer_prompt}
            ]
            res=llm.stream(input=messages) #生成器
            for chunk in res:
                print(chunk.content)
                put_data(task_id,event="delta",data={"delta":chunk.content})
                answer+=chunk.content # 为了保存历史记录


            seen = set()  # 用于去重，避免同一张图片重复出现
            md_img_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
            for i, doc in enumerate(rechunks):
                # 检查 text 字段中的 Markdown 图片 (主要针对 Local Chunk)
                text = doc.get("content")
                matches = md_img_pattern.findall(text)
                for img_url in matches:
                    img_url = img_url.strip()
                    seen.add(img_url)
            images=list(seen)

            put_data(task_id,event="final",data={"image_urls":images})



            if answer:
                message_id=save_chat_message(
                    session_id=session_id,
                    role="assistant",
                    text=answer,
                    rewritten_query=rewritten_query,
                    item_names=item_names,
                )




        return {
            "answer":answer,

        }