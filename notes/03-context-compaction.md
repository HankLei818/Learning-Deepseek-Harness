# 第三课 · 上下文压缩以后，旧消息去哪了？

如果 Session 日志只能追加，模型窗口又需要腾出空间，框架怎么同时做到这两件事？我们读上游 `manual-compact` 场景：它通过 SDK 发起压缩，用受控模型端点记录结果，并保存了一份可以逐行核对的会话。[场景说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/snapshot.yml) · [完整记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/session.v4.jsonl)

## 读四行记录

`seq` 是从 0 开始的事件序号。文件第一行是会话头，因此这份 JSONL 的物理行号比 `seq` 大 2。

| seq | Session 收到的事件 | 在这次压缩中发生了什么 |
| ---: | --- | --- |
| 8–11 | 四条 `user/message` | 一条来自用户，另外三条携带工作目录等运行时信息、技能目录和时间上下文 |
| 16 | `assistant/message` | 第一轮的助手回答 |
| 22 | `compaction/summary` | 保存摘要，并记录它覆盖的事件序号 `[8, 9, 10, 11]` |
| 23 | `user/message` | 来源是 `compact-checkpoint`，携带 `replace(8, 11)`，把摘要放入后续模型历史 |

先预测：只看上表的事件，压缩结束时，模型历史是否还包含序号 8 的原始提问？序号 16 的回答呢？

<details>
<summary>展开答案，对照压缩前后的两种视图</summary>

| 读取对象 | 压缩结束时可读到的内容 |
| --- | --- |
| Session 的原始事件 | 序号 8–11 和 16 都还在，22 和 23 追加在后 |
| 提供给模型的消息历史 | 摘要 23 占据原先 8–11 的位置；范围外的回答 16 仍排在摘要后面 |

这里有两条容易混淆的记录。22 解释这次压缩覆盖了哪些信息；23 上的替换操作才改变后续请求的消息顺序。读另一个场景时，也要先看它声明的替换区间。[两条记录的写入代码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/src/region.ts#L497) · [模型历史生成代码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts#L760)

</details>

## 用记录核对自己的答案

有上游 Git 仓库和 Python 3 即可。在**上游仓库**根目录运行下列命令，读取固定提交并打印摘要、替换区间，以及被覆盖的原始事件。也可以直接在浏览器里对照[记录第 24、25 行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/manual-compact/session.v4.jsonl#L24-L25)。

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

预期先看到 `摘要 22 覆盖 [8, 9, 10, 11]` 和 `检查点 23 替换 8 至 11`，随后还能读到四条原记录的来源。要进一步验证模型实际收到了什么，可以读上游单测：它用模拟适配器捕获第二轮请求，直接断言摘要出现在系统提示之后。[请求重建测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L499)

[上一课 · 追踪一次工具调用](02-turn-and-tools.md) · [框架地图](../guide/architecture.md) · [返回首页](../README.md)
