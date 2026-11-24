# 第八课 · 换一个模型，框架要改哪里？

模型已经接入时，只需为会话选择另一个模型。每一步开始前，框架都会读取当前选择，因此一次任务的前后两步可以用不同模型。工具结果和对话仍留在原来的会话里。[每步读取模型选择](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L286-L300)

## 同一轮任务，先用 Flash，再用 Pro

上游有一段实录。第一步交给 `deepseek-v4-flash`。待办工具执行成功后，测试插件把模型切到 `deepseek-v4-pro`。模型是由测试插件选的，整段任务仍只有一个用户回合。[切换动作](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/model-switch-notice/model-switch-driver.mjs#L25-L31) · [原始会话](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/model-switch-notice/session.v4.jsonl#L13-L29)

怎样确认第二步真的改用了 Pro？`model/selection` 记录“选中了谁”，`request/header` 记录“这次请求用了什么配置”。可以把两种记录放在一起看。

<details>
<summary>用 Git 和 Python 3 核对选择与请求</summary>

在 [DeepSeek Harness 源码仓库](https://github.com/deepseek-ai/deepseek-harness)根目录运行，无需模型密钥。

```sh
python3 - <<'PY'
import json, subprocess

ref = "4b399c39a6d1479cd84ca591b4d7c88e24d38a96"
path = "snapshots/session/model-switch-notice/session.v4.jsonl"
for line in subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines():
    event = json.loads(line)
    if event["type"] == "model/selection":
        print("选择", event["data"]["model"])
    elif event["type"] == "request/header":
        config = event["data"]["header"]["config"]
        print("请求", config["provider"], config["model"])
PY
```

```text
选择 deepseek-v4-flash
请求 deepseek-official deepseek-v4-flash
选择 deepseek-v4-pro
请求 deepseek-official deepseek-v4-pro
```

</details>

## 如果要接入全新的模型服务呢？

例子里两次请求的提供方都是 `deepseek-official`。框架先按提供方找到**适配器**，再把模型名交给它。适配器负责把框架的请求转换成该服务能接收的格式，并把响应交回框架。已有适配器支持的服务可以直接选。需要支持一种新的接口时，就通过插件注册相应的适配器。AgentLoop 仍按原流程组织对话、调用工具。[按提供方选适配器](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L942-L952) · [注册适配器](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L377-L399)

[上一课 · 恢复会话](07-session-resume.md) · [下一课 · 子 Agent 的上下文](09-subagent-context.md) · [返回首页](../README.md)
