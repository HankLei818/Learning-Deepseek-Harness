# DeepSeek Harness 深度版 · 组件原理路线

入门第 12 课写了一个工具。如果全局和当前 Agent 各注册一个同名工具，这个 Agent 会调用哪一个？从这个问题出发，深度版用 **6 个单元、24 讲**，一路读到会话中断后的恢复。本文是课程规划。每讲都给出可先读的实现、上游测试和预期现象。[回顾入门第 12 课](../notes/12-tool-plugin.md)

**怎样读一讲**　先预测结果，只改一个条件，比较两次记录，再回源码找做决定的那一处。入门讲过“压缩后仍能看原文”，深度第 12 讲接着问“如果一刀切在工具调用和结果之间，模型会看到什么”。所有源码与测试都固定在[同一上游版本](https://github.com/deepseek-ai/deepseek-harness/commit/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)。

**怎样选路线**　第一次读，按 01–24 顺序。想写工具插件，从 01–03 到 08，再读 13–16。想做会话或客户端，读 05–06、09–12，再接 21–24。想研究多 Agent，先读 01、09 和 15，再连读 17–20。

## 一 · 插件怎样组成一个 Agent

Cordis 用 `ctx` 给插件提供服务。插件用 `inject` 声明依赖，所需服务就绪后才启动。这四讲追踪一项注册从加载到卸载的全过程。[Cordis 的插件和服务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/cordis-primer.zh.md)

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 01 · 同名工具，究竟调用哪一个？ | 在全局和 Agent 各注册一个 `bash`。对照两次调用的返回值，释放 Agent 的作用域，再查看局部工具清单。 | [工具注册](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L128) · [作用域测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/tests/scoped.spec.ts#L93) |
| 02 · 配置里有插件，启动后为什么看不到？ | 在同一个 profile 配置里放入两个插件，其中一个声明了不兼容的运行时版本。记录谁被导入、谁执行了初始化，再看 Agent 的 preset 怎样处理被禁用的条目。 | [启动检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/boot/app-boot/src/compatibility-preflight.ts) · [装配测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/boot/app-boot/tests/compatibility-preflight.spec.ts#L77) |
| 03 · 一个插件怎样接管模型调用？ | 沿 `llm/stream` 跟一次 `next()`。再让监听器自己产生回复事件流，跳过 `next()`。即使没有为该模型注册适配器，会话也能收到固定回复。 | [模型服务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L1160) · [接管测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L463) |
| 04 · 热更新失败，旧插件还能工作吗？ | 在启用热更新的配置中替换一个运行中的插件。分别让新版本导入成功和导入失败，观察下一次调用落在哪个版本。 | [热更新](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/boot/hmr/src/index.ts) · [替换测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/boot/hmr/tests/modules.spec.ts#L178) |

## 二 · 一轮对话怎样执行

从 AgentLoop 跟到模型适配器和工具执行器。读完能从会话记录分清用户取消、连接中断和工具正常完成。

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 05 · 用户按下停止，半条回复怎么收尾？ | 让模型先输出文字，再输出半截工具调用，随即取消。查看会话保留了哪些文字，以及工具有没有执行。 | [流式回复](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/assistant-stream.ts) · [取消测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/cancel.spec.ts#L699) |
| 06 · 只给你日志，能还原模型收到的请求吗？ | 让工具返回一次结果，再修改系统提示和生成参数。用每次发送前的日志分别重建请求，逐项对照适配器收到的消息、工具定义和参数。 | [请求组装](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts) · [重建测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/request-reconstruction.spec.ts#L848) |
| 07 · 模型返回空回复和半截回复，都会重试吗？ | 让本地端点分别返回合法的空回复和中途结束的流。前者触发重试，后者默认以 `STREAM_CLOSED` 结束。对照请求次数与会话中的尝试记录。 | [重试策略](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-retry/src/index.ts) · [传输测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-retry/tests/transport-recovery.spec.ts#L168) |
| 08 · 两个工具倒序完成，模型先看到谁？ | 让两个可并行工具按相反顺序返回，检查日志仍按调用顺序写入结果。再插入需要独占执行的工具，观察并行在哪一步停下。 | [批量调度](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts) · [顺序测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/tests/tool-calls.spec.ts#L239) |

## 三 · 会话怎样保存和重建

同一份日志可以生成不同的视图。先追踪一批事件何时生效，再研究磁盘写入、状态恢复和模型可见的历史。

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 09 · 一批事件的最后一条无效，前面几条算数吗？ | 先成功提交一批事件，再让最后一条校验失败。对照日志长度和模型可见消息，确认第二批没有留下半次更新。 | [Session 追加](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts) · [整批提交测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/tests/append.spec.ts#L188) |
| 10 · 两个进程同时打开一份会话，谁能写？ | 第一个进程持有 JSONL 写锁时，第二个进程申请写入会失败。让持锁进程退出，再观察第二个何时能接手。 | [写锁](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session/session-persistence-jsonl/src/lease.ts) · [双进程测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session/session-persistence-jsonl/tests/lease.two-process.e2e.ts#L35) |
| 11 · 重开长会话，哪些事件需要重算？ | 投影是从日志算出来的状态。将全量回放与从检查点续算的结果对照，再改变投影的版本，观察它何时回到日志起点。 | [投影注册表](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session/session-projection/src/index.ts) · [恢复测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session/session-projection/tests/registry.spec.ts#L777) |
| 12 · 压缩为什么不能从任意一条消息切开？ | 让保留区的起点落在工具调用与结果之间，观察切点移动。再让摘要生成失败，对照压缩前后模型看到的消息和日志中的失败记录。 | [压缩区间](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/src/region.ts) · [切点测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L884) |

## 四 · 工具怎样执行

读工具源码先认清三个角色。以 `read` 为例，文件工具接收模型参数，`ctx.fs` 定义可以做哪些文件操作，`fs-local` 实现本机读写。沿着这条线，才能找到一次拒绝或超时究竟发生在哪一层。[文件工具](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/src/index.ts#L24) · [文件服务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/fs/src/index.ts#L104) · [本机实现](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/fs-local/src/index.ts)

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 13 · 文件读完后被别人改了，还能直接写吗？ | 显式启用读后写保护。读取文件、从外部修改、再让工具覆盖，会得到 `FS_STALE_VERSION`。重读后再写，核对最终内容。 | [文件观察策略](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/fs-observation-policy/src/index.ts) · [读写测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/fs/tool-fs/tests/integration.spec.ts#L131) |
| 14 · Shell 的超时从哪一刻开始算？ | 给前台命令 100 毫秒，让沙箱准备耗去 60 毫秒。推进测试时钟，观察剩余 40 毫秒用尽时，子进程收到什么信号。 | [沙箱与 Shell](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/bash-sandbox/src/index.ts) · [时限测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/bash-sandbox/tests/foreground-timeout.spec.ts#L96) |
| 15 · 连续两次运行代码，什么时候能共用变量？ | 把 PTC 代码运行时设为内存持久模式（`persistent-in-memory`），定义一个变量。用同一个状态所有者再读一次，然后换所有者、释放原状态分别重试，记录三次结果。 | [PTC 执行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/ptc-runtime/ptc-runtime-node/src/execution.ts) · [状态隔离测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/ptc-runtime/ptc-runtime-node/tests/persistent.spec.ts#L164) |
| 16 · MCP 重新连接后，旧通知还能改工具列表吗？ | 让模拟的外部工具服务断线再连上，然后发出旧连接上积压的通知。检查新工具仍可调用，工具列表只接受当前连接的更新。 | [MCP 连接代次](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/mcp/mcp-client/src/generation.ts) · [重连测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/mcp/mcp-client/tests/reconnect.spec.ts#L810) |

## 五 · 多个任务怎样协作

一个后台任务、一个子 Agent、一张共享任务板、一段工作流，各自保存不同的状态，也有不同的结束条件。

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 17 · 调用方停止等待，后台任务结束了吗？ | 先取消一次等待，观察任务继续运行。再请求停止任务，检查它占用的并发名额什么时候才释放。 | [后台任务](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/jobs/jobs-local/src/index.ts) · [任务生命周期测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/jobs/jobs-local/tests/jobs.spec.ts#L284) |
| 18 · 父 Agent 正在回答，子 Agent 能继承到哪一句？ | 在父回合进行中执行 `fork`。把子会话的起始记录与父日志逐条比对，找出最后一个已完成回合的结束事件 `turn/end`。 | [进程内 fork](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/subagent/subagent-fork-in-process/src/index.ts) · [继承范围测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/subagent/subagent-fork-in-process/tests/fork-source.spec.ts#L82) |
| 19 · 为什么任务板要同时检查负责人和版本号？ | 让甲先领任务，乙用最新版本再领，收到“已被领取”。让甲拿领取前的旧版本提交完成，收到 `TEAM_TASK_STALE_REVISION`。用这两个结果区分归属冲突和过期更新。 | [共享任务板](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/team/agent-team/src/task-board.ts) · [领取与更新测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/team/agent-team/tests/team.spec.ts#L537) |
| 20 · 工作流怎么收集两个子 Agent 的结果，又由谁收尾？ | 让第一个子任务返回文本，第二个按指定字段给出判断。核对脚本的返回值，再查看运行中的 Agent 清单，确认两个子 Agent 已释放。 | [工作流宿主](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/workflow/workflow-ptc/src/host.ts) · [跨组件测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/workflow/workflow-ptc/tests/integration.spec.ts#L31) |

## 六 · 网页和 SDK 怎样看到同一份会话

追踪请求怎样进入 Host（运行 Agent 的进程），以及 Host 的记录怎样到达浏览器和 SDK。最后独立诊断一次中断。

| 讲次与问题 | 动手时观察什么 | 实现与测试 |
| --- | --- | --- |
| 21 · 网页能列出会话，就能读所有会话吗？ | 给测试访客列出会话的资格，只共享其中一个会话。通过 Typert RPC 网关请求列表，再分别读取两份会话的投影，核对可见范围。 | [网关访问检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/gateway/src/access.ts) · [会话授权测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/session-controller/tests/remote-access.host.spec.ts#L186) |
| 22 · 浏览器掉线再连，怎么避免少一条或多一条？ | 模拟断线后用新连接补读，并重发一段重叠记录。检查客户端用补回的页面更新视图，忽略随后重放的重复条目，最后显示的序号连续且不重复。 | [客户端记录流](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/gateway/src/client/journal-stream.ts) · [补读测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/api/gateway/tests/journal-stream.client.spec.ts#L440) |
| 23 · SDK 发出的命令已返回，为什么还要等模型？ | 让一个命令触发模型回复，同时执行另一个只改变状态的命令。核对每次 `query` 等待的工作和返回的结果。 | [SDK 等待逻辑](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/sdk/server/src/query-activity.ts) · [并行命令测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/sdk/server/tests/query-activity.spec.ts#L83) |
| 24 · 综合实验 · 一轮对话中断，重启后从哪一轮继续？ | 用一份末尾只有 `turn/start` 和 `step/start` 的记录，通过 SDK 恢复并发送下一句。交付一张事件表，标明第 2 回合何时记为 `interrupted`，第 3 回合何时记为 `completed`。 | [会话修复](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/repair.ts) · [SDK 恢复测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/sdk/server/tests/resume.spec.ts#L303) |

## 从第 01 讲开始

可以拿入门版写过的插件做练习。先跟 `ToolsService.register()` 找到工具存到了哪一层，再看 `schemas()` 如何得到 Agent 的工具清单，最后跟到 Cordis 怎样回收这次注册。[工具注册与查询](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L128) · [作用域存储](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/scope/src/store.ts#L153) · [Cordis 的 effect](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/vendor/cordis/src/fiber.ts#L443)

在**上游源码仓库**装好开发依赖后，从根目录运行下面的命令。两个用例都用本地测试工具，无需模型密钥。[上游开发环境](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/development.zh.md)

```sh
./node_modules/.bin/vitest run packages/core/tools/tests/scoped.spec.ts \
  -t 'scoped shadows global|disposing the scope unwinds'
```

第一个用例中，在 Agent 内调用 `bash` 得到 `restricted-bash`，从全局调用得到 `global-bash`。第二个用例释放作用域，再查刚才注册的局部工具 `mine`，结果是 `undefined`。两例都通过时，终端会显示 `2 passed`。

## 主线以外，按组件选读

| 读到哪一讲 | 可以继续追的问题 | 上游入口 |
| --- | --- | --- |
| 02 · 装配 | 怎样给不同 Agent 选择预设？已安装的技能何时出现在会话的技能目录里？模型怎样按名加载？ | [Preset](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/preset/README.zh.md) · [Skill](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/skill/README.zh.md) |
| 06 · 模型请求 | 工作区说明怎样进入一次请求？用户登录后，哪个组件提供调用模型所需的凭据？ | [Context](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/context/README.zh.md) · [Account](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/account/README.zh.md) · [Credentials](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/credentials/README.zh.md) |
| 10–12 · 会话数据 | 旧版 JSONL 怎样生成新版并保留原件？旧会话怎么检索？附件和超长工具输出各存在哪里？ | [升级与重开测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session/session-persistence-jsonl/tests/v3-restart-migration.spec.ts) · [Session Query](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/session-query/README.zh.md) · [Attachment](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/attachment/README.zh.md) · [Spill](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/spill/README.zh.md) |
| 13–16 · 工具执行 | 谁处理人工审批？切到 SSH 后文件和命令在哪台机器执行？持久终端怎样区分等输入和进程退出？ | [审批](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/approval.zh.md) · [SSH](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/ssh/README.zh.md) · [Terminal](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/terminal/README.zh.md) |
| 16 · 外部能力 | 做一次代码跳转、网页检索或文档转换，各需要什么服务？浏览器与桌面操作由哪个提供方执行？ | [LSP](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/lsp/README.zh.md) · [Web](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/web/README.zh.md) · [Document](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/document/README.zh.md) · [Browser Use](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/browser-use/README.zh.md) · [Computer Use](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/computer-use/README.zh.md) |
| 17–20 · 协作 | 计划等待谁确认？同一会话的目标怎样延续？定时跟进由谁唤起？ | [Plan](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/plan/README.zh.md) · [Goal](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/goal/README.zh.md) · [Schedule](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/schedule/README.zh.md) |
| 21–24 · 应用接入 | 会话记录怎样变成网页上的卡片？外部程序可以用哪种协议接入？ | [会话界面](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/conversation.zh.md) · [Python SDK](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/python/sdk/README.zh.md) · [ACP](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/acp/README.zh.md) |

其他组件可从上游分组索引查找。选读涉及的实验性实现以上游标记为准，例如持久终端服务和模型可调用的实验版终端工具分别归在两个组。[全部组件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/README.zh.md) · [实验性组件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/experimental/README.zh.md)

## 写作与发布顺序

1. **先写 01–04。** 从一个已会编写的工具切入，让读者能独立解释注册、选用、卸载和替换。第 01 讲作为后续样章。
2. **再写 05–12。** 用请求和会话日志串起两单元。阶段练习给一份短日志，让读者标出模型何时取得工具结果、哪些消息在压缩后仍可见。
3. **最后写 13–24。** 从单个工具推进到后台任务、多 Agent 和客户端。以第 24 讲的中断恢复收尾，读者交付一张能用源码解释的事件表。

[返回入门课程](../README.md) · [框架地图](architecture.md)
