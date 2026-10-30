"""
@Author:xuyinglai
@Date:2026/10/8
@DESC:
"""
import time
# atguigu/import_process/base.py

from abc import ABC, abstractmethod

from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger
from atguigu.tool.task_utils import add_running_task, add_done_task, add_node_duration

"""
查询流程节点基类
定义统一的节点接口规范，提供通用功能
"""
class NodeBase(ABC):

    name: str = "node_base"  # 节点名称，子类应覆盖

    def __init__(self):
        """
        强制子类设置 name
        """
        if self.name == "node_base":
            raise ValueError(f"子类 {self.__class__.__name__} 必须覆盖 name 类属性")


    def __call__(self, state: ImportGraphState) -> ImportGraphState:
        """
        节点执行入口
        """
        try:
            # todo
            start_time=time.time()
            # 1. 开始准备执行节点

            logger.info(f"--- {self.name} 开始啦 ---")
            # todo 修改节点状态为开始运行
            task_id = state.get("task_id")
            add_running_task(task_id,self.name)
            # 2. 执行节点
            result = self.process(state)

            # 3. 执行节点成功
            logger.info(f"--- {self.name} 完成啦 ---")
            # todo 修改节点状态为运行结束
            add_done_task(task_id,self.name)

            # todo
            end_time = time.time()
            add_node_duration(task_id,self.name,end_time-start_time)

            return result

        except Exception as e:
            logger.error(f"{self.name} 执行失败: {e}")
            raise

    @abstractmethod
    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        节点核心处理逻辑
        子类必须实现此方法
        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """
        pass