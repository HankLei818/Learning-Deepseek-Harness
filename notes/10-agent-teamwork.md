# 第十课 · 多个 Agent 怎么分工、交回结果？

一个助手把工作交给另一个助手后，怎样知道**谁在做、做完后得出了什么**？在团队模式下，大家可以从共享任务板看进度，从收件箱看同伴交回的结果。

## 一项任务的两条记录

上游用一个专门编排的测试场景把二者分开。主 Agent 让子 Agent 建立、领取并完成一项任务，然后回复 `TASK_DONE`。[测试场景](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/team-task-inbox/snapshot.yml#L2-L5) · [委派指令](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/team-task-inbox/session.v4.jsonl#L17)

| 看主会话的哪一行 | 发生了什么 | 主 Agent 知道什么 |
| --- | --- | --- |
| 19 | 任务板出现 `task-1`，状态是 `pending` | 有一项待办，还没人领取 |
| 20 | 状态变为 `in_progress`，记下了负责人 | 子 Agent 已领取任务 |
| 31 | 状态变为 `completed` | 板上这项任务已完成 |
| 37 | 收件箱收到子 Agent 的结束消息 `TASK_DONE` | 具体答复已经送到 |
| 42 | 结束消息进入下一步模型输入 | 主 Agent 现在能用这份结果回答用户 |

为什么不从第 31 行直接取结果？更新任务板只改变任务的状态。子 Agent 的最终答复会另外交回仍在线的父 Agent。中途需要对方处理新要求时，也可以显式发消息。[任务板记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/team-task-inbox/session.v4.jsonl#L19-L31) · [收件箱中的交付](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/team-task-inbox/session.v4.jsonl#L37-L42) · [任务和消息的分工](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/team/tool-agent-team/README.md#L131-L135)

<details>
<summary>任务完成时，答复已经到了吗？动手核对</summary>

在 **DeepSeek Harness 上游源码仓库**根目录运行，需要 Git 和 Python 3。

```sh
python3 - <<'PY'
import json
import subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
path = "snapshots/session/team-task-inbox/session.v4.jsonl"
lines = subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines()
for line, record in enumerate(lines, 1):
    event = json.loads(record)
    if event["type"] == "team/task":
        task = event["data"]["task"]
        print(line, task["id"], task["status"])
    elif event["type"] == "agent/inbox/spliced":
        for message in event["data"].get("inserted", []):
            if message["source"]["kind"] == "subagent-settled":
                print(line, "答复入箱", message["content"][-1]["text"])
    elif event["type"] == "user/message" and event["data"]["source"]["kind"] == "subagent-settled":
        print(line, "交给模型", event["data"]["content"][-1]["text"])
PY
```

预期先看到 `19 task-1 pending`、`20 task-1 in_progress`、`31 task-1 completed`，接着是 `37 答复入箱 TASK_DONE`、`42 交给模型 TASK_DONE`。回看第 32 行，此时对收件箱的等待确实超时了，尽管任务刚刚完成。[对照第 31–32 行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/team-task-inbox/session.v4.jsonl#L31-L32)

</details>

[上一课 · 子 Agent 一开始知道什么](09-subagent-context.md) · [下一课 · 用 Python SDK 提交任务](11-python-sdk.md) · [返回首页](../README.md)
