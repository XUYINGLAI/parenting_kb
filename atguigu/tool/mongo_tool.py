"""
@Author:xuyinglai
@Date:2026/10/19
@DESC:
"""
import time

# 给mongoDB的操作进行封装，增删改查
from pymongo import MongoClient
import os
from bson import ObjectId
from atguigu.config.config import MongoConfig

mongodb_client=None
def get_mongodb_client():
    global mongodb_client
    if mongodb_client is None:
        # mongodb_client = MongoClient(MongoConfig.mongo_url)
        mongodb_client=MongoClient(
            host=MongoConfig.mongo_host,
            port=MongoConfig.mongo_port,
        )

        print(mongodb_client)

    return mongodb_client

mongo_tool=None
def get_mongo_tool():
    global mongo_tool
    if mongo_tool is None:
        mongo_client=get_mongodb_client() # 获取连接对象,目的是为了创建数据库

        db=mongo_client[MongoConfig.mongo_db_name] # 创建库
        mongo_tool=db["chat_message"] # 创建表（集合）
        mongo_tool.create_index([("session_id",1),("ts",-1)]) # 建立联合索引
    return mongo_tool

# 表的增删改查操作
# clear_history清空某个session_id的所有消息
def clear_history(session_id):
    mongo_tool=get_mongo_tool()
    mongo_tool.delete_many({"session_id":session_id})
# get_recent_messages根据session_id获取最近的n条消息
def get_recent_messages(session_id,n=10):
    mongo_tool=get_mongo_tool()
    result=mongo_tool.find({"session_id":session_id}).sort("ts",-1).limit(n)
    return list(result) # 必须强转

# save_chat_message保存历史记录（根据id决定是添加还是修改）
# 增改一体
def save_chat_message(session_id,role,text,
                      rewritten_query=None,item_names=None,
                      ts=None,message_id=None):
    # {
    #     "session_id": "",
    #     "role": "",
    #     "text": "",
    #     "rewritten_query": "",
    #     "item_names": [],
    #     "ts": 123
    # }
    mongo_tool=get_mongo_tool()
    if message_id: #修改
        mongo_tool.update_one({"_id":message_id},{
            "$set":{
                "session_id":session_id,
                "role":role,
                "text":text,
                "rewritten_query":rewritten_query,
                "item_names":item_names,
                "ts":ts or time.time(),
            }
        })
    else:# 新增
        result=mongo_tool.insert_one({
            "session_id":session_id,
            "role":role,
            "text":text,
            "rewritten_query":rewritten_query,
            "item_names":item_names,
            "ts":ts or time.time(),
        })
        return result.inserted_id # 返回新增的行的ID

# 回填
def update_history_item_names(
        ids,item_names,rewritten_query,
):
    mongo_tool=get_mongo_tool()
    mongo_tool.update_many(
        {"_id":{"$in":ids}},
        {"$set":{"item_names":item_names,"rewritten_query":rewritten_query}}
    )

if __name__ == '__main__':
    # 模拟会话历史
    session_id = "test_001"
    # result=save_chat_message(session_id, "user", "咨询下烫金机。")
    # print(result)
    # result=get_recent_messages(session_id)
    # print(result)
    # 改
    save_chat_message("hhahah","user","hehehehe",message_id=ObjectId("6ad5f67c889452e508d753ce"))

    # 删
    clear_history(session_id)

