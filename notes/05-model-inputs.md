# 第五课 · 模型每次请求到底看到了什么？

回到第二课。用户让助手读 `greeting.txt`，读完只回复 `DONE`。第一次请求时，模型知道**要读哪个文件**。第二次请求时，它才从工具结果里知道**文件里写着什么**。[原始会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L9-L20)

## 把两次请求并排看

| 框架交给模型的内容 | 第一次请求 | 第二次请求 |
| --- | --- | --- |
| 消息列表（`messages`） | 3 条消息，包括系统给助手的指引、用户的指令、框架补充的运行信息（如当前目录） | 5 条消息，保留前 3 条，新增助手请求读取文件的消息，以及工具返回的 `1: hello` |
| 可用工具的说明（`tools`） | 模型能查到 `read` 的用途，以及必填参数 `file_path` | 本例继续使用同一套工具说明 |

工具说明回答“我可以怎么读文件”，工具结果回答“读到了什么”。前者随请求提供，后者要等工具执行后才会进入下一次请求的消息列表。[框架组装请求的代码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L718-L732) · [read 的参数说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/read.ts#L79-L85)

## 亲自核对

打开原始记录时，第 9 行的 `{{system}}` 和第 12 行的 `{{tools}}` 是录制用的占位符。完整内容可以分开看：系统指引写着“读文本文件用 `read`”，工具清单列出 `read` 接受哪些参数。[系统指引](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/text-turn/system-prompt.expected.md#L9) · [工具清单](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/text-turn/tool-schemas.expected.json#L251-L260)

在**学习仓库**根目录运行。只需要 Python 3，可以离线查看这段记录。

```sh
python3 labs/request_inputs.py
```

脚本会列出两次请求各自用到了原记录的哪几行。第一次是 **9、10、11**，第二次多了 **15、17**。第 16 行明明也写着 `tool/call`，为什么没有算成第六条消息？

<details>
<summary>展开看第 15、16、17 行各记了什么</summary>

第 15 行是**模型说的话**，其中包含“调用 `read`”的请求。第 16 行记录**框架执行了这次调用**。第 17 行是**工具给模型的回答**。因此下一步的消息列表里追加了 15 和 17，第 16 行留在会话日志里供人追踪。[对照这三行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L17)

</details>

这个实验根据会话记录还原框架交给模型适配器的消息顺序。上游还用测试直接捕获适配器收到的请求，逐项核对消息列表和工具说明。[上游请求重建测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L872-L890)

[上一课 · 工具的写入权限](04-write-permission.md) · [下一课 · 流式输出](06-streaming-replies.md) · [第二课 · 工具调用经过](02-turn-and-tools.md) · [返回首页](../README.md)
