# Tools 原理 · 模型点名一个工具，谁决定能否执行？

上游录下过这样一次调用。用户让助手读 `greeting.txt`，读完只说 `DONE`。会话第 15 行是模型提出的 `read`，第 16 行是框架记录的 `tool/call`，第 17 行才出现文件正文 `1: hello`。三行里的调用标识相同。假设只看到第 16 行，你能断定文件已经打开了吗？答案取决于工具系统在哪一步记下这条事件。[实录场景](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/snapshot.yml#L2-L5) · [这次调用的三条记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L20)

## 1. 注册的工具，怎样成为本步骤可调用的工具？

文件插件用 `ctx.tools.register()` 登记 `read`，一起交给框架的有参数说明、执行函数和输出规则。注册表按作用域组织定义。它先收集全局和祖先注册，应用继承的限制，最后加入当前作用域自己的注册。因此同叫 `read` 的名字，到不同 Agent 这里可以指向不同实现。模型看到的是原生执行器从可见定义中提取的名称、说明和参数描述。执行函数仍由 Host 持有。[read 的定义](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/read.ts#L78-L91) · [工具作用域](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L192-L226) · [原生执行器的描述与调用](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tool-executor-native/src/index.ts#L7-L21)

这里有个时间差。给模型列出工具时，插件还在。等模型返回调用时，插件可能已撤下。每个步骤开始，`ToolsService.resolve()` 对可见工具逐个评估可选的 `when` 条件，把通过的注册保存为本步的 `toolSet`。循环给模型组装工具说明、稍后提交工具批次，用的是同一份选择。真正查找时，`toolSet` 还要核对当前 Agent、当前定义和注册身份。旧注册已经撤下，本步就不能凭相同名字执行后来装上的实现。[本步选择与身份核对](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L257-L296) · [组装时使用工具集](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L290-L297) · [执行时沿用工具集](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576-L583)

上游用例让模型在同一条回复里依次请求 `replace`、`x`、`x`。第一个工具会卸载旧的 `x`，再注册同名新工具。后两次调用都得到 `UNKNOWN_TOOL`，新工具执行次数为零。下一步可以重新选择。这解释了为什么注册表必须记住“这一份注册”。只保存工具名会把模型的旧请求交给它从未见过的实现。[同名实现替换测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L167-L201)

## 2. 什么时候才真的打开文件？

模型给出的参数是字符串 `{"file_path": "greeting.txt"}`。`ToolsService.execute()` 找到当前作用域的执行器，原生执行器把同一回复里的调用交给批调度器。调度器解析参数，为每项调用保留模型给出的 ID，并在开始处理它时写入 `tool/call`。**先写开始记录，再做执行前检查。** 因此，第 16 行只证明框架接手了这次调用。[选择执行器](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L353-L377) · [解析参数](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L59-L72) · [先记录再检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L154-L164)

| 阶段 | 它对这次 `read` 做什么 |
| --- | --- |
| `prepare` | 复制并冻结参数，运行 `tools/pre-execute`。策略可以放行、拒绝，或要求询问用户。即使前置策略放行，仍要检查全局和作用域内的 guard。被拒时直接生成带原因的错误结果。 |
| `dispatch` | 进入 `tools/execute` 中间件。正常委托到底层时，框架再取已准入的定义，调用 `tool.execute(args, exec)`。到这里文件工具才解析目标，并通过 `ctx.fs.readText()` 或 `streamText()` 取数据。 |
| `complete` | 标成 `post-result` 的结果进入后置策略，包括执行前被策略拒绝的结果。已标成 `final-result` 的直接定稿。批调度器将最终结果写入会话。 |

复制参数有实际意义。同一次调用中，权限策略检查的文件名和执行函数收到的文件名来自同一个冻结对象。拒绝也有明确落点。上游用例让第二项调用被策略拒绝，工具函数没有启动，日志里照样有该调用的失败结果和结构化原因。排查时可以按调用 ID 找到它。[参数与执行前检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L153-L230) · [调用实际函数](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L263-L312) · [后置策略](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L507-L545) · [策略拒绝测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L461-L504)

## 3. 两个工具倒序完成，为什么结果仍然有序？

一次模型回复可以同时请求多个工具。`read` 声明了 `isConcurrencySafe: () => true`。调度器对每次调用评估这个条件，只有明确返回 `true` 才允许并行。未声明、判断抛错等情况按独占处理。如果模型依次请求“可并行 A、独占 B、可并行 C”，A 收尾后才能开始 B，B 收尾后才轮到 C。这样，最后一项读取不会越过前面的独占写入。[read 的并发声明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/read.ts#L135-L139) · [并发判断](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L99-L114) · [独占调用测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L140-L165)

连续的可并行调用则共享有上限的并发名额。每项完成时把结果放进自己在批次中的位置。调度器另存一个 `committed` 游标，只从游标所在位置向后提交连续就绪的结果。假设模型先请求 A、再请求 B，两者都已启动，B 先完成。B 的计算已经结束，但 A 的位置还空着，此时日志里一条 `tool/result` 都没有。等 A 返回，才依次写入 A、B。**慢调用会延迟后面结果的提交，但两个工具函数可以同时工作。** 这样既能利用并发，模型下次读历史时也能按原调用顺序接收结果。[提交游标与并发池](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L138-L196) · [倒序完成测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L239-L260)

## 4. 文件工具返回的对象，怎样变成模型读到的消息？

`read.execute()` 返回一个含 `path`、`offset`、`lines` 和 `totalLines` 的对象。执行管线复制它、按工具的输出 schema 校验，冻结后再调用 `output.render()` 生成模型可读内容。`read` 还实现了 `presentationMeta()`，把行号、原文等字段留给界面。两个表示都来自同一次读取，界面重开时就能根据记录重画文件卡片。[生成结构化返回值](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/read.ts#L138-L165) · [校验与渲染](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L557-L585) · [read 的文本和界面元数据](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/read.ts#L108-L134)

现在再看第 17 行。批调度器以原调用 ID 写入 `tool/result`。`message.content` 含带行号的正文，`isError: false` 表明成功，`data.meta.lines` 则保有结构化的第一行。同一事件带有 `surfaceOp: "append"`，所以下次构造请求时，Session 会把这条工具消息加入历史。第 20 行的 `DONE` 来自随后那次模型回复。若读取二进制文件，同一个 `read` 会返回 `isError: true` 并带 `FS_NOT_TEXT`，调用方也就能区分“没读成功”和“成功读到空文件”。[提交结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L243-L265) · [原始结果与最终回复](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L17-L20) · [二进制输入测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/tests/integration.spec.ts#L147-L161)

## 自己验证

在学习仓库根目录运行 `python3 labs/turn.py`，可以离线回看这次 `read` 的调用和结果。要观察权限拒绝、同名替换、倒序完成这些运行时分支，在装好开发依赖的**上游源码仓库**根目录执行下列命令，无需模型密钥。[上游开发环境](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/development.zh.md)

```sh
./node_modules/.bin/vitest run packages/core/agent-loop/tests/tool-calls.spec.ts \
  -t 'rejects pending calls whose original registration was replaced|commits tool/result in model order|orders pre-execute denials and errors without dispatching them|an exclusive call between two parallel-safe calls'

./node_modules/.bin/vitest run packages/fs/tool-fs/tests/integration.spec.ts \
  -t 'returns line-numbered content|reports a binary file as an error'
```

第一组应显示 `4 passed`，用固定模型回复控制调用顺序。第二组应显示 `2 passed`，测试在临时目录实际写入两行文本和一个二进制文件，再调用 `read`。回到最初的问题，可以沿同一 ID 查三件事。模型请求了什么，框架作了什么执行决定，最终交给模型的结果是什么？

[追踪工具结果怎样编码进下一次模型请求](llm.md) · [动手添加一个工具](../notes/12-tool-plugin.md) · [五篇组件原理](README.md)
