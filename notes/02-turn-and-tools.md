# 第二课 · 读一个文件，模型要开口几次？

用户给 Agent 一条指令：读 `greeting.txt`，然后只回答 `DONE`。文件里只有一行 `hello`。假设模型先选择 `read` 工具，再给最终答复，你猜会留下几个回合（turn）、几个步骤（step）、几次工具调用？[上游用户输入](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L10) · [示例文件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/workspace/greeting.txt)

## 停在答案出现之前

在**学习仓库**根目录执行。实验只用 Python 3 标准库，离线即可运行。

```sh
python3 labs/turn.py --before-result
```

最后一行事件是上游第 16 行的 `tool/call`。这时我们知道模型选择了哪个工具、要读哪个路径。仅凭这段记录，能断定文件读取成功吗？现在移开断点，看结果落在哪一步。

```sh
python3 labs/turn.py
```

<details>
<summary>展开核对数字和行号</summary>

本例有 **1 个回合、2 个步骤、1 次工具调用、1 个工具结果**。第 15 行的助手消息提出读取文件，第 16 行记录调用，第 17 行记录结果 `1: hello`。第 19 行开始第二步，第 20 行才出现 `DONE`。结果已经成为会话历史，模型可以在第二次请求里使用它。[原始记录第 15 行起](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15) · [构造请求时如何读取历史](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L718)

</details>

## 三个容易数错的地方

| 看到的现象 | 去哪里核对 |
| --- | --- |
| 日志里有两条 `user/message`，用户发了几次消息？ | 看第 10、11 行的 `source.kind`。一次来自用户，另一次是运行时补充的上下文。[两条记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L10) |
| 只有一条 `request/header`，为什么这次有两次模型请求？ | 初次请求会记录 header，后续配置、工具集合或请求系列发生变化时才需要再次记录。这个顺利完成的样本有两个 step，各有一条已完成的助手消息；若研究重试，还须检查同一步内的尝试。[header 写入规则](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L654) · [一次 step 内的请求循环](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L439) |
| 用户看见逐字输出，为什么日志里只有完整的助手消息？ | 运行时通过 `agent/assistant-stream` 发出实时帧。正常完成时，`assistant/message` 一次提交完整消息和紧凑的流记录。上游测试同时观察实时帧和 Session，核对两组内容能对应上。[实时分发](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L476) · [提交消息](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L564) · [上游测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/loop.spec.ts#L80) |

## 实验数据从哪里来

这节课读取上游标为 `recording: live` 的 `fs-read` 会话。随课摘录保留每条记录的原始行号、事件名，以及实验用到的字段。脚本只需在本机读取这份录制，就能按条件展示事件并计数。要独立核对，可把下条命令中的路径替换为本机固定版本上游仓库中的原文件；终端应给出相同的时间线。[随课数据](../labs/fs-read.jsonl) · [快照声明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/snapshot.yml#L5) · [随课数据的上游 MIT 许可](../labs/LICENSE.upstream)

```sh
python3 labs/turn.py --source /path/to/deepseek-harness/snapshots/session/fs-read/session.v4.jsonl
```

**再试一题。** 如果模型在同一条回复里要求读两个文件，第二个先读完，日志会先出现谁的结果？在查看这份[上游测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L239)之前先写下预测。

[上一课 · 启动时如何组装插件](01-profiles-and-agent-loop.md) · [下一课 · 上下文压缩](03-context-compaction.md) · [回到学习路线](../README.md)
