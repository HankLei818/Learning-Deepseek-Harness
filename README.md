# DeepSeek Harness 学习笔记

从一次真实的任务开始，沿源码追踪 DeepSeek Harness 如何启动 Agent、请求模型、执行工具，以及在重新打开会话时恢复上下文。这里记录我们的阅读顺序、实验和仍待回答的问题。

**从这里开始 → [第一课 · Web 和 Headless 如何共用同一个 AgentLoop](notes/01-profiles-and-agent-loop.md)**。这节课只需要 Git，大约五分钟可以核对结论。

## 学习路线

| 进度 | 主题 | 用什么问题检验自己 |
| --- | --- | --- |
| 已整理 | 应用启动与插件组装 | 给出一个 profile 名称，能否找到它加载的 bundle 和 AgentLoop 的注册位置？ |
| 下一课 | 一条消息的完整回合 | 模型先调用工具再回答时，会发起几次请求？哪些事件只在进程内流转，哪些写进 Session？ |
| 待研究 | Session 与上下文 | 如何只用日志重建某次请求？压缩之后，模型能看到哪段历史？ |
| 待研究 | 工具与执行权限 | 沿一次 `write` 调用，找到工具准入、路径解析和写权限检查各自发生的位置。 |
| 待研究 | Web、桌面与 SDK | 重新打开会话时，界面如何把已保存的消息和正在生成的文字接起来？ |
| 待实验 | 扩展一个 Agent | 写一个最小工具插件，为一个 Agent 挂载它，观察工具声明、调用和结果分别出现在哪里。 |

阅读基线为上游提交 [`4b399c3`](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)。每篇笔记固定所读版本，并保留一条可复现命令或一个上游测试，方便升级后重新核对。

## 下一课从哪里看

上游已经有一个很小的对照实验：模拟模型先后请求两个工具调用，让第二个调用先完成，再检查日志按什么顺序写入结果。先预测顺序，再读断言，最后沿 `ctx.tools.execute()` 找到实现。[工具顺序测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L239) · [AgentLoop 分派工具](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576)
