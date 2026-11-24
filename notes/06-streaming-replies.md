# 第六课 · 回复还没写完，文字怎样出现在屏幕上？

上一课看到模型最后回答了 `DONE`。这次看另一段同样以 `DONE` 结尾的 Web 会话。模型先输出 `D`，再输出 `ONE`。网页边接收边把新文字接到已有正文后面，这就是**流式输出**。[Web 原始记录，第 24 行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/turn-tail-actions/session.v4.jsonl#L24)

## 从模型到聊天窗口

| 时机 | 框架和网页各自做什么？ |
| --- | --- |
| 回复开始 | 框架通知网页，一条回复正在生成。 |
| 文字到达 | 框架把新片段发给正在查看这段会话的网页。网页收到 `D` 时，已有正文是 `D`。再收到 `ONE`，已有正文就变成 `DONE`。 |
| 回复正常结束 | 框架先把完整回复和片段记录一起写入一条 `assistant/message`，然后发出“已完成”的通知。 |

如果两个片段赶在同一次屏幕刷新前到达，读者可能直接看到 `DONE`。所以从这份记录能数出两个文字片段，也能核对最终页面显示了什么。[网页怎样拼接文字](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/client/ui-chat/src/client/conversation-nodes/assistant.ts#L109-L115) · [界面怎样合并刷新](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/client/ui-conversation/src/client/conversation/assembly.ts#L220-L235) · [最终页面](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/turn-tail-actions/completed.expected.md#L16)

## 亲自拼一次

在**学习仓库**根目录运行。只需 Python 3，实验会离线读取这条回复。

```sh
python3 labs/stream_reply.py
```

```text
收到 'D'，拼出的正文是 'D'
收到 'ONE'，拼出的正文是 'DONE'
会话记录 assistant/message 中的正文是 'DONE'
```

可以打开[随课数据](../labs/web-reply.json)，比较 `stream` 下的两个片段和 `message` 里的最终正文。实验按录制顺序拼接文字。浏览器实际何时重绘，由页面决定。[上游录制说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/turn-tail-actions/snapshot.yml#L3-L5) · [数据许可](../labs/LICENSE.upstream)

<details>
<summary>如果屏幕上已经出现 D，说明这条回复已经保存了吗？</summary>

屏幕上的 `D` 说明网页收到了一个片段。正常完成时，框架才提交这条回复。如果服务进程在提交前突然退出，重新打开会话时，日志里可能找不回这段临时文字。上游测试也确认，收到“已完成”通知时，完整消息已经写入会话。[提交顺序测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/loop.spec.ts#L87-L123) · [会话保存说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/architecture.zh.md#L134)

</details>

[上一课 · 模型请求的内容](05-model-inputs.md) · [框架地图](../guide/architecture.md) · [返回首页](../README.md)
