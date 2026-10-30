"""
@Author:xuyinglai
@Date:2026/10/27
@DESC:
"""
import shutil
import time
from datetime import datetime

import pathlib
import uvicorn
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Path
import uuid


from starlette.middleware.cors import CORSMiddleware

from atguigu.config.config import MinioConfig
from atguigu.import_process.main_graph import MainGraphRunner
from atguigu.tool.logger import logger
from atguigu.tool.minio_client_tool import get_minio_client
from atguigu.tool.task_utils import get_task_info, update_task_status, TASK_STATUS_PROCESSING, TASK_STATUS_COMPLETED, \
    TASK_STATUS_FAILED, add_running_task, add_done_task, add_node_duration

app = FastAPI(
    title="掌柜智库-导入API",# /docs那边才可以看到
    description="此文档是掌柜智库导入流程的API接口说明"
)
# 配置跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许所有来源访问
    allow_credentials=False,   # 不允许携带跨域凭证
    allow_methods=["*"],       # 允许所有请求方法
    allow_headers=["*"],       # 允许所有请求头
)
def run_main_graph(task_id,local_dir,local_file_path:str):
    # 调用
    init_state={
        "local_file_path":local_file_path,
        "local_dir":local_dir,
        "task_id":task_id,
    }
    try:
        # 修改状态为：运行中
        update_task_status(task_id,TASK_STATUS_PROCESSING)
        result=MainGraphRunner().create_and_run(init_state)
        # 修改状态为：完成
        update_task_status(task_id,TASK_STATUS_COMPLETED)
    except Exception as e:
        # 问题
        update_task_status(task_id,TASK_STATUS_FAILED)
        raise e


    logger.info(result)



@app.post("/upload")
def upload(background_task:BackgroundTasks,file: UploadFile = File(...)):
    task_id=str(uuid.uuid4())

    add_running_task(task_id,"upload_file")
    start_time=time.time()

    # 暂存
    local_dir=fr"D:\output\{datetime.now().strftime('%Y%m%d')}"
    local_dir_obj=pathlib.Path(local_dir)
    if not local_dir_obj.exists():
        local_dir_obj.mkdir(parents=True, exist_ok=True)

    local_file_path_obj=local_dir_obj / file.filename
    # print(local_file_path_obj)
    with open(local_file_path_obj, "wb") as f:
        shutil.copyfileobj(file.file, f,length=1024*1024)

    # 转储minio
    minio_client=get_minio_client()
    minio_client.fput_object(# 复制上传，
        bucket_name=MinioConfig.minio_bucket_name,
        object_name=f"upload_file/{datetime.now().strftime('%Y%m%d')}/{file.filename}" ,
        file_path=str(local_file_path_obj),
    )

    add_done_task(task_id,"upload_file")
    end_time=time.time()
    add_node_duration(task_id,"upload_file",end_time-start_time)


    # todo添加后台任务，跑graph
    background_task.add_task(run_main_graph,task_id,local_dir,str(local_file_path_obj))



    return {"task_id": task_id}

@app.get("/status/{task_id}")
def get_task_status(task_id: str = Path(...)):
    return get_task_info(task_id)


if __name__ == '__main__':
    print("hello")
    uvicorn.run(app, host="0.0.0.0", port=8000)