# 核心组件原理

读同一份会话记录，可以从不同的组件追问。模型在第 15 行要求读取 `greeting.txt`，第 16 行记录执行，第 17 行出现 `1: hello`，第 20 行才有最终答复 `DONE`。要研究哪一段，就从下面相应的文章读起。[上游原始记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L20)

| 组件 | 入口与出口 | 动手核对什么 |
| --- | --- | --- |
| [Cordis 插件系统](plugin-system.md) | 配置选择插件，Cordis 等所需服务就绪，再把能力注册到对应作用域。 | 撤掉服务，依赖它的工具何时从清单消失？ |
| [AgentLoop 执行循环](agent-loop.md) | 从收件箱领取输入，驱动模型和工具，在每步结束时决定是否继续。 | 两次模型请求，怎样分清是下一步还是重试当前步？ |
| [LLM 模型服务](llm.md) | 从模型与提供方的选择，到一次 HTTP 请求，再到统一格式的回复片段。 | 对照端点收到的参数与框架读到的文本、结束原因和用量。 |
| [Tools 工具执行系统](tools.md) | 从本步允许调用的工具，到权限检查、执行和回写结果。 | 让后一个工具先完成，再观察日志按什么顺序提交结果。 |
| [Session 与记忆](session-memory.md) | 把发生过的事写入日志，从中选出当前模型可以读到的消息。 | 用同一条信息对照会话恢复、压缩、显式引用和跨会话召回。 |

想跟完整执行过程，先读 **AgentLoop**，再分别追到 **LLM** 和 **Tools**。想写插件，先读 **Cordis** 再看 **Tools**。如果在排查“以前说过的话为什么没出现在请求里”，直接从 **Session 与记忆** 开始。

[框架地图](../guide/architecture.md) · [入门课程](../notes/README.md) · [实验目录](../labs/README.md) · [返回首页](../README.md)
