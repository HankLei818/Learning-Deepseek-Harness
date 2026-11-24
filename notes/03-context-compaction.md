# 第三课 · 压缩上下文后，旧消息去哪了？

模型每次能读到的对话和补充信息，合起来叫**上下文**。它有长度限制，所以框架可以把一段旧对话压成摘要。旧消息仍保存在会话（Session）日志里，下一次请求会在那段对话原来的位置读到摘要。

## 哪些内容被换成了摘要？

看上游的一次手动压缩。表里的数字是事件序号（`seq`），表示每条记录写入日志的先后顺序。[上游测试场景](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/snapshot.yml) · [完整会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/session.v4.jsonl)

| 序号 | 记录了什么 |
| --- | --- |
| 8–11 | 用户的提问，以及框架补充的运行环境、技能目录和时间信息 |
| 16 | 助手的回答 |
| 22 | 摘要，注明它概括了 8–11 |
| 23 | 一条带摘要的消息，要求在模型历史里用它替换 8–11 |

想一想，8 号提问和 16 号回答，哪一条还会原样出现在模型下一次读到的对话里？

<details>
<summary>查看答案</summary>

**16 号回答会保留原样。** 替换范围只到 11。模型先读到摘要，再读到 16 号回答。要回看 8 号提问的原文，可以直接查日志。[摘要写入代码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/src/region.ts#L497) · [模型如何读取历史](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts#L760)

</details>

<details>
<summary>从同一份日志里找出摘要和四条原记录</summary>

在 **DeepSeek Harness 上游源码仓库**根目录运行，需要 Git 和 Python 3。文件首行是会话信息，第二行才是事件 0，所以事件 22 和 23 对应文件第 24 和 25 行。[查看这两行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/session.v4.jsonl#L24-L25)

```sh
python3 - <<'PY'
import json
import subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
path = "snapshots/sdk/manual-compact/session.v4.jsonl"
lines = subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines()
events = [json.loads(line) for line in lines[1:]]
for seq, event in enumerate(events):
    if event["type"] == "compaction/summary":
        print("摘要", seq, "覆盖", event["data"]["shadowedSeqs"])
    if event["data"].get("source", {}).get("kind") == "compact-checkpoint":
        op = event["surfaceOp"]
        print("检查点", seq, "替换", op["startSeq"], "至", op["endSeq"])
        for old_seq in range(op["startSeq"], op["endSeq"] + 1):
            print("原记录", old_seq, events[old_seq]["data"]["source"]["kind"])
PY
```

输出开头是 `摘要 22 覆盖 [8, 9, 10, 11]` 和 `检查点 23 替换 8 至 11`。接下来的四行能逐条读出旧记录的来源，其中 `原记录 8 user` 对应用户提问。若想看模型收到的消息，还有一份上游测试直接检查第二轮请求的内容。[请求重建测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L499)

</details>

[上一课 · 追踪一次工具调用](02-turn-and-tools.md) · [下一课 · 工具的写入权限](04-write-permission.md) · [框架地图](../guide/architecture.md) · [返回首页](../README.md)
