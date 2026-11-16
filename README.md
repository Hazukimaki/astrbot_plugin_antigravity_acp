<p align="center">
  <img src="logo.png" width="160" alt="AstrBot Antigravity ACP" />
</p>

# AstrBot Antigravity ACP (`astrbot_plugin_antigravity_acp`)

![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Docker-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.29.4%2C%3C4.30-orange)
![Status](https://img.shields.io/badge/Status-v0.7.1-brightgreen)

> **当前正式版本 0.7.1（2026-11-17 发布）**。0.7.1 落地 429 内容相关的结构化标签过滤与候选归因遥测（`content_429_candidate`，不改冷却语义），并完成 WebUI 信息精简与运行监控三层重构（概览 / 详细统计 / 高级诊断，纯 SVG 可视化）。发布记录：Python 离线回归共 246 项（234 通过、12 跳过），前端 19 项通过；对应 CI 与生产实机范围详见 [CHANGELOG](CHANGELOG.md)。0.6.0 的生产实机验收（AstrBot 4.29.4 + AGY CLI 1.5.8，含真实 429 限流风暴下的快速中断与 fallback 兜底）见 [PR #9 验收记录](docs/pr9-acceptance.md)；实施范围与回滚方式见 [改进计划](docs/liftgate-hardening-plan.md)。

通过 Google 官方 `agy` 客户端内置的 ACP（Agent Client Protocol）协议，将 Antigravity 接入 AstrBot 作为日常对话模型使用。

> **WebUI 运行监控（v0.7.1 已发布）**：在 AstrBot 插件详情 →「首次设置」查看，按「运行概览 / 详细统计 / 高级诊断」分层展示会话池、近 24 小时用量、最近上下文采样、缓存和异常信息。监控仅供管理员读取本地快照，不额外请求模型；每实例最多保留最近 24 小时的 100 轮记录，进程重启后清空。缺少上游用量时显示「上游未报告」或「未知」，并非 Google 账号余额。详见 [0.7.1 更新日志](CHANGELOG.md)。

---

## 文档入口

安装与日常使用见下方教程。协助排障或开发的 Agent 先读 [AGENTS.md](AGENTS.md)，再按问题进入专题，无需加载全部历史资料。

- [安装与使用](#-给人类看的说明)
- [当前 Agent 契约摘要](#-给-agent-看的上下文)
- [架构与源码导航](docs/architecture.md) · [排障 SOP](docs/troubleshooting.md) · [测试与交付规范](docs/testing.md)

---

# 👤 给人类看的说明

## 1. 背景与定位

前阵子在 L 站看到大佬写的 `dsh-antigravity-acp`，直接调官方 CLI 走标准协议通信，逛了一圈 AstrBot 的插件市场，发现还没有类似的实现，就参考这个思路搬运并适配了一版

做这个插件最大的动力，其实是因为**我自己被 Google 杀号杀怕了**

折腾过反代、抓包提取 OAuth Token、或者接过各种野生号池的朋友应该都懂，账号风控是玄学，哪天睡醒号就没了。所以这个插件我金盆洗手：**只走官方客户端留的正常接口，不碰任何逆向和黑科技。** 

毕竟这样才能嫖满18个月的咖喱味pro，哈吉米rp这块真是太权威了 hhh

### 明确一下本插件的边界（做什么 vs 不做什么）

| ✅ 这个插件做什么 | ❌ 这个插件坚决不做什么（暂时） |
| :--- | :--- |
| 调用本机安装的官方 `agy` 客户端，走标准 stdio 管道通信 | **不做号池切换与多号轮询**：单实例只绑定当前机器登录的一个账号 |
| 把 AstrBot 的对话、图片和工具调用桥接给 `agy` | **不做上下文破限**：按历史预算规范化上下文，不塞破限提示词 |
| 提供 WebUI 向导，辅助完成官方登录和模型选择 | **不做客户端伪造**：不拦截篡改流量，不伪装其他 IDE 指纹 |
| 隔离运行目录，锁死 `agy` 自带的本地高危工具 | **不提取 OAuth Token**：文件桥只检查元数据并链接单个官方文件，内容与刷新由官方客户端管理 |

谷谷歌歌我都这样了总不至于封我吧？：）

---

## 2. 核心优势

Google 官方的命令行工具 `agy` 自带了一个 `agy acp` 子命令。本插件的作用就是在后台拉起你本机的 `agy`，把 AstrBot 的消息传过去，再把回复接回来。

相比传统的反代方案，这样做有几个实在的好处：
1. **官方客户端直连**：全程调用本机官方客户端完成通信，无第三方中转；这不构成账号安全或上游服务可用性保证。
2. **免 API Key、免额外部署**：不需要申请 API Key，也不用再单独起一个 HTTP 反代服务。只要本机 `agy` 登录了账号就能直接用。
3. **支持工具调用与多模态**：通过内置的本地 MCP 桥接，模型可以直接调用 AstrBot 里的插件工具（如 TTS 语音、查天气、代码沙箱等），也支持发图识图和调节思考深度（Reasoning）。
4. **锁死本地高危权限**：`agy` 本身是个能读写本地文件、执行终端命令的 Agent。为了防止机器人在群里被人用提示词注入把服务器搞崩，插件在启动 `agy` 时**强制关闭了它自带的所有本地文件与终端工具**。它只负责对话，工具执行全交由 AstrBot 自身的权限体系托管。

---

## 3. 安装与操作教程

### 第一步：安装官方 `agy` 客户端
在运行 AstrBot 的机器上（注意必须使用**运行 AstrBot 的同一个系统用户**），参考 [Google 官方文档](https://antigravity.google/docs/getting-started) 安装 `agy`。

安装完成后，在终端验证一下是否可用：
```bash
agy --version
agy acp --help
```
> 注：插件不会自动下载二进制文件。Windows 用户请确保使用的是原生 `agy.exe`，不支持 `.cmd` 或 `.bat` 包装脚本。

### 第二步：安装本插件
在 AstrBot WebUI 插件管理页上传 [主分支 ZIP 包](https://github.com/sl251/astrbot_plugin_antigravity_acp/archive/refs/heads/main.zip)，或者直接在 AstrBot 目录下克隆仓库：
```bash
git clone --branch main https://github.com/sl251/astrbot_plugin_antigravity_acp.git data/plugins/astrbot_plugin_antigravity_acp
```
安装后重载或重启插件。

### 第三步：完成首次设置（登录与选模型）
打开 **AstrBot WebUI → 插件 → Antigravity ACP → 首次设置**（也可以用管理员账号给机器人发 `/agy setup`）：

1. **检查环境**：页面会自动检测本机 `agy` 是否就绪。
2. **官方登录**：点击「开始官方登录」，复制生成的授权链接到浏览器完成登录，需要手动提交时只粘贴浏览器提供的单行授权码（当前不解析完整 localhost 回调 URL）。**注意不要把授权码发到公开群聊里。**
3. **保存模型**：登录成功后，页面会拉取当前账号实际可用的模型列表。选择你需要的模型和思考档位（`default` / `low` / `medium` / `high`），点击 **「保存并启用模型」**。

### 第四步：切换模型
使用页面提示的 `/agy use <provider_id>` 命令，或者直接在 AstrBot 的提供商列表里切换到刚刚保存的模型即可。

---

## 4. 注意事项（避坑必看）

- **国内机器配置代理**：
  如果机器直连 Google 不通，可以在插件配置中将 `proxy_mode` 设为 `custom`，并在 `proxy_url` 填入代理地址（如 `http://127.0.0.1:7890`）。该代理仅注入给 `agy` 子进程，不影响 AstrBot 里的其他国内模型。
  *(Docker 部署注意：容器内的 `127.0.0.1` 指向容器自身，请填写宿主机内网 IP 或 `host.docker.internal`。)*
- **开启工具调用（Tool Use）与识图（Vision）需要开两个开关**：
  这两个功能默认关闭。如果需要开启：
  1. 先在 **插件配置** 中开启 `enable_tools` 或 `enable_images`，保存并重载插件；
  2. 再去 AstrBot 的 **模型 / 提供商配置** 中，为对应模型勾选 `tool_use` 或 `image` 能力。两边同时开启才会生效。
  3. 从 `v0.5.1` 起建议通过提供商 `custom_extra_body.agy_tools_mode`（`chat` / `tools` / `inherit`）或在「首次设置」中选择模型角色做聊天/工具分流：纯聊天用 `chat`（绝不注入工具 schema，走精简 `astrbot-chat` 代理），需要工具的会话用 `tools`（仍受插件总闸 `enable_tools` 控制）。
- **只读诊断与成本统计**：
  管理员可执行 `/agy doctor` 进行无生成连通自检，或执行 `/agy cost` 查看各实例只读缓存复用、Token 统计与进程池摘要（不发送任何模型请求）。
- **关于连通测试与额度**：
  插件「首次设置」里的检测、登录、拉取模型列表均不消耗对话额度。但 AstrBot 模型页自带的“连通测试”会实际发送一条测试消息，消耗少量额度；另外，模型保存成功仅代表协议握手通过，实际对话还需单独验证模型、工具/图片上下文、请求预算、网络及上游状态，不能仅凭保存成功或报错文案判断额度。
- **运行范围与本机能力**：支持 AstrBot `>=4.29.4,<4.30`；0.7.1 对 4.30 已知宿主声明的识别不等于完整支持 4.30。若开启「使用电脑能力 → 本机环境」后仍出现 429，可暂改「不允许任何环境」。这是针对该现象的临时对照，不是所有 429 的通用修复。上游根因仍待确认，当前流程见 [排障 SOP](docs/troubleshooting.md)，历史对照见 [内容相关 429 调研](docs/429-prompt-investigation.md)。

---

## 5. 更新日志

*(详细技术变更见 [`CHANGELOG.md`](./CHANGELOG.md))*

- **v0.7.1（正式发布）**：429 相关宿主能力声明过滤扩展至 AstrBot 4.30 已知结构化标签，新增内容相关 429 候选遥测；WebUI 精简文案并重构三层运行监控与 SVG 可视化。246 项离线测试中 234 通过、12 项跳过，前端 19 项通过，生产实机验收完成。
- **v0.6.1（正式发布）**：交付 #11–#14 的插件侧修复与缓解，完善 MCP 权限分层、工具失败归因、数组 schema 宿主契约和本地能力声明过滤；CLI 拒绝后回喂问题及上游 429 根因仍未解决。
- **v0.6.0（正式发布）**：疑似上游压缩后终态退休、强错误提前中断、部分输出/工具失败防重放、Windows 认证 MCP 桥与 Job Object、成本分组和 CLI 能力诊断。组件精简实验默认关闭；动态 MCP 更新与 CLI 安装器未交付。
- **v0.5.3**：修复 #8：Windows 深路径宿主下首聊因 `MAX_PATH`（260 字符）被拒而报 `FileNotFoundError`；会话数据改用 Win32 扩展长度路径（`\\?\`），不再要求开启 `LongPathsEnabled`。
- **v0.5.2**：上架审查整改：运行时日志记录器统一为宿主 `astrbot.api.logger`，删除内置 `logging` 及 `ImportError` 回退分支；无功能与配置变更。
- **v0.5.1**：合并原计划 0.5.0 的安全会话复用、聊天/工具分流、`/agy cost` 统计和失败冷却，以及原计划 0.4.4 的 #4–#7 修复：模型列表来源绑定、配置自愈、微信 JPEG 尾部裁剪、上游重试告警过滤。0.5.0 与 0.4.4 均未单独发布；#4 的响应耗时问题仍在跟踪。
- **v0.4.3**：过滤上游 CLI 容量不足时输出的 `503 UNAVAILABLE` 告警行，纯告警轮次转为 `QUOTA` 交给 AstrBot fallback。
- **v0.4.2**：调整了启动策略，把环境预检放到后台静默执行，没装 `agy` 也不会卡住 AstrBot 启动了；清理了内部状态同步的冗余代码。
- **v0.4.1**：完善官方登录与设置页交互，清理冗余配置；当前授权输入边界见 [登录排障](docs/troubleshooting.md#启动登录与模型设置)。
- **v0.4.0**：仓库正式改名为 `astrbot_plugin_antigravity_acp`；新增了 WebUI「首次设置」页面，登录、拉模型列表、调思考档位终于不用手搓配置文件了。
- **v0.3.x**：把 `agy` 自带的本地文件和终端工具权限彻底锁死；补上了发图识图支持（加了防 SSRF 和尺寸限制）；重构了进程池，解决了异常退出时留僵尸进程的问题。
- **v0.2.x**：写了个本地 MCP 桥接器，让 `agy` 能正常调用 AstrBot 里的插件工具；兼容了 TTS 这类直接发消息不返回文本的插件。
- **v0.1.0**：看到 L 站的 DSH 插件后摸出来的初版，跑通了基础的 `agy acp` 对话流程。

---

# 🤖 给 Agent 看的上下文

先读 [AGENTS.md](AGENTS.md)。当前发布基线为 **v0.7.1**；仅支持 AstrBot **`>=4.29.4,<4.30`**、Python **3.11+**。本节只保留当前有效契约，历史实现和既有验收见 [CHANGELOG](CHANGELOG.md)。

| 当前契约 | 详细说明与证据入口 |
| --- | --- |
| 模型请求只走官方 `agy acp` stdio；每会话隔离目录，认证由官方 CLI 管理，不读取或记录凭据内容 | [架构与认证](docs/architecture.md)，[启动/登录排障](docs/troubleshooting.md#启动登录与模型设置) |
| CLI 内置文件、终端、web search/browser 继续拒绝；只有当前活跃 prompt 中已观测且匹配的快照 MCP 调用可获唯一 `allow_once`，宿主审批/校验/预算仍有效 | [MCP 权限与 schema](docs/architecture.md#mcp-的两层权限与两份-schema)，[#12 排障](docs/troubleshooting.md#empty权限拒绝与-12) |
| 模型 schema 适配与宿主原始契约独立；执行按原始 schema 校验，两者均参与工具指纹 | [#13 参数排障](docs/troubleshooting.md#tool_arguments-与-13) |
| 默认严格会话复用；已输出正文/思考或交接工具后失败禁止重试/fallback，避免重复副作用 | [会话与防重放](docs/architecture.md#会话历史与防重放) |
| system 仅过滤已知宿主能力声明；4.30 文案处理不是 4.30 宿主兼容证明；`content_429_candidate` 是候选遥测，不是上游根因 | [过滤与 429 边界](docs/architecture.md#system-过滤与-429-的证据边界)，[#14 排障](docs/troubleshooting.md#rate_limit--quota-与-14) |
| 检测/保存不等于真实生成；用量缺失保留未知；监控只读现有脱敏快照，不发模型请求 | [排障 SOP](docs/troubleshooting.md)，[实机验收分层](docs/testing.md#实机验收) |
| 工具/图片默认关闭，要求插件与宿主双开关；不支持音频、视频、PDF 或图片生成 | [关键配置](docs/architecture.md#关键配置)、[配置 schema](_conf_schema.json) |

开发时按 [测试与交付规范](docs/testing.md) 记录通过/失败/跳过、环境与实机边界。定位错误直接用 [故障 → 源码 → 测试索引](docs/architecture.md#故障定位索引)，无需先读旧施工书。

---

## 致谢与协议

- 灵感来源：感谢 L 站大佬的 `dsh-antigravity-acp` 插件提供的思路。
- 开源协议：详见 [`LICENSE`](./LICENSE) 与 [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md)。
- 免责声明：本插件仅作为本地官方 `agy` 客户端与 AstrBot 之间的协议适配器，与 Google 官方无关。请遵守 Google Antigravity 官方服务条款使用。
