# 第十二课 · 给助手加一个自己的工具

我们要让助手调用 `count_codepoints`，数出“学习🌱”有几个 Unicode 码点。“学”“习”“🌱”各占一个，所以工具应当返回 `3`。

## 插件只做三件事

打开[工具源码](../labs/tool_plugin/count_codepoints.mjs)，按下面三个步骤读。

1. **告诉模型怎么调用。** `ctx.tools.register(...)` 注册工具。`name` 给它命名，`parameters` 声明必填的文本参数 `text`。
2. **算出结果。** 框架调用 `execute(args)`。插件检查参数，然后用 `Array.from(args.text).length` 计算码点数。
3. **把结果交回模型。** `output.schema` 声明结果为整数，`output.render` 把它转成模型能读到的文本。[上游工具接口](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/contracts.ts#L16-L40)

## 把工具装进一轮真实会话

先按[第十一课](11-python-sdk.md)安装 SDK，在**学习仓库根目录**运行下列命令。Windows 请把 `.venv/bin/python` 换成 `.venv\Scripts\python.exe`。

```sh
.venv/bin/python -m labs.tool_plugin.run
```

```text
tool/call   count_codepoints('学习🌱')
tool/result 3
最终答复    3
```

实验沿用第十一课的本地模型端点，无需云端密钥。脚本启动 `sdk-minimal`，用一份临时补丁加载插件的绝对路径。本地端点在工具清单中找到 `count_codepoints` 后，发出一次约定好的调用。Harness 随后执行插件，把结果交回端点。[实验脚本](../labs/tool_plugin/run.py) · [上游插件加载说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/user/develop/basic/index.md#L46-L56)

**怎样确认数字来自插件？** 脚本从会话中找到 `tool/call`，再用相同的调用编号找到 `tool/result`，最后与助手答复核对。端点只回显收到的工具结果。把输入换成下面这段，工具结果和最终答复应一起变成 `4`。

```sh
.venv/bin/python -m labs.tool_plugin.run 'AI🌱!'
```

**动手改一行逻辑。** 打开工具源码，把 `return Array.from(args.text).length` 改成下面三行。保存后重新运行上面两条命令，结果应当仍为 `3` 和 `4`。

```js
let count = 0
for (const point of args.text) count += 1
return count
```

[上一课 · 用 Python SDK 发起任务](11-python-sdk.md) · [接着读工具执行原理](../components/tools.md) · [课程目录](README.md)
