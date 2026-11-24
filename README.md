# Learning DeepSeek Harness

**一次读文件，为什么模型要回答两次？**

上游有一段很短的会话：用户让 Agent 读取 `greeting.txt`，然后回复 `DONE`。文件里只有 `hello`。在聊天窗口里，这像是一问一答；在 Session 里，却能找到两条 `assistant/message`。[上游会话记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl)

<details>
<summary>先猜两条消息分别做了什么，再点这里</summary>

第一条消息要求调用 `read`。工具运行后，框架把 `hello` 记为 `tool/result`；模型在下一步读到这个结果，才给出第二条消息 `DONE`。一次用户回合（turn）经历了两个模型步骤（step）。[跟着这段记录走一遍](notes/02-turn-and-tools.md)

</details>

这是一份面向开发者的中文源码教程。我们用 DeepSeek Harness 已提交的会话记录和测试，回答三个问题：Agent 如何行动、它记住了什么、我们能在哪里改变它的行为。前三课都可以直接在 GitHub 上阅读。

## 从你想弄懂的问题开始

| 我想弄懂…… | 从哪里开始 | 可以亲自验证什么 |
| --- | --- | --- |
| 整个框架如何协作 | [框架地图](guide/architecture.md) | 从一个用户动作找到负责编排、执行和记录的组件 |
| Web 和命令行为什么共用一个循环 | [第一课 · 应用如何组装](notes/01-profiles-and-agent-loop.md) | 用 Git 在三个配置文件里定位同一个循环和两个入口 |
| 模型怎样知道工具做完了 | [第二课 · 追踪一次工具调用](notes/02-turn-and-tools.md) | 在工具返回前暂停，预测下一条会话事件 |
| 压缩后怎么还能读到旧消息 | [第三课 · 上下文压缩](notes/03-context-compaction.md) | 对比同一份日志中保存的原记录和模型将读到的摘要 |

## 在本机看这段会话

克隆**学习仓库**后运行下面的命令，只需要 Python 3，无需模型密钥。它读取随课保存的事件摘录，可以离线使用。

```sh
git clone https://github.com/HankLei818/Learning-Deepseek-Harness.git
cd Learning-Deepseek-Harness
python3 labs/turn.py
```

然后执行 `python3 labs/turn.py --before-result`。在这个时间点，模型已经请求读文件。你能从已经出现的事件中找到文件内容吗？[实验说明与答案](notes/02-turn-and-tools.md)

## 接下来一起拆什么

- **工具权限。** 一次 `write` 从模型可见的工具声明走到磁盘，中间谁决定哪些路径可以写？
- **客户端与恢复。** 关闭窗口再打开，Web 如何拼起已有记录和正在生成的文字？SDK 能看到其中哪些事件？
- **做一个插件。** 为单个 Agent 新增一个工具，用一段会话验证它何时出现、由谁执行、如何留下结果。

如果你在某个行为上卡住了，欢迎[提一个源码问题](https://github.com/HankLei818/Learning-Deepseek-Harness/issues/new)：写下触发它的操作、你的预测和实际看到的结果。这样下一个读者也能复现它。

教程固定于上游提交 [`4b399c3`](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)。
