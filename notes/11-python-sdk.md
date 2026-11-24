# 第十一课 · 用 Python 发起一次任务

前面的课读了已经保存的会话。这次亲手发一条消息，让 Python 拿到答复。实验会启动真正的 Harness 运行时，请求发到本机的模拟模型端点，它固定回复 `SDK_OK`。你可以反复运行，全程无需个人 API 密钥。[完整代码](../labs/sdk_task.py)

## 先跑一遍

在学习仓库根目录执行下面三条命令。需要 Python 3.10 或更新版本。首次安装会下载 SDK 和配套的运行时。这里固定使用两个包的同一发行版本 `0.2.2rc2`。[SDK 发行页](https://pypi.org/project/deepseek-harness-sdk/0.2.2rc2/) · [运行时支持的平台](https://pypi.org/project/deepseek-harness-runtime-bin/0.2.2rc2/#files)

```sh
python3 -m venv .venv
.venv/bin/python -m pip install deepseek-harness-sdk==0.2.2rc2
.venv/bin/python labs/sdk_task.py
```

Windows PowerShell 下，第一行用 `py -3 -m venv .venv`，后两行把 `.venv/bin/python` 换成 `.\.venv\Scripts\python.exe`。

```text
会话  lesson-11
答复  SDK_OK
结束  completed
```

## Python 做了哪三件事？

1. **启动。** 进入 `with DeepSeekHarness(...)` 时，SDK 启动随包安装的 `dsh`，并与它建立连接。实验选择 `sdk-minimal`，用临时目录保存配置和会话。
2. **发送并等候。** `harness.run("请回复 SDK_OK。", session_id="lesson-11")` 把指令交给运行时，等这一轮结束。返回值的 `final_response` 是助手答复，`finish_reason` 是结束原因。
3. **关闭。** 离开 `with` 时，SDK 关闭运行时进程。脚本随后打印结果，结束时清理临时目录。[启动与关闭](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/python/sdk/src/deepseek_harness/api.py#L146-L173) · [发送任务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/python/sdk/src/deepseek_harness/api.py#L190-L200)

试试把提示词改成“请回复 HELLO”。输出仍是 `SDK_OK`，因为随课端点固定返回这段文字。下一课会让它发起工具调用，沿相同的 SDK 链路把执行结果带回来。[本地模型端点](../labs/local_model.py)

[上一课 · 多个 Agent 怎么分工](10-agent-teamwork.md) · [下一课 · 写一个工具插件](12-tool-plugin.md) · [返回首页](../README.md)
