"""
@Author:xuyinglai
@Date:2026/10/29
@DESC:
"""
from atguigu.config.config import MilvusConfig
from atguigu.tool.milvus_client_tool import get_milvus_client



if __name__ == '__main__':

    client = get_milvus_client()

    for collection_name in (
        MilvusConfig.item_name_collection,
        MilvusConfig.chunks_collection,
    ):
        client.alter_collection_field(
            collection_name=collection_name,
            field_name="item_name",
            field_params={"max_length": 512},
        )

        info = client.describe_collection(collection_name)
        for field in info["fields"]:
            if field["name"] == "item_name":
                print(collection_name, field)