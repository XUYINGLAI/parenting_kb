# PDF 自动切分与空正文 chunk：第一次改编问题复盘

归档日期：2026-10-30。本文对应从「掌柜智库」到「育儿知识库」的第一次改编，以本次提交源码为准。作者已确认大 PDF 自动拆分与解析在本地实跑成功；下文记录历史问题、已完成处理和后续增强。

## 一、PDF 为什么要在后台切分

### 1. 现象与需求

此前导入约 300 页的育儿 PDF 时，在线解析耗时较长，需要人工将书籍拆成上、下篇。**本版已经完成后台自动拆分与解析，并经作者本地实跑成功。** 现在用户直接上传原始 PDF，由后台按最多 150 页拆分，再逐份调用 MinerU，无需人工分篇。

这是「PDF 页级拆分」，发生在结构化解析之前；后面的 `chunk_size=300` / `chunk_overlap=50` 是「文本切片」，发生在 PDF 转成 Markdown 后。两个步骤的输入、目的和计量单位不同。

### 2. 方案与源码入口

- `atguigu/web/service/import_service.py`：`/upload` 保存原文件、复制到 MinIO，并创建后台导入任务。
- `atguigu/tool/pdf_split_tool.py`：`split_pdf()` 按页拆分并检查导出文件大小。
- `atguigu/import_process/nodes/node_pdf_to_md.py`：`process()` 调度分段解析与合并，`_convert_single_pdf()` 保留原单份 MinerU 解析逻辑。
- `atguigu/import_process/nodes/node_md_img.py`：从最终 Markdown 同级的 `images` 目录读取图片，生成摘要并上传。

```text
原始 PDF 保存 / MinIO 归档
→ split_pdf(max_pages=150, max_bytes=180 * 1024 * 1024)
→ 按页序逐份 _convert_single_pdf()
→ 合并 Markdown，并复制、重命名图片
→ 返回一个 md_path / md_content
→ 原图片处理、文本切片、主题识别、向量化、入库流程
```

例：320 页通常生成第 1–150 页、第 151–300 页、第 301–320 页三份。`range(0, page_count, max_pages)` 使用从 0 开始的索引，文件名转成人类阅读习惯的从 1 开始页码。超过大小限制时在该页范围中点递归拆分，先左后右处理，保证返回结果页序。

### 3. 为什么除了页数还检查大小

150 页扫描件可能比 300 页纯文本文件还大。只限制页数不能保证服务接受该文件。

归档时查阅的 [MinerU 官方文档](https://mineru.net/apiManage/docs) 对当前使用的精准解析 API 给出单文件最多 200 页、200 MB 的限制。项目使用更保守的 150 页、180 MiB 分段阈值；外部接口限制可能调整，后续以官方文档为准。

每份导出后使用 `part_path.stat().st_size` 检查实际大小。若单页单独导出仍超限，抛出明确错误，要求先压缩该页图片；加密 PDF 和零页 PDF 也明确拒绝。因此「后台自动拆分」不代表支持任意容量的输入。

### 4. 为什么要合并图片而不只是正文

下一节点固定读取 `md_path.parent / "images"`。如果只拼正文，分散在各段解压目录的图片不会自动被发现。

每次解析用 UUID 创建独立目录，当前产物结构如下：

```text
pdf_job_<uuid>/
├─ parts/
│  ├─ pages_000001_000150.pdf
│  └─ pages_000151_000300.pdf
├─ parsed_0001/              # 第一份 ZIP 和解压结果
├─ parsed_0002/              # 第二份 ZIP 和解压结果
└─ merged/
   ├─ 原始文件名.md
   └─ images/
      ├─ part_0001_<原图片名>.jpg
      └─ part_0002_<原图片名>.jpg
```

Markdown 中的 `](images/原图片名)` 同时改为新名称，避免同名图片覆盖。当前实现只处理这一标准 Markdown 形式，没有覆盖 HTML 图片或所有可能的相对路径写法。`file_title` 保留入口设置的原文件名，不需要在图状态中改成多个文件。

### 5. 执行和失败边界

当前使用 `for` 循环串行解析，前一份完成后才提交下一份；这是有意保持实现简单，并未实现 PDF 分段并行。

所有分段解析合并成功后才进入后续图片、向量化和正文入库；其中任意一份抛错，任务失败。原文件可能已归档，局部分段和 ZIP 也可能留在磁盘。这不等于整个系统具有事务回滚：后续主体集合、正文集合和对象存储仍是不同写入步骤。

当前 `_convert_single_pdf()` 的轮询预算是 **1600 秒，约 26 分 40 秒，每份单独计算**，不是先前讨论的 1800 秒。计时判断发生在请求返回后，`requests` 调用没有显式 `timeout`，故它不是严格的总墙钟时间上限。等待状态与失败终态也没有区别处理，服务返回 `failed` 时可能继续等到预算耗尽。

### 6. 在已跑通流程上的后续增强

- 增加单次网络连接 / 读取超时，区分等待、完成、失败终态，保留服务端错误信息。
- 在前端展示第几段 / 共几段，持久化任务及分段结果，支持失败重试与恢复。
- 处理原始上传同名覆盖、容量配额、大文件上传和磁盘清理。
- 大书合并后仍会整体进入后续步骤，需继续评估内存、模型批量及长文处理成本。
- 分页边界可能截断跨页段落或表格，未来结合结构与原始页码完善溯源。

## 二、为什么出现 title=无标题、content="" 的 chunk

### 1. 观察到的现象

Milvus 中存在标题为「无标题」、正文为空的记录。提问「5岁孩子睡前总拖延、反复下床，家长应该怎么做」可以回答，而提问「儿童性格心理学的作者是谁」曾报重排请求失败。

![Milvus 中的正文切片，包含历史空正文记录](images/v0.1/milvus-chunks.png)

注意：「无标题」是代码填写的默认值，并不是数据库丢失了标题；只有标题的一条片段，与正文完全为空的片段，也需要分别判断。

### 2. 根因：第一个标题之前没有内容，却生成了区块

源码：`atguigu/import_process/nodes/node_document_split.py` 的 `NodeDocumentSplit.process()`。

假设文件第一行就是：

```markdown
# 餐桌冲突与挑食沟通话术

孩子不愿意吃饭时……
```

初始 `start_index=0`，第一行命中标题时 `idx=0`，执行：

```python
temp_section_list.append(split_line_list[start_index:idx])
# 实际 append(split_line_list[0:0])，加入的是 []。
```

接下来把空区块转换为正文，并自动填写标题：

```python
content = "\n".join(temp_section).strip()  # ""
title = (
    content.split("\n", 1)[0]
    if content.startswith("#")
    else "无标题"
)
```

得到 `{"title": "无标题", "content": ""}`。后续只判断 `len(real_content) < 300`，长度为 0 也满足条件，于是加入 `final_chunk_list`。若文档开头只有空行，`.strip()` 后也会落到相同情况。

当前切分和正文入库节点没有逐条拒绝空内容，所以该记录可能继续向量化并入库。检查 `if not chunks` 只能拒绝整个列表为空，不能拒绝列表内部某一条正文为空。

### 3. 为什么只有部分问题触发

重排处理的是当前查询召回的候选，不是数据库全部记录。问题变化会改变普通检索、HyDE 和融合后的候选，因此含空记录的数据库仍可能对某些问题正常回答。

这与「失败的查询候选中出现空片段」相符，但历史日志只有泛化的「重排请求失败」，缺少服务端详细错误，不能据此认定它就是每次失败的唯一原因，也不能断言服务端如何处理某个空格。

### 4. 为什么空格不能代替过滤

```python
{"content": ""}.get("content", " ")  # 仍然是 ""
```

`get(key, default)` 的默认值仅用于键不存在；键已存在且为空字符串时，不会替换。

```python
content = chunk.get("content") or " "
bool("")   # False
bool(" ")  # True
```

`or " "` 虽然生成空格，但没有有效正文，且服务如果去除空白，仍会得到空字符串。Python 中空格为真值，会通过简单的 `if content` 检查。应过滤无效候选，而不是用占位字符假装它有内容。

### 5. 本次提交实际实现的保护

`atguigu/query_process/nodes/node_rerank.py` 当前是：

```python
merged_chunks = [
    {
        "title": chunk.get("item_name") or chunk.get("title"),
        "content": str(chunk.get("content") or ""),
        "url": chunk.get("url") or "",
        "source": chunk.get("source", ""),
    }
    for chunk in merged_chunks
]
merged_chunks = [chunk for chunk in merged_chunks if chunk["content"]]
```

将缺失内容和 `None` 归一为 `""`，过滤后再产生 `documents`，并令 `top_n=len(merged_chunks)`。返回的 `index` 对应本次发送列表的位置，用它给过滤后的同一个 `merged_chunks` 回填 `relevance_score`。

例如 `[空片段A, 正文B]` 过滤后变成 `[正文B]`，服务返回 `index=0` 就应指向 B。如果只过滤 `documents` 却对旧列表回填，就会错误地把 B 的分数填给 A。

### 6. 直接调用与工具函数封装的区别

掌柜智库阶段也使用 DashScope，只是经由 `text_rerank()` 封装。当前节点直接调用 `dashscope.TextReRank.call()`，从 `output.results` 读取 `index` 和 `relevance_score`。配置已经统一从 `RerankConfig` 读取，真实凭据不写入节点。

当前 `return_documents=False`，因为候选正文已保存在本地，只需返回下标与分数。直接调用没有让空记录自动失效，输入过滤才是本次保护的关键。SDK 1.x 接口风格和新版接口的响应路径不同，不应混用示例。

后续可重新封装普通 Python 函数 `text_rerank()`，统一请求、错误处理与 `[{"index": ..., "score": ...}]` 返回结构；不需要 `@tool`。过滤仍放在节点中，或显式返回原始下标映射，避免函数内部静默删正文造成错位。

### 7. 本次还没完成的改进

以下是建议方案，**不是本次源码已经完成的修复**：

切分源头在拼接后跳过空正文：

```python
content = "\n".join(temp_section).strip()
if not content:
    continue
```

查询防御层增加 `.strip()`，同时拒绝全空候选并交给后续无资料策略处理：

```python
content = str(chunk.get("content") or "").strip()
```

还需补充请求状态检查、具体错误码 / 信息 / 请求 ID、缺失结果和分数处理，清理已入库历史空记录。不能只删除标题为「无标题」的记录，因为没有 Markdown 标题的实际正文也可能有价值。仅包含标题的片段是否保留，应另定规则。

## 三、验收清单与证据边界

| 范围 | 应验证什么 | 当前证据 |
| --- | --- | --- |
| 页级拆分 | 150 / 151 / 320 页，页序不乱，每份不超页数 | 源码已实现；本次离线检查见 release-checks.md |
| 字节限制 | 超大小继续拆，单页超限明确报错 | 源码已实现；离线边界检查另记 |
| 分段合并 | 图片重名不覆盖，正文引用与实际文件一致 | 源码已实现；离线模拟合并检查另记 |
| 大 PDF 在线流程 | 原文件上传、自动拆分、逐份解析与合并 | 作者确认已本地实跑成功；归档时未重复调用云端服务 |
| 导入与问答展示 | 文件完成、Milvus 写入、聊天能返回答案 | 作者本地反馈和运行截图 |
| 空片段防御 | 请求列表没有空字符串且下标一致 | 当前源码可见；历史数据库截图仍有空记录 |
| 源头修复与纯空白 | 不产生空记录，重排拒绝空白且全空不报二次异常 | 待后续版本完成 |

运行截图是特定时刻的样本，不证明所有问题类型、容量、失败重试和并发场景都已通过。截图中的 892 条正文和 28 条主题是当时数据库快照计数，不是持续更新的仓库指标。

## 参考

- [MinerU API](https://mineru.net/apiManage/docs)
- [pypdf：按页范围写入](https://pypdf.readthedocs.io/en/stable/user/merging-pdfs.html)
- [阿里云重排序](https://help.aliyun.com/zh/model-studio/rerank)
- [DashScope 1.x 调用参考](https://help.aliyun.com/zh/model-studio/dashscope-1x-legacy-reference)
