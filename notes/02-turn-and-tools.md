# 第二课 · 从工具调用到模型答复

从用户要求读文件，到收到最终答复，是一个回合（turn）。这个回合有两个步骤（step）。第一步，模型请工具读文件。第二步，模型看到工具结果，再回答用户。

## 先看到工具调用

在**学习仓库根目录**运行下面的命令。脚本用 Python 3 读取随课记录，可以离线运行，无需 API 密钥。

```sh
python3 labs/turn.py --before-result
```

最后显示的事件对应原始记录第 16 行。这里的 `tool/call` 记下了框架调用的工具 `read` 和要读的文件 `greeting.txt`。猜一猜，接下来哪条记录能告诉你文件是否读成功了？

## 再看工具返回了什么

```sh
python3 labs/turn.py
```

| 上游行号 | 事件 | 你能从中知道什么 |
| --- | --- | --- |
| 17 | `tool/result` | 工具传回 `1: hello`，说明读到了文件，第一行是 `hello`。 |
| 19 | `step/start` | 第二步开始。框架把工具结果放进发给模型的对话历史。 |
| 20 | `assistant/message` | 模型按用户要求回答 `DONE`。 |

终端末行应显示 **1 个回合 · 2 个步骤 · 1 次工具调用 · 1 个工具结果**。[对照原始记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L22) · [框架如何构造下一次请求](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L718)

<details>
<summary>为什么日志里的行数和请求次数对不上？</summary>

第 10、11 行都叫 `user/message`。看 `source.kind` 就能区分来源。一条标着 `user`，来自用户。另一条标着 `runtime-context`，是框架补充的信息。[两条消息的来源](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L10-L11)

这段录制有两次模型请求，却只有一条 `request/header`。两步沿用了同一份请求配置，框架只需记录一次。其他场景还可能在同一步里重试，请求次数也会随之增加。[请求配置的记录规则](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L654) · [重试逻辑](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L439)

</details>

实验摘自上游 `fs-read` 录制，保留了原始行号和本课用到的字段。[随课数据](../labs/fs-read.jsonl) · [上游录制说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/snapshot.yml#L5) · [数据的 MIT 许可](../labs/LICENSE.upstream)

[上一课 · 应用如何组装](01-profiles-and-agent-loop.md) · [下一课 · 上下文压缩](03-context-compaction.md) · [返回首页](../README.md)
