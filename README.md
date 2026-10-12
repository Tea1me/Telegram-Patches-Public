# Telegram Desktop v7.3.1 补丁版构建

本分支将本仓库的五项客户端补丁适配到 Telegram Desktop 上游 **v7.3.1**，并提供 Windows x64 便携版构建工作流。它不是 Telegram 官方发行版。

- 上游标签：[`v7.3.1`](https://github.com/telegramdesktop/tdesktop/releases/tag/v7.3.1)
- 固定源码 commit：[`6fed91ffab9861771a75f29df65031b3c80b6941`](https://github.com/telegramdesktop/tdesktop/commit/6fed91ffab9861771a75f29df65031b3c80b6941)
- 补丁目录：[`patches/v7.3.1/`](patches/v7.3.1)
- 目标：Windows x64、Qt 6.11.2、Release 或 Debug 便携构建

## 补丁内容

| 补丁 | 客户端改动 |
| --- | --- |
| `0001` | 不显示赞助消息和赞助顶栏入口。 |
| `0002` | 放宽受保护消息的选择、复制和媒体保存限制；保留限时媒体与扩展付费媒体的保存检查。 |
| `0003` | 将邀请预览到期时间改为不在客户端到期。 |
| `0004` | 将普通与 Premium 客户端账号槽位上限改为 255。 |
| `0005` | 在实验设置中增加关闭 Stories 的选项，默认关闭该选项；启用后需重启客户端。 |

这些改动只修改客户端行为，不能变更服务器端的权限、订阅状态或限制。邀请链接、账号数、受保护内容等仍可能受服务器规则约束。

### v7.3.1 保存行为说明

上游 v7.3.1 发布说明包含修复“受限媒体进入 Downloads”的改动。本分支的 `0002` 会放宽相关客户端限制，因此和这项上游行为存在直接的兼容性取舍。补丁仍保留限时媒体及扩展付费媒体的检查；如果你需要保持上游对其他受限媒体的默认保护行为，请不要应用 `0002`。来源：[v7.3.1 发布说明](https://github.com/telegramdesktop/tdesktop/releases/tag/v7.3.1)。

## 构建

工作流文件：[`.github/workflows/build-v7.3.1-semantic-v3-msys2.yml`](.github/workflows/build-v7.3.1-semantic-v3-msys2.yml)。

1. 在仓库 **Settings → Secrets and variables → Actions** 设置 `TDESKTOP_API_ID` 和 `TDESKTOP_API_HASH`。
2. 打开 **Actions → Build Telegram Desktop Patched Portable**，点击 **Run workflow**。
3. 选择 `Release` 或 `Debug` 并手动启动。
4. 成功后下载 `Telegram-Patched-v7.3.1-Win64-Release` 或 `Telegram-Patched-v7.3.1-Win64-Debug` artifact。便携 ZIP 附带 SHA-256 文件。

本分支的构建 workflow **只有手动触发**，没有 `push` 触发器。创建和更新此分支时不会启动 GitHub Actions。构建依赖 Windows、Visual Studio、Qt 和较长时间的依赖编译；artifact 保留 14 天，源码差异和补丁清单保留 30 天。

工作流将上游 x64 便携包固定为 [`td-portable-win-x64-7.3.1.zip`](https://github.com/telegramdesktop/tdesktop/releases/download/v7.3.1/td-portable-win-x64-7.3.1.zip)，并核对其 SHA-256：`e3ec293ecadce43aab947e8ef274456529e634a6841e6b661eca6efe600ffcda`。该包用于提取 D3D 编译器 DLL，不是本项目生成的补丁客户端。

## 适配与验证状态

五项补丁是按固定的 v7.3.1 源码重新对齐的，工作流会检查源码 commit、补丁数量、补丁目标和应用结果。构建脚本也按该版本的 `prepare.py` 调整：v7.3.1 已使用 MSYS2 UCRT64 软件包名称，因此没有照搬 v7.2.10 的 diffutils/NASM 改写；Qt ICU、Windows SDK ICU、VS2026 Breakpad 工具集和 Qt 单配置步骤则保留并加了锚点检查。

本地静态验证（2026-10-12）已通过：

- 13 个补丁目标文件取自固定的上游 commit；五个 patch 的 `git apply --check`、应用、反向检查和 `git diff --check` 均通过。
- `tools/apply_semantic_patches.py` 对每个旧代码块都找到唯一匹配；工作流生成的五个 canonical patch 经 `git am --3way` 重放后，补丁树一致。
- 针对上游 `prepare.py` 模拟了 Qt/MSYS2/VS 锚点修改与 Release、Debug 两种配置；workflow YAML 解析通过，触发器仅为 `workflow_dispatch`。

验证使用的是固定版本的目标源码文件快照，不是完整 Telegram 仓库构建。尚未验证 Windows 全量编译、便携包内 DLL 提取和客户端启动；本任务没有启动 GitHub Actions。

## 版本分支约定

每个 `vX.Y.Z` 分支对应一个上游版本，固定其 tag/commit、补丁目录、构建 workflow 和 README。这样可以隔离源码上下文与构建工具链变化；补丁不可只改版本号后直接复用。随着支持版本增加，可把重复的构建逻辑抽成共享脚本，但每个版本仍应保留独立的补丁集和上游 commit 锁定。

仓库中的 `build-noads.yml` 是另一条手动前移流程，来源与本分支的五个固定补丁不同；它不能替代本分支的适配和验证。
