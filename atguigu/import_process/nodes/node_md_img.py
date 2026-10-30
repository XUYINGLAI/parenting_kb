"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from langchain.chat_models import init_chat_model
from minio import Minio
from minio.deleteobjects import DeleteObject

from atguigu.config.config import LLMConfig, MinioConfig
# atguigu/import_process/nodes/node_md_img.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger
from atguigu.tool.minio_client_tool import get_minio_client


class NodeMDImg(NodeBase):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    def process(self, state: ImportGraphState):
        # todo 第一步 获取到md_content
        md_content, md_path_obj = self.get_md_context(state)

        # todo 拿到md内容，匹配图片的位置名字，使用正则表达式
        image_dir = md_path_obj.parent / "images"
        if not image_dir.exists():
            return {
                "md_content": md_content,
            }
        image_names = os.listdir(image_dir)
        if not image_names:
            return {
                "md_content": md_content,
            }
        image_with_context_list = self.get_image_with_context_list(image_dir, image_names, md_content)
        image_with_summary_list = self.get_image_with_summary_list(image_with_context_list)

        # todo 上传图片
        minio_client = get_minio_client()
        upload_dir=f"{MinioConfig.minio_img_dir}/{datetime.now().strftime('%Y%m%d')}/{md_path_obj.stem}"# 目录名字
        # 上传之前要做幂等性删除  如果目录有文件，就先删除在上传新的
        old_image_generator=minio_client.list_objects(
            bucket_name=MinioConfig.minio_bucket_name,
            prefix=upload_dir,
            recursive=True,# 递归列出对象
        )
        delete_object_list=[DeleteObject(obj.object_name) for obj in old_image_generator] # 生成器 遍历删除

        errors=minio_client.remove_objects(# 使用这个工具删除
            bucket_name=MinioConfig.minio_bucket_name,
            delete_object_list=delete_object_list,
        )
        for error in errors:
            logger.warning("error occurred when deleting object", error)
        image_with_summary_url_list=[]

        #todo#########################################################
        for image_with_summary in image_with_summary_list:
            minio_client.fput_object(
                bucket_name=MinioConfig.minio_bucket_name,
                object_name=f"{upload_dir}/{image_with_summary.get('image_name')}",
                file_path=image_with_summary.get("image_path"),
            )
            url=f"http://{MinioConfig.minio_endpoint}/{MinioConfig.minio_bucket_name}/{upload_dir}/{image_with_summary.get('image_name')}"
            # print(url)
            image_with_summary_url_list.append({
                **image_with_summary,
                "url": url,
            })
        logger.info(image_with_summary_url_list)

        #todo###########################################
        # 替换url
        for image_with_summary_url in image_with_summary_url_list:
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_with_summary_url.get("image_name")) + r"\)")
            md_content=pattern.sub(
                # f"![{image_with_summary_url.get("summary")}]({image_with_summary_url.get("url")})",# 新
                lambda _:f"![{image_with_summary_url.get("summary")}]({image_with_summary_url.get("url")})",
                md_content,# 旧
            )
        # 最新的md文件路径，存放替换后的文档
        new_md_path_obj=md_path_obj.parent / f"{md_path_obj.stem}_new.md"
        with open(new_md_path_obj, "w",encoding="utf-8") as f:
            f.write(md_content)










        return {
            "md_content": md_content,
            "image_with_summary_list": image_with_summary_list ,
            "md_path":str(new_md_path_obj),
        }


    def get_image_with_summary_list(self, image_with_context_list: list[Any]):
        # 交给大模型
        llm = init_chat_model(
            model=LLMConfig.vl_model,
            model_provider="openai",
            api_key=LLMConfig.openai_api_key,
            base_url=LLMConfig.openai_api_base,
            temperature=LLMConfig.llm_default_temperature,
        )

        dq = deque(maxlen=30)
        image_with_summary_list = []
        for image_with_context in image_with_context_list:
            current_time = time.time()
            while dq and current_time - dq[0] > 60:
                # 先盲清一波
                dq.popleft()  # 第一个出队
            # 限制频率操作。使用队列
            if len(dq) == dq.maxlen:
                # 全部装满
                need_wait_time = 60 - (current_time - dq[0])

                if need_wait_time > 0:
                    time.sleep(need_wait_time)
                current_time = time.time()

                while dq and current_time - dq[0] > 60:
                    dq.popleft()
            dq.append(current_time)  # 令牌分发

            import base64

            # 1. 打开图片，rb 表示读取二进制数据
            with open(image_with_context.get("image_path"), "rb") as f:
                image_bytes = f.read()
                base64_data = base64.b64encode(image_bytes).decode("utf-8")

            # todo 构建提示词 System User Tool AIassistant
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_data}"
                            },
                        },
                        {"type": "text",
                         "text": f"""
                                    这是一张图片，图片上文部分为"{image_with_context.get("pre_text")}"，
                                    下文部分为"{image_with_context.get("post_text")}"，
                                    请用中文简要总结这张图片的摘要,字数在50字以内。"""
                         },
                    ],
                },
            ]  # todo 不能要逗号

            res = llm.invoke(input=messages)
            print(res.content)

            # 把摘要保存
            image_with_summary_list.append({
                "image_name": image_with_context.get("image_name"),
                "summary": res.content,
                "image_path": image_with_context.get("image_path"),  # 本地地址，后续会用
            })
        return image_with_summary_list

    def get_image_with_context_list(self, image_dir, image_names: Any, md_content: Path) -> list[Any]:
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

        #
        image_with_context_list = []

        for image_name in image_names:
            suffix = Path(image_name).suffix
            if suffix.lower() not in IMAGE_EXTENSIONS:
                logger.warning("图片后缀名不对")
                continue

            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_name) + r"\)")
            match = pattern.search(md_content)

            if match is None:
                continue
            start, end = match.span()  # 拿到图片在文档的位置
            print(match.span())
            pre_text = md_content[max(start - 300, 0):start]
            post_text = md_content[end:min(end + 300, len(md_content))]

            image_with_context_list.append({
                "image_name": image_name,
                "pre_text": pre_text,
                "post_text": post_text,
                "image_path": str(image_dir / image_name)
            })
        return image_with_context_list

    def get_md_context(self, state: ImportGraphState) -> tuple[Path, str]:
        md_path = state.get("md_path")
        if not md_path:
            logger.error("md_path不能为空")
            raise ValueError("md_path不能为空")
        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("md_path文件不存在")
            raise ValueError("md_path文件不存在")

        with open(md_path_obj, "r", encoding="UTF-8") as f:
            md_content = f.read()
        return md_content, md_path_obj


if __name__ == '__main__':
    node = NodeMDImg()
    init_state = {
        "md_path": r"D:\output\hak180产品安全手册\hak180产品安全手册.md"
    }
    result = node(init_state)
    logger.info(result)
