# 第七课 · 重新打开聊天窗口，旧消息怎么接回来？

再打开昨天的对话，网页按**会话 ID** 找到原来的记录。旧消息保存在框架的会话日志里，浏览器可以重新向服务端索取。[Web 客户端如何读取会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/web-client.zh.md#L44-L50)

## 补历史时，正好又来了一条回复呢？

1. 服务端先监听这个会话的新消息，再读取最近一段历史。
2. 网页先收到这段历史，以及历史读到哪里的位置标记。
3. 服务端接着发出这段历史尚未包含的新消息。这样，即使回复恰好在读取期间完成，网页也能接上。[订阅和读取顺序](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/session-controller/src/web/controller.ts#L32-L70)

关闭网页时，服务端可能仍在生成回复。重新连接时，它可以把当前正在生成的内容一起交给网页。如果服务进程也已退出，能恢复的是已保存的记录。第六课里那个只显示在屏幕上、尚未提交的 `D` 就可能丢失。[进行中回复的快照](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/session-controller/src/web/controller.ts#L47-L58) · [回复保存时机](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/architecture.zh.md#L132-L134)

## 服务重启后，下一条消息还是同一个会话吗？

上游还做了一个受控的 SDK 测试。第一轮结束后，测试关闭运行时，启动另一个运行时，用原来的 ID 恢复会话，再发送第二条消息。它检查恢复得到的 ID 与原来相同。试着猜一猜，第二条消息会记在第 1 轮，还是第 2 轮？[测试步骤](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/sdk.snapshot.ts#L979-L988) · [测试记录的性质](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/session-resume/snapshot.yml#L2-L5)

<details>
<summary>用 Git 和 Python 3 核对两轮记录</summary>

在 [DeepSeek Harness 源码仓库](https://github.com/deepseek-ai/deepseek-harness)根目录运行。命令只读取固定版本的测试数据。

```sh
python3 - <<'PY'
import json, subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
path = "snapshots/sdk/session-resume/session.v4.jsonl"
for line in subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines():
    event = json.loads(line)
    if event["type"] == "assistant/message":
        data = event["data"]
        reply = "".join(block["text"] for block in data["message"]["content"] if block["type"] == "text")
        print(data["turn"], reply)
PY
```

输出是 `1 ONE` 和 `2 TWO`。同一份日志里，恢复后的回答接在第二轮。[第一轮回答](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/session-resume/session.v4.jsonl#L16) · [第二轮回答](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/sdk/session-resume/session.v4.jsonl#L33)

</details>

[上一课 · 流式输出](06-streaming-replies.md) · [下一课 · 模型切换](08-model-switch.md) · [返回首页](../README.md)
