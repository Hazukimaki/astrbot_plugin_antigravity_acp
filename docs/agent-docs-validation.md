# #16 文档改进验证记录

日期：2026-11-17。基线：`492d9b2`（当时发布基线 v0.7.0；合并时发布基线已升至 v0.7.1）；交付分支：`docs/agent-contracts-issue-16`。本次仅修改 Markdown；未改运行代码、配置、认证、ACP 或 WebUI 行为，没有部署或升级 CLI。

## 范围与证据

- 新增 [AGENTS.md](../AGENTS.md)、[架构导航](architecture.md)、[排障 SOP](troubleshooting.md)、[测试与交付规范](testing.md)，替换 README 历史混排的 Agent 段。
- 从当前源码及既有测试核对 #12 permission、#13 原始 schema、#14 system 过滤/429，以及拒绝归因、防重放、用量与监控权限。
- 更正历史更新日志中“已有输出不记候选”的说明：`test_content_429.py` 明确覆盖候选 `has_output=true`。未改遥测或冷却逻辑，不据候选推断 Google 上游根因。
- 历史计划/验收文件补时间与当前入口；旧记录中的测试结果不作为本次验证。

## 本次离线结果

环境：Windows、Python **3.12.10**、Node **v24.11.1**。当前 CI 配置使用 Node 22 与 Linux/Windows × Python 3.11/3.12；本机不能替代全部矩阵。

| 检查 | 结果 |
| --- | --- |
| `python -m unittest discover -s tests -v` | 共 246 项：242 通过、0 失败、0 错误、4 跳过、0 预期失败/意外成功；退出 0 |
| `node --test tests/setup.test.mjs` | 19 项，19 通过、0 失败/取消/跳过/todo；退出 0 |
| `python -m compileall -q main.py agy_provider tests` | 退出 0 |
| Markdown 渲染、本地链接/锚点与围栏 | 12 个修改/新增文档渲染为 HTML，186 个本地链接/锚点、19 个表格、12 个代码块检查通过；14 个文中测试模块均存在且包含测试 |
| `git diff --check`、仅文档范围核对 | 通过；12 个文件均为 Markdown，运行文件及配置未修改 |

渲染使用临时安装的 `markdown-it-py`（CommonMark + 表格/删除线），解析标题锚点与相对链接并生成本地 HTML；检查脚本/渲染产物/依赖均在系统临时目录，未加入插件或引入运行时依赖。围栏、details 与 HTML pre 配对检查通过；Mermaid 源码结构由作者核对，未用 GitHub 原生引擎渲染。

Python 跳过项（非通过项）：

1. `test_link_and_session_cleanup_preserve_official_file`：当前 Windows 文件元数据/链接权限不满足，失败分支另有覆盖。
2. `test_unsafe_file_and_parent_modes`：POSIX ownership/mode 检查。
3. `test_native_posix_socket_permissions_and_list`：Unix socket 需要 POSIX。
4. `test_official_4294_fallback_contract`：未提供可选官方宿主源码。

没有把跳过的官方源码契约测试算作当前环境已验证；其他防重放离线测试通过也不能替代它。

## 版本与验收限制

- metadata、README、AGENTS 和发布日志均以 **0.7.1** 为当前发布基线。文档任务期间 `main.py` 注册、transport clientInfo、mcp_bridge serverInfo 曾标 **0.6.1**；已在本版发布时统一为 0.7.1，验证记录保留当时发现。
- 当前提交 CI：以交付 PR 的 Checks 与提交 SHA 为准，远端结果另行报告；本报告的计数仅指上述本地运行，不以历史发布 CI 冒充。
- 本次未执行真实官方 CLI、模型生成、真实工具、宿主 iframe/HTTP 或生产部署验收；所有模型/宿主输入均为离线夹具。
- 本次 Markdown 检查不重新核实历史调研的外部项目结论；远程历史证据链接未逐一探测。GitHub 原生 Mermaid/页面视觉效果亦需审阅。
- #12/#13/#14 导航与约束由作者对照源码自审，**独立 Agent 审读、维护者验收仍待完成**，交付保持 Draft；不将其写成已通过、不自动合并或关闭 issue。

## 回滚

本次没有数据或运行行为迁移；回滚该文档提交即可。保留用户原工作区已有修改，无需删除配置、会话根或官方登录目录。
