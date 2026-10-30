"""
@Author:xuyinglai
@Date:2026/10/27
@DESC:
"""
from fastapi import FastAPI, Path, Body, BackgroundTasks
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from atguigu.query_process.main_graph import QueryMainGraphRunner
from atguigu.tool.mongo_tool import get_recent_messages, clear_history
import uuid
import json
from atguigu.tool.task_utils import update_task_status, TASK_STATUS_PROCESSING, TASK_STATUS_COMPLETED, \
    TASK_STATUS_FAILED, create_queue, put_data, get_task_info, get_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]  # 允许跨域请求的头信息
)
@app.get("/health")# 健康检查
def health():
    return {"hello": "ok"}
# todo 返回历史列表到前端显示
@app.get("/history/{session_id}")
def get_history(session_id: str=Path(...,description="会话ID")):
    history_list=get_recent_messages(session_id)
    history_list=[{
        **item,
        "_id":str(item.get("_id")), # 把前面的覆盖了 因为序列化导致这 ObjectId会报错
    } for item in history_list]
    history_list.sort(key=lambda item: item["ts"],reverse=False)
    return {"items": history_list} # 字典列表 看前端需要什么

# todo 清空历史记录，mongodb的也被清理干净
@app.delete("/history/{session_id}")
def remove_history(session_id: str=Path(...,description="会话ID")):
    clear_history(session_id)
    return {"message":"ok"} # 前端对这个返回值没有要求

# todo 用户开始检索
class BodyParams(BaseModel):
    query:str=Field(...,description="检索关键字")
    session_id:str=Field(...,description="会话id")

def run_main_graph(query,session_id,task_id):
    init_state={
        "task_id": task_id,
        "session_id": session_id,
        "original_query": query,
    }
    # sse 后端主动推送 生成器接口流式推送
    try:
        update_task_status(task_id,TASK_STATUS_PROCESSING)
        put_data(task_id,event="progress",data=get_task_info(task_id))
        QueryMainGraphRunner.create_and_run(init_state)
        update_task_status(task_id,TASK_STATUS_COMPLETED)
        put_data(task_id, event="progress", data=get_task_info(task_id))

    except:
        update_task_status(task_id,TASK_STATUS_FAILED)
        put_data(task_id, event="error", data=get_task_info(task_id))
        raise


@app.post("/query") # 请求体参数
def query(
        background_tasks: BackgroundTasks,
        body_params:BodyParams=Body(...,description="检索关键字和会话id")
):
    query=body_params.query
    session_id=body_params.session_id
    task_id=str(uuid.uuid4()) # 看前端需要这个
    # 创建队列
    create_queue(task_id)

    # 添加后台任务
    background_tasks.add_task(run_main_graph,query,session_id,task_id)

    return {"task_id":task_id}

# todo sse的订阅请求
def generate_data(task_id):
    while True:
        data = get_data(task_id)
        yield f"event: {data['event']}\n"
        yield f"data: {json.dumps(data['data'])}\n\n"
@app.get("/stream/{task_id}")
def sse_stream(task_id:str=Path(...,description="任务id")):
    return StreamingResponse(generate_data(task_id),media_type="text/event-stream")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)