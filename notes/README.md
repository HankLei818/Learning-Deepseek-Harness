# 入门教程 · 十二课

第一次接触 DSH，直接读[第一课](01-profiles-and-agent-loop.md)。前十课可以在浏览器里跟着源码和记录阅读，最后两课在本机启动真正的 Harness，用模拟端点代替在线模型。[先看全局](../guide/architecture.md) · [配套实验](../labs/README.md)

## 第一部分 · 看懂一次任务

1. [应用如何启动](01-profiles-and-agent-loop.md) — 网页和命令行怎样共用一套执行逻辑？
2. [跟踪一次工具调用](02-turn-and-tools.md) — 模型怎样知道文件已经读到了？
3. [上下文压缩](03-context-compaction.md) — 对话压成摘要后，还能找到原话吗？

## 第二部分 · 跟踪执行过程

4. [工具的写入权限](04-write-permission.md) — 为什么模型能请求写文件，这次写入却被拒绝？
5. [模型请求的内容](05-model-inputs.md) — 工具读完文件，模型下一次多看到什么？
6. [流式输出](06-streaming-replies.md) — 回复还没写完，文字怎样出现在屏幕上？

## 第三部分 · 会话与协作

7. [恢复会话](07-session-resume.md) — 重新打开窗口后，旧消息和新回复怎么接上？
8. [切换模型](08-model-switch.md) — 同一项任务能让两个模型前后接手吗？
9. [子 Agent 的上下文](09-subagent-context.md) — 子 Agent 能记得父会话里提过的暗号吗？
10. [团队如何交付](10-agent-teamwork.md) — 任务板显示“已完成”时，去哪里找具体答复？

## 第四部分 · 动手实践

11. [用 Python SDK 跑一次任务](11-python-sdk.md) — 从自己的程序发送消息，取回最终答复。
12. [给助手添加一个工具](12-tool-plugin.md) — 写一个文本计数工具，亲眼看到它被调用、返回结果。

读完第 12 课，可以沿刚写好的工具继续追问。谁把它装进 Agent？模型看到怎样的声明？工具失败又由谁收尾？[进入五篇组件原理](../components/README.md)

[返回首页](../README.md)
