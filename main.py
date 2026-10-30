import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# API Key is loaded from .env; never print credentials.

# 示例：假设系统有环境变量 MY_KEY=system_val，.env里 MY_KEY=dotenv_val
print(os.getenv("MY_KEY"))
# load_dotenv() → 输出 system_val（系统优先级高）
# load_dotenv(override=True) → 输出 dotenv_val（.env覆盖系统）


from atguigu.tool.milvus_client_tool import get_milvus_client
if __name__ == '__main__':

    client = get_milvus_client()
    print("Milvus 服务端版本：", client.get_server_version())