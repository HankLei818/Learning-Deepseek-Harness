# 第一课 · Web 和 Headless 如何共用同一个 AgentLoop

运行 `dsh web` 会得到浏览器界面，运行 `dsh headless` 可以处理一次性任务。两者共享基础 bundle 中的 AgentLoop；启动时选中的第二个 bundle，决定这套运行时对外提供 Web 服务还是一次性任务入口。[内置 profile 清单](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/util/official-bundles/src/bundles.ts#L10)

## 沿启动配置读三步

1. **找到应用组合。** `PROFILE_TEMPLATES` 中，`web` 选择 `dsh-base` 和 `dsh-web-app`，`headless` 选择 `dsh-base` 和 `dsh-headless`。这里也有一个例外：`sdk-minimal` 只选自己的 bundle。[Profile 定义](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/util/official-bundles/src/bundles.ts#L10)
2. **找到实际插件。** 在三个 bundle 的补丁文件里搜索注册项。共享的 `agent-loop` 出现在 base；`webserver` 和 `headless-runner` 分别出现在 Web 和 Headless 的配置中。[基础配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/base/cordis.patch.yml#L546) · [Web 配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/web-app/cordis.patch.yml#L194) · [Headless 配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/headless/cordis.patch.yml#L19)
3. **找到自己的改动会在哪里生效。** 启动器按顺序叠加 bundle、profile 自己的补丁、Harness home 的补丁和命令行 `--patch`。上游测试用两个 bundle 和一层用户配置连续修改同一行，可以直接对照最终值。[配置顺序](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/architecture.zh.md#L25) · [上游测试](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/boot/app-boot/tests/profile.spec.ts#L304)

## 五分钟源码实验

在含有下列提交的**上游源码仓库**根目录执行。命令直接读取 Git 对象，在其他分支也可以运行。上游仓库地址见 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)。

```sh
ref=4b399c39a6d1479cd84ca591b4d7c88e24d38a96
git show "${ref}:packages/util/official-bundles/src/bundles.ts" | sed -n '10,25p'
git grep -nE 'id: (agent-loop|webserver|headless-runner)$' "$ref" -- \
  packages/bundle/base/cordis.patch.yml \
  packages/bundle/web-app/cordis.patch.yml \
  packages/bundle/headless/cordis.patch.yml
```

第二条 Git 命令在该提交应命中三处：

| 配置文件 | 行 | 注册项 |
| --- | ---: | --- |
| `packages/bundle/base/cordis.patch.yml` | 546 | `agent-loop` |
| `packages/bundle/headless/cordis.patch.yml` | 19 | `headless-runner` |
| `packages/bundle/web-app/cordis.patch.yml` | 194 | `webserver` |

这个实验核对的是发行版的默认配置。如果要解释某台机器为什么多加载了一个插件，还要检查该机器的补丁。准备好上游项目依赖后，可以用 `pnpm dsh --profile web --dump-config` 查看本机合成的配置。[启动与配置说明](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/architecture.zh.md#L25)

## 接着追一个回合

共享的 AgentLoop 收到输入后，会记录 `turn/start`。试着沿着源码找到第一次 `step/start`、实际发送的模型历史，以及模型要求调用工具后的分支。下节课用这条路径解释为什么“一条用户消息”可以触发多次模型请求。[回合起点](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L332) · [请求使用的历史](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L718) · [工具调用分支](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576)
