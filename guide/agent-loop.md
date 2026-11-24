# AgentLoop 原理 · 谁决定要不要再问一次模型？

让助手读 `greeting.txt`，读完只回复 `DONE`。用户只发了一句话，模型却收到了两次请求。但工具可以通过 `exec.concludeTurn()` 请求收尾，省去下一次模型调用。如果工具执行期间又收到新指令，即使工具要求收尾，两次请求也可能出现在**同一个回合**里。要解释这三个结果，需要看懂 AgentLoop 在哪几个时刻做决定。

## 入口在工厂里，循环在每个 Agent 身上

从源码目录打开 `index.ts`，先找到 `new ReactLoopAgent(...)`。外层的 `AgentLoop` 是 Cordis 服务，负责创建和管理 Agent。每个实例拿到自己的 Session、收件箱和运行状态。真正推动单个会话的是 `agent.ts` 中的三个嵌套循环。[实例创建](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/index.ts#L574) · [实例状态](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L111)

| 哪一层 | 管什么 | 什么时候再来一次 |
| --- | --- | --- |
| `kick()` 的循环 | 同一个 Agent 接下来还有没有回合要处理 | 当前回合正常收尾，收件箱还有待处理输入 |
| `turn()` 的循环 | 当前回合要走几个步骤（step） | 普通工具执行后还要让模型看结果，或收尾前又收到本步之后要处理的输入 |
| `step()` 的循环 | 为本步骤调用模型，一次调用算一次尝试（attempt） | 模型流返回结构化失败，错误处理插件明确要求重试 |

所以，**同一回合可以有两步，同一步也可以有两次请求**。读日志时先数 `turn/start` 和 `step/start`。仅凭 HTTP 请求次数，推不出用户发了几次话或执行了几次工具。[回合循环](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L271) · [步骤循环](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L338) · [尝试循环](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L439)

## 一句话到了，为什么不会启动两个循环？

`followup()` 把消息放进 `next-turn` 并请求唤醒。空闲时，`wakeDriver()` 先把状态改为 `running`，再启动异步的 `kick()`。如果这时又收到一条普通追问，现有循环会继续领取输入。两条追问按回合排队，共用一个驱动器。[入队](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L168) · [启动顺序](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L232)

`steer()` 和 `inject()` 则把消息放进 `next-step`，前者请求唤醒，后者只入队。回合首步会先取走所有 `next-step` 输入，再取至多一个 `next-turn` 输入。后续步骤只取 `next-step`。这解释了为什么“请再做一件事”和“补充一下当前任务”可以有不同的执行时机。[三个发送入口](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L177) · [收件箱的领取规则](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/inbox.ts#L103)

**入队、领取、发给模型是三个时刻。** `preStep()` 先领取本步输入，确定模型和工具集，再让 `agent/pre-step` 监听器决定是否放行。放行后才记录 `step/start`。如果插件在更晚的 `agent/request` 钩子里调用 `inject()`，消息虽然已经进了收件箱，当前请求仍然读不到它。上游测试把它标成 `[late context]`，直接检查它只出现在后一次请求。[步骤准备](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L286) · [记录步骤开始](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L343) · [晚到输入的测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L737)

## 顺着一次 read，对照两次请求

下面的数字是固定版本录制文件的**行号**。先看第 15–17 行。同一个工具调用标识把模型提出的 `read`、执行记录、工具结果连在了一起。三条都有查阅价值，其中有两条会加进模型的消息历史。[完整录制](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L22)

| 行号 | 发生了什么 | 对下一次模型请求的影响 |
| --- | --- | --- |
| 9–11 | 写入系统消息、用户任务和运行时上下文 | 第一次请求包含这三条消息 |
| 12 | 写入初始 `request/header` | 提供模型配置和工具声明，消息条数仍是三条 |
| 15 | `assistant/message` 包含模型提出的 `read` | 历史多出一条助手消息，记录它要读哪个文件 |
| 16 | `tool/call` 记录框架开始执行该调用 | 这一行没有 `surfaceOp` 标记，消息历史里不会多出第二份调用 |
| 17 | `tool/result` 带回文件正文 `1: hello` | 历史多出一条工具消息。第二次请求共五条消息 |
| 18–22 | 第一步结束，第二步收到 `DONE`，回合完成 | 文件内容已在第二次请求里，无需再调用工具 |

**工具怎样把结果“交给”模型？** 执行器把结果追加到 Session。等到下一步，`buildRequest()` 从 `session.deriveMessages()` 取得当下可见的消息，和工具声明、生成参数等一起构造冻结的请求。工具无需把返回值直接传给模型，AgentLoop 也无需另外维护一份聊天数组。记录与请求之间只有一套选择消息的规则。[写入工具结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L252) · [选择可见消息](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts#L760) · [构造请求](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L714)

这里还有一个容易漏掉的约束。步骤开始时，`tools.resolve()` 解析出本步可用的工具集。同一份 `toolSet` 既用于组装给模型看的工具说明，也传给本步的 `tools.execute()`；步骤收尾时由循环释放。声明和执行因此有共同的依据，具体工具仍能在执行时检查权限。[取得工具集](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L295) · [执行工具](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576) · [释放工具集](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L386)

在**学习仓库**根目录运行，可以分别看到事件顺序和两次请求的消息差异。脚本使用随课录制，不需要模型密钥。

```sh
python3 labs/turn.py
python3 labs/request_inputs.py
```

第一个脚本给出 `1 个回合 · 2 个步骤 · 1 次工具调用 · 1 个工具结果`，第二个脚本列出两次请求各自的 3 条和 5 条消息。要核对工具声明和生成参数，可看上游的另一组测试：它从每次回复落定前的日志分别重建消息与请求头，再逐项比对适配器实际收到的请求。[请求重建测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L848)

## 谁决定停下来？

模型流正常结束后，`step()` 先把完整助手消息写进 Session。达到 token 上限时返回 `max-tokens`。其余情况下，它从消息内容里取出工具调用块，按下面三条路径返回。[实际分支](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L556-L587)

| 模型和工具做了什么 | `step()` 返回什么 | `turn()` 接下来怎么做 |
| --- | --- | --- |
| 回复只有文字 | `completed` | 检查是否有待处理的 `next-step` 输入 |
| 调用了普通工具，批次执行完成 | `null` | 进入下一步，让模型看到结果，即使用户没再说话 |
| 工具调用了 `exec.concludeTurn()`，批次标为结束 | `completed` | 同样检查待处理输入。没有新输入时可以结束回合 |

为什么 `step()` 返回 `completed`，外面还要再检查一次？因为工具执行、用户补充输入和插件的收尾动作可以发生在同一回合。准备结束且队列为空时，`turn()` 会先发出 `agent/turn-stopping`，等监听器返回后，再读一次队列。此时仍为空，才结束回合并写 `turn/end`。[收尾前的两次检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L390-L395) · [记录最终原因](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L398-L422)

两个上游用例把这条分支验证得很清楚。第一组让 `echo` 执行完调用 `exec.concludeTurn()`，得到 **1 次模型请求**，日志中仍有工具结果。第二组的 `finalize` 在请求收尾前，还用 `steer()` 追加了文本 `late steering`。这次得到 **2 次模型请求、1 个回合**，而且新增指令确实出现在第二次请求里。[第一组](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/loop.spec.ts#L1244) · [第二组](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/loop.spec.ts#L1266)

## 同样只收到半段文字，取消和重试会留下什么？

用户在生成过程中按停止时，循环已经有了流式片段，但可能还没有执行工具。此时它只收下非空的文字或推理文本，跳过所有尚未派发的工具调用。如果有可保留的内容，就把它写成带 `interrupted: true` 的 `assistant/message`；没有则只写 `assistant/attempt`。在上游用例里，文字 `reading the file` 留在会话里，半截 `read` 没有对应的执行记录。这样下一步就不会等一个从未启动的工具交结果。[中断时如何选内容](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/assembler.ts#L162) · [循环如何落日志](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L489-L520) · [取消测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/cancel.spec.ts#L699)

把故障点往后挪，结论就变了。完整的助手消息已经记录，工具执行到一半才出错，循环会在 `step/end` 前给缺结果的调用补一条错误结果。修复代码查看是否已有对应的 `tool/call`：没有开始记录，可以注明未开始；已经有开始记录但缺少结果，只能注明结果未知。例如一个写文件工具可能已经改了磁盘，单凭结果缺失无法判断是否适合重跑。[循环如何补齐结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L359-L384) · [两种修复结果](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/repair.ts#L157-L179)

再看另一条路径。一个测试让模型先输出 `doomed partial`，随后以服务错误结束。循环把失败的流写为 `assistant/attempt`，错误处理插件要求重试。第二次成功返回 `recovered`，会话中只有这一条正式的助手消息。**失败的流可供排查，只有采纳为消息的内容才会进入后续模型历史。** [重试决策](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L531-L553) · [失败与成功的两份记录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/cancel.spec.ts#L748)

为什么重试要回到 `step()` 顶部重新构造请求？设想第一次因历史过长被拒。上游用例让错误处理插件用摘要替换一段可见历史，再要求重试。仍然是同一步、同一批用户输入，第二次请求已经读到摘要；如果原样重发第一次的请求对象，这项修复就不会生效。代码用 `firstAttempt` 避免再次追加已采纳的用户输入，但每次都会重新读取 Session。[重试时重新组装](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L439-L469) · [同一步压缩后重试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L536)

## 用源码检验自己的判断

在装好开发依赖的**上游源码仓库**根目录运行下面两条命令。第一条验证主动结束和中途追加输入，第二条验证取消与重试。两组各选中两个用例，使用本地模拟模型。[上游开发环境](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/development.zh.md)

```sh
./node_modules/.bin/vitest run packages/core/agent-loop/tests/loop.spec.ts \
  -t 'a tool can conclude the turn|continues for steering that arrived'
./node_modules/.bin/vitest run packages/core/agent-loop/tests/cancel.spec.ts \
  -t 'cancel drops a half-streamed tool call|retry retains the failed attempt'
```

回到开头的 `read`。如果你要查“助手为什么又请求了一次模型”，先对照两次请求的回合号和步骤号。同回合、同步骤，查失败尝试与重试决定；同回合、不同步骤，查上一步的工具结果和待处理输入；如果回合号也变了，再查收件箱里是谁提交了新任务。这三条线索指向三个不同的循环。

[核心组件索引](deep-dive-roadmap.md) · [返回首页](../README.md)
