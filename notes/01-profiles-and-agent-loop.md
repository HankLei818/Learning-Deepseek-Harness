# 第一课 · 网页和命令行怎样共用一套执行逻辑？

`dsh web` 启动网页，`dsh headless` 在命令行处理一次任务。两种模式都加载同一个 AgentLoop 插件，由它请求模型、调用工具，直到这一轮工作结束。

## 从启动配置里找答案

每种启动模式都有一份配置（**profile**），列出要加载哪些插件组合（**bundle**）。[默认启动配置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/util/official-bundles/src/bundles.ts#L10)

| 启动模式 | 共用的包 | 各自多加载的包 |
| --- | --- | --- |
| `web` | `dsh-base`，包含 `agent-loop` | `dsh-web-app`，启动网页服务 |
| `headless` | `dsh-base`，包含 `agent-loop` | `dsh-headless`，接收一次性任务 |

想看网页怎样接入，就读 Web 包。想看模型何时调用工具，就读两者共用的循环。[网页入口](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/web-app/cordis.patch.yml#L194) · [命令行任务入口](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/headless/cordis.patch.yml#L19) · [共享循环的注册位置](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/bundle/base/cordis.patch.yml#L546)

<details>
<summary>用 Git 找到这三个插件</summary>

在 **DeepSeek Harness 上游源码仓库**根目录运行。命令读取教程指定的提交，无需安装项目依赖。[获取上游源码](https://github.com/deepseek-ai/deepseek-harness)

```sh
ref=4b399c39a6d1479cd84ca591b4d7c88e24d38a96
git show "${ref}:packages/util/official-bundles/src/bundles.ts" | sed -n '10,25p'
git grep -nE 'id: (agent-loop|webserver|headless-runner)$' "$ref" -- \
  packages/bundle/base/cordis.patch.yml \
  packages/bundle/web-app/cordis.patch.yml \
  packages/bundle/headless/cordis.patch.yml
```

第一条 Git 命令会列出各模式加载的包。第二条应命中这三处注册位置，即 `base` 第 546 行的 `agent-loop`、`headless` 第 19 行的 `headless-runner`、`web-app` 第 194 行的 `webserver`。

</details>

[下一课 · 追踪一次工具调用](02-turn-and-tools.md) · [框架地图](../guide/architecture.md) · [返回首页](../README.md)
