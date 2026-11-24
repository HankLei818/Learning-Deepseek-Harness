# DeepSeek Harness 中文源码教程

让助手读一个文件，模型会提出 `read`，文件工具才真正打开它。这个仓库用可回放的会话、能运行的实验和固定版本的源码，解释这两端是怎样连起来的。[先看框架地图](guide/architecture.md)

| 想做什么 | 从这里开始 |
| --- | --- |
| **从头学** | [12 课入门教程](notes/README.md) · 从应用启动读到用 Python 调用 Harness、亲手写一个工具 |
| **拆一个组件** | [5 篇组件原理](components/README.md) · 每篇跟一次具体调用，读到做决定的源码和验证它的测试 |
| **动手复现** | [实验目录](labs/README.md) · 任选一次离线回放，或启动本地运行时执行工具 |

## 五个核心组件

| 在一次读文件任务里 | 对应的原理文章 |
| --- | --- |
| 谁把 `read` 装到这个 Agent 上？ | [Cordis · 插件、依赖与作用域](components/plugin-system.md) |
| 为什么一句指令会发出两次模型请求？ | [AgentLoop · 回合、步骤与重试](components/agent-loop.md) |
| 请求怎样发到模型端点，流式回复怎样变成工具调用？ | [LLM · 从模型服务到 HTTP 和响应流](components/llm.md) |
| 谁执行 `read`？两次并行调用倒序完成时，结果怎么对应？ | [Tools · 从工具声明到结果提交](components/tools.md) |
| 文件内容如何进入下一次请求，重开会话又能找回什么？ | [Session · 消息历史与记忆](components/session-memory.md) |

## 从一次读文件开始

用 Python 3 回放一份上游录制。下载后可以离线运行，无需模型密钥。

```sh
git clone https://github.com/HankLei818/Learning-Deepseek-Harness.git
cd Learning-Deepseek-Harness
python3 labs/turn.py
```

模型先请求读取 `greeting.txt`，工具返回 `1: hello`，模型才回答 `DONE`。最后一行应显示 **1 个回合 · 2 个步骤 · 1 次工具调用 · 1 个工具结果**。[读懂这份记录](notes/02-turn-and-tools.md) · [核对上游原始记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L22)

[本教程对应的源码版本](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96) · [提问或反馈](https://github.com/HankLei818/Learning-Deepseek-Harness/issues/new)
