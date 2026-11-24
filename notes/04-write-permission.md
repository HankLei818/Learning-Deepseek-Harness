# 第四课 · 工具明明可用，为什么不能写这个文件？

模型可以请求调用 `write`。文件能否写进去，还得看这一次调用有没有写权限。在上游录制的一次对话里，模型先后两次请求把同一段文字写进工作目录里的 `policy-neutral.txt`，结果不同。[原始会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/permission-policy-context/session.v4.jsonl#L59-L82)

## 第一次为什么失败？

会话当时处于只读模式（`read-only`）。第 69 行记录了模型要写哪个文件，第 70 行才是工具返回的结果 `FS_SANDBOX_DENIED`。即使文件就在工作目录里，只读模式也会拦下写入。[会话模式](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/permission-policy-context/session.v4.jsonl#L59-L60) · [第一次调用和结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/permission-policy-context/session.v4.jsonl#L69-L70)

这项检查发生在写磁盘之前。`write` 把目标路径和本次权限交给文件服务。文件服务发现是只读模式，就返回错误。上游还有一个测试专门检查磁盘，确认被拒绝的新文件没有出现。[工具怎样提交写入](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/write.ts#L118-L125) · [文件服务的只读检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/fs-sandbox/src/index.ts#L156-L162) · [磁盘断言](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/fs-sandbox/tests/fs-sandbox.spec.ts#L69-L76)

## 第二次什么时候才算写好了？

模型再次请求写入同一个文件。第 76 行记录了 `allowed-once`，意思是“只允许这一次”。**读到这里，你能告诉用户文件已经写好了吗？**

<details>
<summary>展开，按行核对</summary>

| 原始行号 | 发生了什么 | 此时能确认什么 |
| --- | --- | --- |
| 74 | 模型再次调用 `write` | 已经提出写入请求 |
| 75–76 | 框架发起审批，得到 `allowed-once` | 这一次调用获得写权限 |
| 77 | 工具返回成功，操作为 `create` | 工具确认文件已创建 |
| 81–82 | `read` 读回 `POLICY_NEUTRAL_OK` | 文件内容也与预期一致 |

所以要等到**第 77 行**才能确认写完。如果还要核对写进去的文字，就看第 82 行。单次批准只对第二次调用生效。[调用、审批和结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/permission-policy-context/session.v4.jsonl#L74-L82) · [最终文件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/web/permission-policy-context/workspace.expected/policy-neutral.txt)

</details>

<details>
<summary>用 Python 读出这四个结果</summary>

在 **DeepSeek Harness 上游源码仓库**根目录运行，需要 Git 和 Python 3。下面的命令只读取固定版本的会话记录，可以离线完成。[获取上游源码](https://github.com/deepseek-ai/deepseek-harness)

```sh
python3 - <<'PY'
import json
import subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
path = "snapshots/web/permission-policy-context/session.v4.jsonl"
lines = subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines()

def data(line):
    return json.loads(lines[line - 1])["data"]

print("首次写入", data(70)["error"]["code"])
print("审批决定", data(76)["outcome"])
print("再次写入", data(77)["meta"]["operation"])
print("读回内容", data(82)["meta"]["lines"][0]["text"])
PY
```

你会看到以下四行。

```text
首次写入 FS_SANDBOX_DENIED
审批决定 allowed-once
再次写入 create
读回内容 POLICY_NEUTRAL_OK
```

</details>

[上一课 · 上下文压缩](03-context-compaction.md) · [框架地图](../guide/architecture.md) · [返回首页](../README.md)
