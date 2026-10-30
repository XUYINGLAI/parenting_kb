# atguigu/query_process/nodes/node_web_search_mcp.py
import asyncio
import os
import json
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings

from atguigu.config.config import MCPConfig
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger



class NodeWebSearchMcp(NodeBase):
    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_web_search_mcp"

    def process(self, state: QueryGraphState):
        # TODO
        logger.info(f"【{self.name}】节点逻辑")
        rewritten_query=state.get("rewritten_query")

        # todo第一步：创建协程对象
        coro = self.mcp_run(rewritten_query)

        # todo 第二步：运行协程，等待执行结束
        result = asyncio.run(coro)


        # print(result.content[0].text)
        data = json.loads(result.content[0].text).get("pages")
        # print(json_format(data))
        chunks=[
            {
                "title":item.get("title"),
                "content":item.get("snippet"),
                "url":item.get("url"),
                "source":"web",
            }
             for item in data
        ]
        return {
            "web_search_docs":chunks,
        }





    async def mcp_run(self,query,limit=10) :
        async with MCPServerStreamableHttp(
                name="网络搜索工具",
                params={
                    "url": MCPConfig.mcp_base_url,
                    "headers": {"Authorization": f"Bearer {MCPConfig.mcp_api_key}"},
                    "timeout": 10,
                },
                cache_tools_list=True,
                max_retry_attempts=3,
        ) as server:
            result=await server.call_tool(
                tool_name="bailian_web_search",
                arguments={"query": query, "count": limit}
            )
            return result



if __name__ == '__main__':
    init_state={
         "rewritten_query":"关于hak180烫金机如何使用",
    }
    node_search_embedding = NodeWebSearchMcp()
    result=node_search_embedding.process(init_state)
    logger.info(json_format(result))