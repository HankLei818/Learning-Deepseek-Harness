# DeepSeek Harness 中文源码教程

当你让 AI 助手读一个文件，模型负责决定下一步做什么，工具负责打开文件。DeepSeek Harness 把两者连起来，并记下整个过程。

## 从一次读文件开始

用户让助手读取 `greeting.txt`，读完只回复 `DONE`。用户最后看到的文字答复只有一个词。猜一猜，模型是在哪一步知道文件内容的？

<details>
<summary>展开看这次会话的三条记录</summary>

1. 模型请求调用 `read`，并给出文件名。
2. 工具读到 `hello`，框架把结果交给模型。
3. 模型看到了文件内容，按用户要求回复 `DONE`。

[查看原始记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L20)

</details>

想亲自核对？用 Git 下载这份教程，然后用 Python 3 查看随课记录。下载后可以离线运行，无需模型密钥。

```sh
git clone https://github.com/HankLei818/Learning-Deepseek-Harness.git
cd Learning-Deepseek-Harness
python3 labs/turn.py
```

最后一行应显示 `1 个回合 · 2 个步骤 · 1 次工具调用 · 1 个工具结果`。[第二课解释这些数字](notes/02-turn-and-tools.md)

## 按问题选一课

| 你想知道什么？ | 从这里读 |
| --- | --- |
| 从用户发出指令到文件写入磁盘，谁负责哪一步？ | [框架地图](guide/architecture.md) |
| 网页版和无界面模式为什么能共用同一套代码处理任务？ | [第一课 · 应用如何启动](notes/01-profiles-and-agent-loop.md) |
| 模型发出读文件请求后，怎样判断文件已经读到了？ | [第二课 · 跟踪一次工具调用](notes/02-turn-and-tools.md) |
| 长对话被压缩成摘要后，还能找到原话吗？ | [第三课 · 上下文压缩](notes/03-context-compaction.md) |

接下来会继续研究工具权限、关闭窗口后如何恢复会话，以及如何给助手添加一个工具。

每课回答一个问题，用真实记录或源码说明，再给一个能自己核对的结果。如果哪一段需要猜，欢迎把原句和你的疑问贴出来。[提问或反馈](https://github.com/HankLei818/Learning-Deepseek-Harness/issues/new)

[教程对应的源码版本](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)
