"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import json
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from atguigu.config.config import MineruConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger


class NodeDocumentSplit(NodeBase):
    """
    文档切分节点：智能文档切片
    """

    name = "node_document_split"

    def process(self, state: ImportGraphState):
        md_path=state.get("md_path")
        file_title=state.get("file_title")
        if not md_path:
            logger.error("未提供文件路径")
            raise Exception("未提供文件路径")
        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("文件不存在")
            raise Exception("文件不存在")
        if not file_title:
            logger.error("文件名不存在")
            raise Exception("文件名不存在")


        with open(md_path_obj,"r",encoding="utf-8") as f:
            md_content=f.read()

        # 拿到md内容后，按行切分，split()方法
        # 统一换行符
        md_content=md_content.replace("\r\n","\n").replace("\r","\n")
        split_line_list=md_content.split("\n")


        is_block=False # 标志位 flase表示不在代码块
        code_pattern = r"^(`{3,}|~{3,})"
        title_pattern = r'^\s*#{1,6}\s+.+'
        # code_pattern = re.compile(code_pattern) # 一个正则字符串要写多次
        marker=None #
        start_index=0
        temp_section_list = []
        for idx, split_line in enumerate(split_line_list,start=0):
            split_line=split_line.strip()# 去除两端空格
            # 判断该行是不是标题
            #       先：判断该行不在代码围栏
            #       再：该行符合标题正则
            match=re.match(pattern=code_pattern,string=split_line)
            # print(match.group())
            if match: # 正则匹配成功，这一行长得像标题，但是还得具体判断
                # 拿到~~~或者```
                if not is_block: # ~~~或者```是第一次遇到，是代码块的开始
                    is_block=True
                    marker=match.group(1) # 我需要知道具体是~~~还是```，因为后面需要知道什么时候能结尾
                else:
                    if marker==match.group(1):
                        is_block=False
                        marker=None
                    else:
                        pass # 啥也不干

            if not is_block and re.match(title_pattern,split_line):
                # 该行一定是标题
                # 切
                temp_section_list.append( split_line_list[start_index:idx])# 包头不包尾
                start_index=idx

        temp_section_list.append(split_line_list[start_index:])

        # 把小列表整理成字典 粗切
        split_section_list=[]
        for temp_section in temp_section_list:
            content = "\n".join(temp_section).strip()
            title=content.split("\n",1)[0]  if content.startswith("#") else "无标题" # 只切一刀

            split_section_list.append({
                "title":title,
                "content":content,
                "file_title":file_title
            })

        # logger.info(json_format(split_section_list))



        # todo 细切：长切短合
        splitter=RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "。", "！", "？", "；", "!", "?", ";", " "],
            chunk_size=300,
            chunk_overlap=50,
        )

        final_chunk_list=[]
        for split_section in split_section_list:
            # 获取每个区块的内容，判断要不要切分
            title=split_section.get("title")
            content=split_section.get("content")
            real_content=content[len(title)+2:] if content.startswith("#")  else content

            if len(real_content)<300:
                final_chunk_list.append({
                    **split_section,
                    "part":0 # todo 溯源，没有被切的标号为0 ; 一旦被切了，就从1开始，1，2，3，4
                })
                continue
            if "<table" in real_content:
                final_chunk_list.append({
                    **split_section,
                    "part":0
                })
                continue
            # 开始切
            for idx, splite_text in enumerate(splitter.split_text(real_content),start=1):
                # 把切成的小文本，也放到final_chunk_list，
                final_chunk_list.append({
                    "title":title,
                    "content":title+"\n\n"+splite_text,
                    "file_title":file_title,
                    "part":idx
                })

            # logger.info(json_dumps(final_chunk_list))

        # 为了下一个节点的单元测试
        # 存储为json文件
        # with open(r"D:\output\hak180产品安全手册\chunks.json",'w',encoding="utf-8") as f:
        #     # f.write("".join_format(final_chunk_list))
        #     json.dump(final_chunk_list,f,ensure_ascii=False,indent=4)


        return{
            "chunks":final_chunk_list,
        }










if __name__ == '__main__':
    node = NodeDocumentSplit()
    init_state={
        "md_path":r"D:\output\hak180产品安全手册\hak180产品安全手册_new.md",
        "file_title":"hak180产品安全手册",

    }
    result=node(init_state)
    print(result)
    logger.info(json_format(result))
