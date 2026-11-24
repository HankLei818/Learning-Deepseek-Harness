# LLM 模型服务 · 一句 hi 怎样变成一次模型调用？

上游有个很小的实验。程序向 `ctx.llm.stream()` 交一条文本 `hi`，指定提供方 `deepseek-official`、模型 `deepseek-v4-pro`。本地 HTTP 服务器收到 JSON，逐段返回 `hello`。在调用方这头，回复被组装成一条助手消息，结束原因是 `stop`，用量是 3 个输入 token 加 1 个输出 token。服务器的回答是预设的，走过的运行时、适配器、HTTP 和流解析都是真实代码。[调用与断言](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/runtime.spec.ts#L379-L408) · [本地服务器发送的六个事件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/mock-server.ts#L29-L37)

**运行时选定适配器和参数，适配器把请求发到端点，再把返回的事件翻译成统一格式。** 用服务器收到的请求和调用方拿到的回复，可以逐段检查这条链路。

## 一、先确定由谁回答，再确定这次调用的参数

`provider` 和 `model` 回答不同的问题。运行时用 `deepseek-official` 在注册表里找到适配器，再让适配器解析具体的 `deepseek-v4-pro`。这里的 API Key 插件负责把官方路由接到 DeepSeek 适配器；插件卸载时会撤掉它注册的路由。提供方自己的接入代码掌握凭据和连接配置，AgentLoop 只选择路由、模型及本次请求的参数。[官方路由注册](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek-api-key/src/index.ts#L92) · [挂载适配器](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/host.ts#L83) · [运行时注册表](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L383-L399)

为什么要有 `prepareCall()`？假设准备请求时，路由指向服务器 A，默认输出上限是 12；准备完成后，管理员把地址改成 B，上限也改成 24。如果声明上限和实际发送各自去读一次配置，一个请求就可能混用两套值。DeepSeek 适配器在准备时取得一份连接配置，读取模型能力，并让发送函数捕获这份配置。上游用两个本地端点验证：用此前准备的适配器调用，A 收到的仍是 `max_tokens: 12`；重新发起的调用到达 B。[适配器怎样绑定连接](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/adapter.ts#L39-L58) · [双端点实验](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/prepared-call.spec.ts#L43-L59)

上面的实验直接使用适配器准备的连接。再往外一层，`ctx.llm.prepareCall()` 会固定适配器注册、重试策略和已解析的生成参数。直接调用 `ctx.llm.stream()` 时，这些信息在流即将交给适配器时解析；AgentLoop 会提前取得运行时的准备句柄，让写进 Session 请求头的参数与稍后发出的参数一致。**运行时句柄只能成功发起一次调用。** 拿同一句柄重复发送，或把已经确定的模型换成另一个，都会收到 `INVALID_PREPARED_CALL`。[两种调用入口](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L1045-L1075) · [准备与发送检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L942-L996) · [配置变化对照](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/tests/service.spec.ts#L1008-L1040)

## 二、服务器究竟收到了什么？

回到 `hi`。调用者传给服务的是 Harness 消息对象，只显式指定模型和消息。DeepSeek 适配器把历史与参数交给 `serialize()`，组装 Messages 请求，再通过 `fetch` 向模型端点发出 POST。下面是这次请求中最值得对照的字段。[请求序列化](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/serialize.ts#L118-L165) · [HTTP 发送](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/adapter.ts#L126-L160)

| 请求字段 | 这次发送的值 | 它来自哪里 |
| --- | --- | --- |
| `model` | `deepseek-v4-pro` | 调用者选择的目标模型 |
| `messages` | 一条 `user` 消息，文本块内容为 `hi` | 本次传入的消息历史 |
| `max_tokens` | `256000` | 该固定版本与模型配置解析出的输出上限 |
| `output_config.effort` | `high` | 此模型配置的推理强度 |
| `stream` | `true` | 适配器要求端点逐段返回结果 |

有工具参与时，翻译多了一层。以随课的真实读文件录制为例，模型提出了 `read`，工具随后返回 `hello`，两条记录通过调用 ID 配对。下一次发给 DeepSeek 时，适配器把这次请求编码成助手消息里的 `tool_use`，把结果编码成用户角色消息里的 `tool_result`，并在 `tool_use_id` 填回原 ID。即使两个消息相邻，ID 对不上也会触发 `INVALID_REQUEST`。这样提供方能区分工具输出与用户亲手输入的文字。[读文件会话的第 15–17 行](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L15-L17) · [助手工具调用的编码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/serialize.ts#L27-L37) · [调用与结果的配对检查](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/serialize.ts#L118-L146)

这也解释了为何 DSH 分开保存助手正文和 `replayState`。正文保留文字、工具名和调用参数；附带的回放信息可以存放某个模型协议要求的块标记和签名。再次发送前，运行时先检查历史路由是否仍由同一适配器实例负责，DeepSeek 再核对回放版本、块顺序与模型。上游用一份含未知版本标记的旧工具记录做了两次 HTTP 调用：两次调用都正常结束。测试在第一次请求体里核对了 `bash` 调用、原调用 ID 和 `TERMINAL_OK` 结果，还确认旧消息保持原样，两次合计只报告一次降级提示。[运行时筛选](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm/src/index.ts#L1008-L1022) · [原生回放校验](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/replay.ts#L33-L64) · [端点实际收到的请求](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/adapter.spec.ts#L586-L623)

## 三、收到 hello 以后，为什么还要继续读？

HTTP 200 只表示端点已经接受请求。在这个实验里，`hello` 早于结束信号到达。适配器先用 `parseSse()` 将字节流拆成完整的服务端推送事件（SSE），再用 `translate()` 将提供方事件翻译成 Harness 的 `StreamChunk`。最后，调用方的 `BlockAssembler` 按块编号拼起文本、工具参数和用量。[解析 SSE 帧](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/sse.ts#L8-L27) · [翻译成 Harness 事件](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/translate.ts#L111-L176) · [调用方的组装代码](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/assemble.ts#L18-L30)

| 本地服务器发出的事件 | 运行时这一侧得到什么 |
| --- | --- |
| `message_start` | 记录初始用量，输入 3 个 token |
| `content_block_start` → `content_block_delta` → `content_block_stop` | 打开文本块、接收 `hello`、封闭该块。此时已经可以显示文字 |
| `message_delta`，含 `end_turn` | 记下结束原因与输出用量 1 |
| `message_stop` | 校验后交付统一的 `usage` 与 `finish(stop)`，调用方才能确认回复完整 |

工具参数也可以分片。另一个测试让端点格式的事件先带来 `{"path":`，稍后才带来 ` "a"}`。适配器按块追踪这些片段，组装结果保留调用 ID、名称 `read` 和完整参数；`tool_use` 结束原因转成 `tool-calls`。这个用例只检查分片能否拼成一个工具调用。实际文件工具要求参数名为 `file_path`，工具函数和文件访问在下一段执行链上。[分片和组装的断言](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/tests/stream.spec.ts#L15-L34) · [停止原因映射](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/translate.ts#L97-L103)

## 四、正文为空和连接提前结束，会作同样处理吗？

把成功端点换成两个会出错的本地端点，差别就清楚了。两例都运行了实际的 DeepSeek 适配器与 `llm-retry` 插件，也都预备了一个能成功的后续响应。[测试中的提供方与重试配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-retry/tests/transport-recovery.spec.ts#L51-L79)

| 端点行为 | 协议层的判断 | 这组配置实际做了什么 |
| --- | --- | --- |
| 给出 `end_turn` 和 `message_stop`，对应 `stop`，内容块数量为零 | `EMPTY_RESPONSE` | 端点收到两次内容相同的请求，Session 记录一次 `llm/retry`。最终助手消息只有 `recovered from empty` |
| 已发出部分文字，随后 HTTP 响应结束，缺少 `message_stop` | `STREAM_CLOSED` | 端点只收到一次请求，Session 留下失败的 `assistant/attempt`，没有提交助手消息 |

这项分工决定了该从哪里排错。缺少 `message_stop` 去检查原始事件流；错误已被识别而没有重试，查看提供方重试策略和 `llm-retry` 对错误码的判断。即便用户已经在屏幕上看到文字，协议仍可能以失败收尾。[完整、空与提前结束的判定](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-deepseek/src/translate.ts#L150-L179) · [按策略决定是否重试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-retry/src/index.ts#L192-L225) · [请求次数与会话记录的对照](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/llm/llm-retry/tests/transport-recovery.spec.ts#L168-L217)

## 复现这条链路

在装好开发依赖的**上游源码仓库**根目录运行下面的命令。第一条选中一个成功调用，第二条选中上表的两个失败分支。实验使用本机环回地址和测试凭据，无需在线模型密钥。[上游开发环境](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/development.zh.md)

```sh
./node_modules/.bin/vitest run packages/llm/llm-deepseek/tests/runtime.spec.ts \
  -t 'streams a text generation end to end through the assembler'
./node_modules/.bin/vitest run packages/llm/llm-retry/tests/transport-recovery.spec.ts \
  -t 'retries a wire-valid content-less completion|exposes a clean partial EOF'
```

想把模型服务和执行器连起来看，可以运行[第 12 课的本地工具实验](../notes/12-tool-plugin.md)。第一次请求让本机端点看见工具声明，端点返回一次工具调用；第二次请求携带真正的执行结果，端点把它作为最终答复返回。[端点如何核对工具结果](../labs/tool_plugin/run.py) · [继续读 Tools](tools.md) · [五篇组件原理](README.md)
