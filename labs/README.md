# 随课实验

所有命令都在**学习仓库根目录**执行。源码测试的命令则写在各篇组件文章末尾，需要进入上游源码仓库。

## 回放已有记录

只需 Python 3。前两项使用同一份 `fs-read` 记录，第三项使用 Web 流式回复录制。

| 想验证什么 | 运行命令 | 应看到什么 |
| --- | --- | --- |
| [一次工具调用的经过](../notes/02-turn-and-tools.md) | `python3 labs/turn.py` | 1 个回合、2 个步骤、1 次调用、1 个工具结果。加 `--before-result` 可以停在结果出现之前。 |
| [两次模型请求的差别](../notes/05-model-inputs.md) | `python3 labs/request_inputs.py` | 第二次请求的消息从 3 条变成 5 条，多出助手提出的工具调用和工具结果。 |
| [屏幕上的文字怎样拼出来](../notes/06-streaming-replies.md) | `python3 labs/stream_reply.py` | 先收到 `D`，再收到 `ONE`，拼出的 `DONE` 与保存的答复相同。 |

## 启动 Harness 实际执行

需要 Python 3.10 或更新版本。先按[第 11 课的安装步骤](../notes/11-python-sdk.md)准备 SDK 和配套运行时。命令使用课程固定的 `0.2.2rc2` 发行版，模型端点监听本机，无需个人密钥。Windows 请用 `.\.venv\Scripts\python.exe` 替换下表的 `.venv/bin/python`。

| 想验证什么 | 运行命令 | 应看到什么 |
| --- | --- | --- |
| [通过 SDK 提交一轮任务](sdk_task.py) | `.venv/bin/python labs/sdk_task.py` | 答复为 `SDK_OK`，回合结束原因为 `completed`。 |
| [自己注册的工具是否真的执行](../notes/12-tool-plugin.md) | `.venv/bin/python -m labs.tool_plugin.run` | `count_codepoints('学习🌱')` 的工具结果和最终答复都是 `3`。 |

想看端点怎样产生回复、工具怎样算出结果，可以并排打开[本地模型端点](local_model.py)、[工具实现](tool_plugin/count_codepoints.mjs)和[端到端实验](tool_plugin/run.py)。

[入门课程](../notes/README.md) · [组件原理](../components/README.md) · [返回首页](../README.md)
