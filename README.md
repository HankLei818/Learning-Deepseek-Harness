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

## 十二课学习路线

想先看全局，可以从[框架地图](guide/architecture.md)开始。前十课可以直接在浏览器里读。第 11、12 课用 Python 在本机启动真正的 Harness，用本地测试端点代替在线模型。

### 第一部分 · 入门

1. [应用如何启动](notes/01-profiles-and-agent-loop.md) — 网页和命令行怎样共用一套执行逻辑？
2. [跟踪一次工具调用](notes/02-turn-and-tools.md) — 模型怎样知道文件已经读到了？
3. [上下文压缩](notes/03-context-compaction.md) — 对话压成摘要后，还能找到原话吗？

### 第二部分 · 执行

4. [工具的写入权限](notes/04-write-permission.md) — 为什么模型能请求写文件，这次写入却被拒绝？
5. [模型请求的内容](notes/05-model-inputs.md) — 工具读完文件，模型下一次多看到什么？
6. [流式输出](notes/06-streaming-replies.md) — 回复还没写完，文字怎样出现在屏幕上？

### 第三部分 · 会话与协作

7. [恢复会话](notes/07-session-resume.md) — 重新打开窗口后，旧消息和新回复怎么接上？
8. [切换模型](notes/08-model-switch.md) — 同一项任务能让两个模型前后接手吗？
9. [子 Agent 的上下文](notes/09-subagent-context.md) — 子 Agent 能记得父会话里提过的暗号吗？
10. [团队如何交付](notes/10-agent-teamwork.md) — 任务板显示“已完成”时，去哪里找具体答复？

### 第四部分 · 动手实践

11. [用 Python SDK 跑一次任务](notes/11-python-sdk.md) — 从自己的程序发送消息，取回最终答复。
12. [给助手添加一个工具](notes/12-tool-plugin.md) — 写一个文本计数工具，亲眼看到它被调用、返回结果。

每课回答一个问题，用真实记录或源码说明，再给一个能自己核对的结果。如果哪一段需要猜，欢迎把原句和你的疑问贴出来。[提问或反馈](https://github.com/HankLei818/Learning-Deepseek-Harness/issues/new)

[教程对应的源码版本](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)
