# Session 原理 · DSH 怎样记住，又怎样想起

你告诉助手“我的验收暗号是青梅 7301”。关掉程序，重开原会话再问，助手可能答得出来。换一个新会话也问同一句，它还能答出来吗？要解释这两个结果，先找出**哪条记录把暗号带进了这一次模型请求**。

## 重开原会话，模型怎样接上上一句

默认配置把每个 Session 的事件追加到本地 JSONL 文件。日志记录的事情比模型需要读的多。譬如框架要记下“工具开始执行”，模型下一次请求需要的是自己刚提出的工具调用和工具返回的内容。Session 维护一份当前的消息视图，源码里叫 `surface`。标为 `surfaceOp: "append"` 的消息可以在视图末尾增加一项。AgentLoop 组装请求时通过 `deriveMessages()` 取得这份历史。[持久化配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/base/cordis.patch.yml#L142-L145) · [从视图生成消息](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/session/src/index.ts#L778-L802)

在教程仓库运行 `python3 labs/request_inputs.py` 就能看到差别。第一次请求有三条消息，来自录制的第 9、10、11 行。第二次有五条，多出来的是第 15 行的助手工具调用和第 17 行包含 `hello` 的结果。第 16 行也记录了 `tool/call`，却没有再给模型增加一条消息。你可以对照原始记录中的 `surfaceOp` 字段逐行核对。[离线实验](../labs/request_inputs.py) · [完整录制](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/fs-read/session.v4.jsonl#L8-L20)

重开时，SDK 用原 Session ID 找到这份历史。上游测试先说 `remember kiwi`，关闭旧宿主，再在新宿主恢复同一个 ID。恢复结束时，模型适配器还没有收到调用。等用户问 `what did I say?`，发出的请求里才同时出现旧问题、旧回复和新问题。读者能直接核查请求，哪怕模型最终答错，也知道旧内容已经送达。[恢复实验及请求断言](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/sdk/server/tests/resume.spec.ts#L265-L299)

## 日志里还在，为什么模型可能忘了

上下文压缩可以改变当前视图。看一次真实录制的第 24、25 行。前一行 `compaction/summary` 保存摘要及覆盖范围。后一行是携带摘要的 `user/message`，它的 `surfaceOp` 要求把视图中从 `startSeq: 8` 到 `endSeq: 9` 的节点替换掉。这里的数字是事件序号，读源码时要与文件行号区分。下次请求读取替换后的视图，原事件仍在日志里。如果暗号在被替换的消息里，而摘要漏掉了它，用户翻历史还能找到暗号，模型这一轮却可能拿不到。[压缩录制](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/snapshots/session/compaction-recovery/session.v4.jsonl#L23-L26) · [摘要与替换分别写入](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/src/region.ts#L497-L515)

压缩还有两个值得核对的结果。保留区切在工具调用和结果之间时，算法会调整切点，把两者留在一起。摘要生成失败时，框架会记录失败，本次摘要替换不会生效。这让后来排查问题的人既能找到失败原因，也能核对当时交给模型的消息。[调用与结果配对](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L884) · [摘要失败测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L1241)

## 新会话怎样获得旧会话里的信息

普通新会话有自己的日志。如果在网页里显式引用会话 A，引用插件会在处理新输入时读 A 的当前视图，提取用户和助手的可见文本，按预算生成一份快照，把它作为一条额外消息放在本次提问之后。快照会标明引用内容来自另一会话，仅供参考。之后 A 又增加的消息，也不会改写已经放进 B 的那份快照。[引用消息怎样进入请求](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/context/session-reference/src/index.ts#L168-L192) · [引用提取哪些内容](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/context/session-reference/src/projection.ts#L39-L58)

如果只知道关键词，可以走会话检索。基础配置允许精确读取已知会话，SQLite 全文搜索默认关闭。部署启用全文索引后，程序可以按词查历史；若希望模型自己发起搜索，还可以挂载实验性的会话查询工具。搜到的内容要通过引用或工具结果进入新会话，模型才能使用。启用索引本身不会把命中内容自动填入每次请求。[默认检索配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/base/cordis.patch.yml#L153-L165) · [面向模型的查询工具](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/experimental/tool-session-query/README.zh.md#L26-L32)

## 跨会话长期记忆，谁写入、谁召回

如果希望多个独立会话共用一条偏好，可以另接记忆服务。这个版本提供 Memorix、MCP Reference Memory 和 Engram 三份默认关闭的参考配置。DSH 通过 MCP 发现服务的读写工具；记什么、存到哪、用什么算法找，由所选服务实现。以 MCP Reference Memory 为例，它把实体、关系和观察写入本地知识图谱，按子字符串查找。这里甚至无需向量数据库。[第三方服务的职责](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/user/guide/mcp-memory.zh.md#L5-L31) · [参考实现的检索方式](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/user/guide/mcp-memory.zh.md#L46-L55)

**怎样判断真的发生了跨会话召回？** 先任选一份配置，并让两个会话使用同一处提供方存储。用自己临时编的唯一暗号做下面的对照。[上游实验步骤](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/user/guide/mcp-memory.zh.md#L74-L82)

1. 在会话 A 说“记住我的验收暗号是……”。检查日志里有记忆写入工具的成功结果。助手口头说“记住了”还不足以判断写入成功。
2. 新建独立会话 B，提问中只说“查一下我的验收暗号”。保持输入里没有暗号，也不引用 A。检查召回工具的结果是否带回原值，以及随后回复是否用对这个值。

本篇已用固定版本的测试核对了同会话恢复、压缩切点、摘要失败和引用快照。最后的 A/B 步骤是供接入真实第三方服务后运行的验收方法。

[回到构造请求的 AgentLoop](agent-loop.md) · [五篇组件原理](README.md) · [返回首页](../README.md)
