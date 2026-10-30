"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
from pathlib import Path

# atguigu/import_process/nodes/node_entry.py
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodeEntry(NodeBase):
    """
    入口节点：任务分发
    """

    name = "node_entry"

    def process(self, state: ImportGraphState):
        local_file_path=state.get("local_file_path",'')
        if not local_file_path:
            logger.error("未提供文件路径")
            raise Exception("未提供文件路径")
        local_file_path_obj=Path(local_file_path)
        if not local_file_path_obj.exists():
            logger.error("文件不存在")
            raise Exception("文件不存在")

        suffix=local_file_path_obj.suffix #后缀
        file_title=local_file_path_obj.stem

        if suffix.lower()==".pdf":
            return {
                "is_pdf_read_enabled":True,
                "file_title":file_title,
                "pdf_path":str(local_file_path_obj),
            }
        elif suffix.lower()==".md":
            return {
                "is_md_read_enabled":True,
                "file_title":file_title,
                "md_path":str(local_file_path_obj),
            }
        else:
            logger.error("不支持的文件类型")
            raise Exception(f"文件不是可以支持的格式，只能支持PDF和MD文件")


if __name__ == '__main__':
    node=NodeEntry()
    init_state={
        "local_file_path":r"D:\output\hak180产品安全手册.pdf"
    }
    result=node(init_state)
    print(result)

    logger.info(list(ImportGraphState.__annotations__.keys()))


