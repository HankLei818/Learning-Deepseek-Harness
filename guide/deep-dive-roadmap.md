# DeepSeek Harness · 核心组件原理

理解这套框架，可以从三个问题入手。能力怎样装进来？一次任务由谁推进？过去发生的事怎样影响下一次回答？它们分别落在 Cordis、AgentLoop 和 Session 上。再向外看，LLM 负责和模型交换请求与响应，Tools 负责让模型提出的动作实际执行。这个索引按这五个组件组织，每篇沿着一个例子读到做决定的源码。[上游架构说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/architecture.zh.md#L7)

| 组件 | 为什么值得单独拆一篇 | 阅读入口 |
| --- | --- | --- |
| **Cordis 插件系统** | `read` 工具在配置里排在文件服务之前，为什么也能启动？当提供服务的插件退出，谁把依赖它的工具一起撤掉？ | [万物皆插件是怎样实现的](plugin-system.md) |
| **AgentLoop 执行循环** | 用户说一句话，为什么模型可能被问两次？程序怎样区分进入下一步、重试当前步和结束回合？ | [谁决定要不要再问一次模型](agent-loop.md) |
| **Session 与记忆** | 同一会话的原文、模型现在能看见的消息、新会话能找回的信息，分别由谁管理？ | [一条信息怎样被记住、压缩和召回](session-memory.md) |
| **LLM 模型服务** | 同一接口怎样接入不同模型？流式片段何时成为完整消息，模型切换时哪些信息还要传下去？ | 待写 · [适配器与运行时](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L190) |
| **Tools 工具系统** | 怎样从工具声明走到执行？当两个工具倒序完成、其中一个失败时，谁负责把结果与原调用对齐？ | 待写 · [批量执行与结果提交](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts) |

**记忆值得放在主线。** 默认配置用会话日志保留经历，`deriveMessages()` 决定当前模型看到哪一部分。主动引用或检索可带回另一会话的信息。想让新会话按偏好或事实召回，还能通过 MCP 接入独立的长期记忆服务。这几种做法各有自己的读写路径，在 Session 一篇里对照最清楚。[消息视图](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts#L760) · [跨会话引用](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/context/session-reference/README.zh.md#L34) · [第三方记忆服务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/user/guide/mcp-memory.zh.md#L5)

[入门版 · 十二课学习路线](../README.md) · [框架地图](architecture.md)
