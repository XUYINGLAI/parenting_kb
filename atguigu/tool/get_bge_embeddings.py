"""
@Author:xuyinglai
@Date:2026/10/14
@DESC:
"""
# 数据向量化工具
from typing import List

from pymilvus.model.hybrid import BGEM3EmbeddingFunction

from atguigu.config.config import BGEM3Config
from atguigu.tool.json_format import json_format


# from FlagEmbedding import BGEM3FlagModel  # 之前使用这个初始化模型对象
bge3_model=None

def get_bge_model():
    global bge3_model
    if bge3_model is None:
        bge3_model = BGEM3EmbeddingFunction(
            model_name=BGEM3Config.bge_m3_path, # 不是写名字，写我本地下载路径
            device=BGEM3Config.bge_device,

            use_fp16=BGEM3Config.bge_fp16,
        )
    return bge3_model

def get_bge_embedding(texts:list[str]): # 接收列表
    model=get_bge_model()
    result=model.encode_documents(texts) # 这个返回结果有很多不需要的东西

    # print(result)
    # print(type(result))
    # print(result.get("dense"),type(result.get("dense")))
    # print(result.get("dense")[0],type(result.get("dense")[0]))
    # print(result.get("dense")[0][0],type(result.get("dense")[0][0]))
    # print('*'*80)
    # print(result.get("sparse"),type(result.get("sparse")))
    # print('*' * 80)
    # print(result.get("sparse").__dict__)
    # for intem in result.get("sparse"):
    #     print(intem,type(intem))
    #     print('*' * 80)
    #     print(intem.__dict__)

    # 现在这两个都是 numpy / scipy 对象，
    # Milvus 存不了、json 也序列化不了，必须转成纯 Python 类型：
    return{
        "dense": [item.tolist() for item in result.get("dense")]   ,
        "sparse":[dict(zip(item.indices.tolist(),item.data.tolist())) for item in result.get("sparse")]   ,
    }


if __name__ == "__main__":
    result=get_bge_embedding(["我是傻逼","我是徐应来"])
    print(json_format(result)) # 向量化的结果
    with open(r"D:\output\test.json","w",encoding="utf-8") as f:
        f.write(json_format(result))
