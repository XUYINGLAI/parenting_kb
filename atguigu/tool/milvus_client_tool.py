"""
@Author:xuyinglai
@Date:2026/10/16
@DESC:
"""
import os
from pymilvus import MilvusClient, AnnSearchRequest, WeightedRanker
from atguigu.config.config import MilvusConfig

# 单例
milvus_client=None
def get_milvus_client():
    global milvus_client
    if not milvus_client:
        milvus_client=MilvusClient(
            uri=MilvusConfig.milvus_url,
            # token=  # 用户:密码
        )
    return milvus_client # 返回实例对象


def get_search_reqs(
        dense_data,dense_anns_field,
        sparse_data,sparse_anns_field,
        dense_param=None,sparse_param=None,
        limit=10,expr=None):
    if dense_param is None:
        dense_param={
            "metric_type":"COSINE",

        }
    if sparse_param is None:
        sparse_param={
            "metric_type":"IP",
        }

    dense_req=AnnSearchRequest(
        data=dense_data,
        anns_field=dense_anns_field,
        param=dense_param,
        limit=limit,
        expr=expr,
    )



    sparse_req=AnnSearchRequest(
        data=sparse_data,
        anns_field=sparse_anns_field,
        param=sparse_param,
        limit=limit,
        expr=expr,
    )

    return [dense_req, sparse_req]


def hybrid_search(collection_name,reqs,output_fields,limit=10,ranker=(0.5,0.5)): # 混合检索
    weighted_ranker=WeightedRanker(*ranker)  # 实参写* 是解包列表  ** 是解包字典
    milvus_client = get_milvus_client()
    res=milvus_client.hybrid_search(
        collection_name=collection_name,
        reqs=reqs,
        ranker=weighted_ranker,
        limit=limit,
        output_fields=output_fields, # 字段
    )



    return res

