# 第九课 · 子 Agent 一开始知道什么？

假设你先告诉助手“项目暗号是 `MARMALADE`”，等它答完，再让它找一个子 Agent 回忆暗号。你没有在派给子 Agent 的指令里重说暗号。它能答出来吗？关键在于父 Agent 创建它时，带过去了哪段对话。

| 创建方式 | 子 Agent 收到什么 | 适合什么任务 |
| --- | --- | --- |
| `subagent`（spawn） | 从新会话开始，收到父 Agent 写给它的任务说明 | 可以用几句话交代清楚的独立任务 |
| `subagent_fork`（fork） | 继承父会话截至上一个已结束回合的记录，再收到自己的任务说明 | 需要引用前面讨论过的要求、例子或决定 |

例如，用 spawn 委派检查文案，可以把目标读者直接写进任务说明。用 fork 接着改一篇讨论了好几轮的文章，先前定好的要求已经随历史带过去。正在发起委派的这一轮还没结束，其中的新要求仍要写进任务说明。[spawn 的初始会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/subagent/subagent-spawn-in-process/src/index.ts#L45-L54) · [fork 怎样选择继承范围](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/subagent/subagent-fork-in-process/src/index.ts#L39-L52)

## 顺着暗号找证据

在上游的 fork 实录里，父 Agent 的第 1 轮收到暗号并回答 `OK`。第 2 轮才发起委派。打开子会话，第 10 行已经有带暗号的原话，第 28 行收到的只是“前面提到的项目暗号是什么”，第 31 行答出 `MARMALADE`。[父会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/subagent-fork-in-process/session.v4.jsonl#L10-L25) · [子会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/subagent-fork-in-process/session.1.v4.jsonl#L28-L31)

<details>
<summary>动手核对两种子会话的起点</summary>

在 **DeepSeek Harness 上游源码仓库**根目录运行，需要 Git 和 Python 3。spawn 使用上游手工编排的测试记录，fork 使用上游实际录制的会话。

```sh
python3 - <<'PY'
import json
import subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
for mode in ("spawn", "fork"):
    path = f"snapshots/sdk/subagent-{mode}-in-process/session.1.v4.jsonl"
    lines = subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines()
    header, *events = map(json.loads, lines)
    first = next(e["data"] for e in events if e["type"] == "user/message")
    print(mode, "带入父历史", header["isSeeded"], "第一条消息来源", first["source"]["kind"])
PY
```

spawn 的输出是 `False` 和 `agent-message`，第一条输入来自父 Agent 的委派。fork 的输出是 `True` 和 `user`，第一条输入来自继承的旧对话。[spawn 测试记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/subagent-spawn-in-process/session.1.v4.jsonl#L1-L10) · [fork 实录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/subagent-fork-in-process/session.1.v4.jsonl#L1-L10)

</details>

[上一课 · 切换模型](08-model-switch.md) · [下一课 · 多 Agent 如何协作](10-agent-teamwork.md) · [课程目录](README.md)
