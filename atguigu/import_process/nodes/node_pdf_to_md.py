"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import time
import shutil
from pathlib import Path
from uuid import uuid4

from atguigu.tool.pdf_split_tool import split_pdf
from atguigu.config.config import MineruConfig
# atguigu/import_process/nodes/node_pdf_to_md.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodePDFToMD(NodeBase):
    """
    PDF 转 Markdown 节点：PDF结构化解析
    """

    name = "node_pdf_to_md"

    def _convert_single_pdf(self, state: ImportGraphState):
        local_file_path=state.get("local_file_path")
        local_dir=state.get("local_dir") # 输出保存的地址
        if not local_file_path:
            logger.error("local_file_path不能为空")
            raise ValueError("local_file_path不能为空")

        local_file_path_obj=Path(local_file_path)
        if not local_file_path_obj.is_file():
            logger.error("local_file_path文件不存在")
            raise ValueError("local_file_path文件不存在")

        if not local_dir:
            logger.error("local_dir不能为空")
            raise ValueError("local_dir不能为空")
        local_dir_obj=Path(local_dir)
        if not local_dir_obj.exists():
            local_dir_obj.mkdir(parents=True, exist_ok=True)

        # 使用minerU
        import requests

        token = MineruConfig.mineru_token
        url = "https://mineru.net/api/v4/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "files": [
                {"name": f"{local_file_path_obj}", "data_id": "abcd"}
            ],
            "model_version": "vlm"
        }
        file_path = [local_file_path]
        # 判断请求成功
        response = requests.post(url, headers=header, json=data)
        if response.status_code != 200:
            logger.error("上传文件请求失败")
            raise ValueError("上传文件请求失败")
        result = response.json()

        if result["code"] != 0:
            logger.error("上传文件请求数据获取失败")
            raise ValueError("上传文件请求数据获取失败")


        batch_id = result["data"]["batch_id"]
        urls = result["data"]["file_urls"]
        for i in range(0, len(urls)):
            with open(file_path[i], 'rb') as f:
                res_upload = requests.put(urls[i], data=f)
                if res_upload.status_code == 200:
                    logger.info(f"{urls[i]}上传成功")
                else:
                    logger.error(f"{urls[i]}上传失败")

                # 拿着上传得到的batch_id去轮询获取mineru转化的md的压缩包路径

        import requests

        token = MineruConfig.mineru_token
        batch_id = batch_id
        url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        total_time = 1600
        current_time = 0

        # 轮询获取 隔2秒发一次请求 直到拿到需要的结果(实时)
        while True:
            try:
                start_time = time.time()
                res = requests.get(url, headers=header)
                # 判断请求成功不成功
                if res.status_code != 200:
                    logger.error("获取mineru转化的md的压缩包路径请求失败")
                    raise ValueError("获取mineru转化的md的压缩包路径请求失败")
                # 请求成功拿请求体内容
                result = res.json()
                if result["code"] != 0:
                    logger.error("获取mineru转化的md的压缩包路径请求数据获取失败")
                    raise ValueError("获取mineru转化的md的压缩包路径请求数据获取失败")

                data = result.get("data")
                # 判断数据拿的对不对
                if data.get("extract_result")[0].get("state") != "done":
                    logger.error("获取mineru转化的md的压缩包路径请求数据获取数据不对，解析还在处理")
                    raise ValueError("获取mineru转化的md的压缩包路径请求数据获取数据不对，解析还在处理")

                url = data.get("extract_result")[0].get("full_zip_url")
                # print(url)
                break
            except Exception as e:
                time.sleep(2)
                end_time = time.time()
                current_time += end_time - start_time
                if current_time > total_time:
                    logger.error("获取mineru转化的md的压缩包路径请求超时")
                    raise ValueError("获取mineru转化的md的压缩包路径请求超时")
                continue

        # 下载压缩包的内容并保存到本地的zip文件当中
        import requests
        zip_res = requests.get(url)
        if zip_res.status_code != 200:
            logger.error("下载压缩包的内容请求失败")
            raise ValueError("下载压缩包的内容请求失败")

        zip_content = zip_res.content  # 获取压缩包的内容
        # 把压缩包的内容写入到本地的一个zip文件当中，保存到本地
        zip_file_path_obj = local_dir_obj / f"{local_file_path_obj.stem}.zip"

        with open(zip_file_path_obj, 'wb') as f:
            f.write(zip_content)

        # 把下载的zip文件解压到本地
        import zipfile
        unzip_dir_obj = local_dir_obj / f"{local_file_path_obj.stem}"
        # 幂等性删除
        if unzip_dir_obj.exists():
            shutil.rmtree(unzip_dir_obj)  # 递归删除 有没有内容都删
        unzip_dir_obj.mkdir(parents=True, exist_ok=True)

        # 打开zip压缩文件，把文件当中的内容解压到指定的目录当中
        with zipfile.ZipFile(zip_file_path_obj) as unzip_content_handler:
            unzip_content_handler.extractall(unzip_dir_obj)

        # 把解压出来的文件进行改名处理
        # 第一步找到老文件的位置
        old_md_file_path_obj = unzip_dir_obj / "full.md"
        # 第二步改名处理，但是没有落盘，返回的新的文件路径对象
        new_md_file_path_obj = old_md_file_path_obj.with_name(f"{local_file_path_obj.stem}.md")
        # 第三步真正的改名处理，落盘
        old_md_file_path_obj.rename(new_md_file_path_obj)

        with open(new_md_file_path_obj, 'r', encoding='utf-8') as f:
            md_content = f.read()

        return {
            "md_path": str(new_md_file_path_obj),
            "md_content": md_content
        }
    def process(self, state: ImportGraphState):
        pdf_path = Path(state["local_file_path"])
        output_root = Path(state["local_dir"])

        # 每次解析使用独立目录，避免拆分文件和图片相互覆盖。
        job_dir = output_root / f"pdf_job_{uuid4().hex}"
        job_dir.mkdir(parents=True, exist_ok=True)

        # 1. 自动拆分 PDF。
        part_paths = split_pdf(
            pdf_path=str(pdf_path),
            output_dir=str(job_dir / "parts"),
            max_pages=150,
        )

        # 2. 准备最终 Markdown 和图片目录。
        merged_dir = job_dir / "merged"
        merged_images_dir = merged_dir / "images"
        merged_images_dir.mkdir(parents=True, exist_ok=True)

        merged_sections = []

        # 3. 按页序逐份解析。
        for number, part_path in enumerate(part_paths, start=1):
            logger.info(
                f"PDF 分段解析：{number}/{len(part_paths)}，"
                f"文件：{part_path.name}"
            )

            single_state = {
                **state,
                "local_file_path": str(part_path),
                "local_dir": str(job_dir / f"parsed_{number:04d}"),
            }

            result = self._convert_single_pdf(single_state)

            part_md_path = Path(result["md_path"])
            content = part_md_path.read_text(encoding="utf-8")

            if not content.strip():
                raise ValueError(
                    f"第 {number} 份 PDF 的解析正文为空"
                )

            # 4. 合并图片，并同步修改 Markdown 图片引用。
            part_images_dir = part_md_path.parent / "images"

            if part_images_dir.exists():
                for image_path in part_images_dir.iterdir():
                    if not image_path.is_file():
                        continue

                    new_name = (
                        f"part_{number:04d}_{image_path.name}"
                    )

                    shutil.copy2(
                        image_path,
                        merged_images_dir / new_name,
                    )

                    # 对应当前项目使用的 Markdown 图片形式：
                    # ![](images/xxx.jpg)
                    content = content.replace(
                        f"](images/{image_path.name})",
                        f"](images/{new_name})",
                    )

            merged_sections.append(content.strip())

        # 5. 合并为一个 Markdown，继续交给后面的节点。
        merged_content = "\n\n".join(merged_sections) + "\n"
        merged_md_path = merged_dir / f"{pdf_path.stem}.md"
        merged_md_path.write_text(
            merged_content,
            encoding="utf-8",
        )

        return {
            "md_path": str(merged_md_path),
            "md_content": merged_content,
        }
if __name__ == '__main__':
    node = NodePDFToMD()
    init_state = {
        "local_file_path": r"D:\output\hak180产品安全手册.pdf",
        "local_dir": r"D:\output"
    }

    result = node(init_state)
    logger.info(result)