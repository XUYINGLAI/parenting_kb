# atguigu/query_process/nodes/node_rrf.py

from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger

class NodeRrf(NodeBase):
    """
    节点功能：Reciprocal Rank Fusion
    将多路召回的结果（向量、HyDE、Web）进行加权融合排序。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_rrf"

    def process(self, state: QueryGraphState):
        """
        节点逻辑
        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """
        # TODO
        logger.info(f"【{self.name}】节点逻辑")

        embeddings_chunks=state.get("embedding_chunks")
        hyde_embeddings_chunks=state.get("hyde_embedding_chunks")

        weighted_embedding_chunks=[
            (embeddings_chunks,1),
            (hyde_embeddings_chunks,1),# 设置权重->分子值
        ]
        rrf_dict={} # chunk的id为key 整个chunk为value
        for chunks,weight in weighted_embedding_chunks:# 解包
            for idx, chunk in enumerate(chunks,start=1):
                score=weight/(60+idx)
                id=chunk.get("id")

                if id in rrf_dict:
                    # 有重复
                    rrf_dict[id]["score"]+=score

                else:
                    # 无重复
                    chunk["score"]=score
                    rrf_dict[id]=chunk # 加入字典

        rrf_chunks=sorted(rrf_dict.values(),key=lambda x:x["score"],reverse=True)[:10 ]
        return {
            "rrf_chunks": rrf_chunks,
        }






if __name__ == '__main__':
    # 模拟两路的融合
    node=NodeRrf()
    init_state={
        "embedding_chunks":[
        {
            "content": "## 设备\n\n•\t将本设备放置在平整、水平且稳定的表面上（如桌面），避免震动和冲击。\n\n•\t将本设备放置在通风良好的环境中。\n\n•\t为了防止人员受伤，请谨慎操作，避免将手指放置在图中所示的区域中。\n\n![图片警示勿将手指伸入设备内部纸张通道区域，以防被锋利部件或运动机构夹伤，强调操作安全。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/944ad0b1ae642d4a65bc1b40c979beeb12bc30e6a409b9d9666ee013ff48cc60.jpg)",
            "part": 1,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436041,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7669357657432556,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片警示：禁止将手指伸入打印机进纸/出纸区域，以防夹伤；操作时需注意纸张锋利边缘，确保人身安全。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/3bf3b3639360a2c43c223a6ee46c44b27d54f4a79506a17a8b99e6ba4703df40.jpg)",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436042,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7569139003753662,
            "source": "local"
        },
        {
            "content": "## 为设备选择一个安全的位置\n\n![图片对比展示了搬运设备的错误方式（抓托盘/出纸盒）与正确方式（双手托住设备底部），强调安全搬运以防部件脱落或设备损坏。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/0bc44b278a939f7ec6ff239a4423c46a74a6e07572150f9e912f5fa55e0f598d.jpg)",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436045,
            "title": "## 为设备选择一个安全的位置",
            "file_title": "hak180产品安全手册",
            "score": 0.7559900283813477,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片警示打印机内部高温部件（170°C/338°F）存在烫伤风险，禁止触摸灰色标记区域，并强调操作前需等待设备冷却。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/37eecd8ac02745dac415a628b51c26974067062c9b9747c069579fdaa99dbae9.jpg)  \n儎⑟ഴḽ䆜઀ᛞ࠽व䀜᪮儎⑟Ⲻ䇴༽䜞ԬȾ",
            "part": 7,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436036,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7532610297203064,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片展示一只手正在操作一台打开盖子的设备（疑似打印机或复印机）内部的滚筒组件，属于设备维护或清洁场景。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/71f9e17a760882436455f7ddc3a5fd358ce821ceb6e598b76d013d93dc26c943.jpg)",
            "part": 8,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436037,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7529160976409912,
            "source": "local"
        },
        {
            "content": "## 设备\n\n•\t请勿拆解本设备。拆解本设备可能会导致火灾或触电。\n\n•\t请勿尝试自行维修本设备。打开或拆下盖子可能使您接触到危险电压点以及带来其他风险，并且可能使您的保修失效。对于所有维修事宜，请联系 Brother 呼叫中心或您当地的 Brother 经销商。\n\n•\t请在以下环境使用本设备：温度保持在 10 °C 和 32 °C 之间，湿度保持在 20% 和 80% 之间，无冷凝。\n\n•\t请勿使本设备受到阳光直射、过热、接触明火、腐蚀性气体、湿气或灰尘。否则可能产生触电、短路或火灾的风险，从而导致损坏设备和/ 或导致设备无法运行。\n\n•\t请勿将设备放在加热器、空调、电风扇或水附近。",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436031,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7455034255981445,
            "source": "local"
        },
        {
            "content": "## 为设备选择一个安全的位置\n\n![图片警示：设备出纸盒伸出桌面边缘存在跌落风险，可能导致人身伤害或设备损坏，应确保设备稳固放置且部件不悬空。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/baa3590221a744dda3b19dfb126ddc6a3fd79b59cf19ff8d6793b51114c0d57b.jpg)\n\n“重要事项”表示可能导致财产损失或本设备功能丧失的潜在危险情况。",
            "part": 4,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436047,
            "title": "## 为设备选择一个安全的位置",
            "file_title": "hak180产品安全手册",
            "score": 0.744644284248352,
            "source": "local"
        },
        {
            "content": "## HAK 180 烫金机\n\n•\t严禁未经授权擅自复制或重制本文档的任何部分或全部内容。\n\n•\t请注意，对于使用通过本设备制作的产品造成的任何损坏或利润损失，或者故障、维修导致的数据消失或更改，或者第三方提出的任何索赔，我们不承担任何责任。",
            "part": 3,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436028,
            "title": "## HAK 180 烫金机",
            "file_title": "hak180产品安全手册",
            "score": 0.7397591471672058,
            "source": "local"
        },
        {
            "content": "## HAK 180 烫金机\n\n产品安全手册（简体中文）\n\n感谢您购买 HAK 180 烫金机。\n\n在使用本设备之前，请先阅读本手册，包括所有预防措施。阅读本手册后，请妥善保管。\n\n有关使用本设备的更多信息，请参阅使用说明书，其可在兄弟 (中国)商业有限公司技术服务支持网站 http://www.95105369.com/Web/Manuals.aspx 上找到。建议您先通读使用说明书，再使用本设备。\n\n如需获得常见问题解答、故障排除和说明书，请访问\n\nhttp://www.95105369.com。\n\n对于本设备所有者不遵守本指南中规定的说明操作而导致的损害，Brother 不承担任何责任。",
            "part": 1,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436026,
            "title": "## HAK 180 烫金机",
            "file_title": "hak180产品安全手册",
            "score": 0.5295050740242004,
            "source": "local"
        },
        {
            "content": "## HAK 180 烫金机\n\n对于本设备所有者不遵守本指南中规定的说明操作而导致的损害，Brother 不承担任何责任。\n\n•\t对于保养、调整或维修事宜，请联系 Brother 呼叫中心或您当地的Brother 经销商。\n\n•\t如果本设备工作不正常或发生任何错误，请关闭本设备，拔下所有电缆，然后联系 Brother 呼叫中心或您当地的 Brother 经销商。\n\n•\t本文档中提供的信息可能会随时更改，恕不另行通知。\n\n•\t严禁未经授权擅自复制或重制本文档的任何部分或全部内容。",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436027,
            "title": "## HAK 180 烫金机",
            "file_title": "hak180产品安全手册",
            "score": 0.5268999934196472,
            "source": "local"
        }
    ],
        "hyde_embedding_chunks": [
        {
            "content": "## 设备\n\n•\t将本设备放置在平整、水平且稳定的表面上（如桌面），避免震动和冲击。\n\n•\t将本设备放置在通风良好的环境中。\n\n•\t为了防止人员受伤，请谨慎操作，避免将手指放置在图中所示的区域中。\n\n![图片警示勿将手指伸入设备内部纸张通道区域，以防被锋利部件或运动机构夹伤，强调操作安全。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/944ad0b1ae642d4a65bc1b40c979beeb12bc30e6a409b9d9666ee013ff48cc60.jpg)",
            "part": 1,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436041,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.8173573017120361,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片警示打印机内部高温部件（170°C/338°F）存在烫伤风险，禁止触摸灰色标记区域，并强调操作前需等待设备冷却。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/37eecd8ac02745dac415a628b51c26974067062c9b9747c069579fdaa99dbae9.jpg)  \n儎⑟ഴḽ䆜઀ᛞ࠽व䀜᪮儎⑟Ⲻ䇴༽䜞ԬȾ",
            "part": 7,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436036,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.8149075508117676,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片警示：禁止将手指伸入打印机进纸/出纸区域，以防夹伤；操作时需注意纸张锋利边缘，确保人身安全。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/3bf3b3639360a2c43c223a6ee46c44b27d54f4a79506a17a8b99e6ba4703df40.jpg)",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436042,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.814616858959198,
            "source": "local"
        },
        {
            "content": "## 设备\n\n![图片展示一只手正在操作一台打开盖子的设备（疑似打印机或复印机）内部的滚筒组件，属于设备维护或清洁场景。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/71f9e17a760882436455f7ddc3a5fd358ce821ceb6e598b76d013d93dc26c943.jpg)",
            "part": 8,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436037,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.8030044436454773,
            "source": "local"
        },
        {
            "content": "## HAK 180 烫金机\n\n对于本设备所有者不遵守本指南中规定的说明操作而导致的损害，Brother 不承担任何责任。\n\n•\t对于保养、调整或维修事宜，请联系 Brother 呼叫中心或您当地的Brother 经销商。\n\n•\t如果本设备工作不正常或发生任何错误，请关闭本设备，拔下所有电缆，然后联系 Brother 呼叫中心或您当地的 Brother 经销商。\n\n•\t本文档中提供的信息可能会随时更改，恕不另行通知。\n\n•\t严禁未经授权擅自复制或重制本文档的任何部分或全部内容。",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436027,
            "title": "## HAK 180 烫金机",
            "file_title": "hak180产品安全手册",
            "score": 0.7955605983734131,
            "source": "local"
        },
        {
            "content": "![图片为HAK 180烫金机产品安全手册封面，含条形码、型号D01WD7001-00、品牌SCHN及中文安全提示，强调使用前须阅读手册并参考官网资料。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/f93ddcd837fa399f0c165da43b0badb013c2961acc828a095c6d98f0a660dbca.jpg)  \nD01WD7001-00\n\nSCHN",
            "part": 0,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436025,
            "title": "无标题",
            "file_title": "hak180产品安全手册",
            "score": 0.7926693558692932,
            "source": "local"
        },
        {
            "content": "## 设备\n\n•\t请勿拆解本设备。拆解本设备可能会导致火灾或触电。\n\n•\t请勿尝试自行维修本设备。打开或拆下盖子可能使您接触到危险电压点以及带来其他风险，并且可能使您的保修失效。对于所有维修事宜，请联系 Brother 呼叫中心或您当地的 Brother 经销商。\n\n•\t请在以下环境使用本设备：温度保持在 10 °C 和 32 °C 之间，湿度保持在 20% 和 80% 之间，无冷凝。\n\n•\t请勿使本设备受到阳光直射、过热、接触明火、腐蚀性气体、湿气或灰尘。否则可能产生触电、短路或火灾的风险，从而导致损坏设备和/ 或导致设备无法运行。\n\n•\t请勿将设备放在加热器、空调、电风扇或水附近。",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436031,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.7919341921806335,
            "source": "local"
        },
        {
            "content": "## HAK 180 烫金机\n\n产品安全手册（简体中文）\n\n感谢您购买 HAK 180 烫金机。\n\n在使用本设备之前，请先阅读本手册，包括所有预防措施。阅读本手册后，请妥善保管。\n\n有关使用本设备的更多信息，请参阅使用说明书，其可在兄弟 (中国)商业有限公司技术服务支持网站 http://www.95105369.com/Web/Manuals.aspx 上找到。建议您先通读使用说明书，再使用本设备。\n\n如需获得常见问题解答、故障排除和说明书，请访问\n\nhttp://www.95105369.com。\n\n对于本设备所有者不遵守本指南中规定的说明操作而导致的损害，Brother 不承担任何责任。",
            "part": 1,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436026,
            "title": "## HAK 180 烫金机",
            "file_title": "hak180产品安全手册",
            "score": 0.626693606376648,
            "source": "local"
        },
        {
            "content": "## 为设备选择一个安全的位置\n\n![图片对比展示了搬运设备的错误方式（抓托盘/出纸盒）与正确方式（双手托住设备底部），强调安全搬运以防部件脱落或设备损坏。](http://192.168.10.10:9000/knowledge-base/upload-images/20261019/hak180产品安全手册/0bc44b278a939f7ec6ff239a4423c46a74a6e07572150f9e912f5fa55e0f598d.jpg)",
            "part": 2,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436045,
            "title": "## 为设备选择一个安全的位置",
            "file_title": "hak180产品安全手册",
            "score": 0.6194168329238892,
            "source": "local"
        },
        {
            "content": "## 设备\n\n如果遵守了操作说明进行操作，但是设备不能正确运行，请仅调整操作说明中涵盖的控制。错误调整其他控制可能导致损坏并且通常需要合格技术进行全面工作以将本设备恢复到正常操作。Brother不建议使用 Brother 正品烫金膜盒以外的其他品牌烫金膜盒。如果使用与本设备不兼容的耗材导致损坏本设备的任何零件，由此导致的任何维修可能不在保修范围内。",
            "part": 0,
            "item_name": "SCHNHAK180烫金机",
            "id": 469847825734436048,
            "title": "## 设备",
            "file_title": "hak180产品安全手册",
            "score": 0.6089511513710022,
            "source": "local"
        }
    ]
    }
    result=node(init_state)
    logger.info(json_format(result))