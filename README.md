# Telegram Desktop v7.3.1 补丁版构建

本分支将本仓库的十项客户端补丁适配到 Telegram Desktop 上游 **v7.3.1**，并提供 Windows x64 便携版构建工作流。它不是 Telegram 官方发行版。

- 上游标签：[v7.3.1](https://github.com/telegramdesktop/tdesktop/releases/tag/v7.3.1)
- 固定源码 commit：[6fed91ffab9861771a75f29df65031b3c80b6941](https://github.com/telegramdesktop/tdesktop/commit/6fed91ffab9861771a75f29df65031b3c80b6941)
- 补丁目录：[patches/v7.3.1](patches/v7.3.1)
- 目标：Windows x64、Qt 6.11.2、Release 或 Debug 便携构建

## 补丁内容

| 补丁 | 客户端改动 |
| --- | --- |
| 0001 | 不显示赞助消息和赞助顶栏入口。 |
| 0002 | 放宽受保护消息的选择、复制和媒体保存限制；保留限时媒体与扩展付费媒体的保存检查。 |
| 0003 | 将邀请预览到期时间改为不在客户端到期。 |
| 0004 | 将普通与 Premium 客户端账号槽位上限改为 255。 |
| 0005 | 在实验设置中增加关闭 Stories 的选项，默认关闭该选项；启用后需重启客户端。 |
| 0006 | 在“设置 → 高级 → 连接类型”显示当前账号的主 DC 编号，随 DC 切换刷新。它不代表每个媒体文件使用的 DC。 |
| 0007 | 自动下载并发以每 DC 两个 MTProto 会话起步，可按上游逻辑逐步扩到 8 个；保留超时回退，不改上传策略。 |
| 0008 | 在“设置 → 高级 → 数据与存储”增加每 DC 下载会话数设置：自动（2 起步、自适应到 8）或手动 1–8。手动值既是起步数也是上限；超时恢复逻辑仍可暂时降到 1。 |
| 0009 | 增加按需 DC1–DC5 连通性检查，显示握手延迟或失败并标记当前账号主 DC；10 秒后收尾，不改变连接路由。 |
| 0010 | 默认关闭；启用后将服务器消息 ID 显示在时间戳悬停提示中，仅对正数消息 ID 生效，不改变消息布局。 |

### 按需检查 DC 连通性

入口位于“设置 → 高级 → 数据与存储 → Test data center connections”。打开后并行检查 DC1–DC5，显示连接延迟或失败，并标记当前账号的主 DC。每次检查最多运行 10 秒，使用启用的 Telegram 代理（Web 代理除外），否则直连；关闭对话框会结束检查。这只是网络诊断，不代表某个文件的实际 DC，也不会改变正常路由。

### 查看消息 ID

在“设置 → 高级 → 数据与存储”启用 **Show message IDs in timestamp tooltip**（默认关闭）。悬停消息时间戳即可查看正数服务器消息 ID；频道消息原有的浏览量或转发量提示会保留并另起一行显示 ID。该设置即时生效，不需要重启。

这些改动只修改客户端行为，不能变更服务器端的权限、订阅状态或限制。邀请链接、账号数、受保护内容等仍可能受服务器规则约束。

### v7.3.1 保存行为说明

上游 v7.3.1 发布说明包含修复“受限媒体进入 Downloads”的改动。本分支的 0002 会放宽相关客户端限制，因此和这项上游行为存在直接的兼容性取舍。补丁仍保留限时媒体及扩展付费媒体的检查；如果你需要保持上游对其他受限媒体的默认保护行为，请不要应用 0002。来源：[v7.3.1 发布说明](https://github.com/telegramdesktop/tdesktop/releases/tag/v7.3.1)。

## 如何验证下载加速

客户端里的 Download sessions per DC 位于“设置 → 高级 → 数据与存储”。默认 Automatic (2–8) 会从 2 个会话起步并自适应增加到 8；手动选 1–8 时会按所选数量起步并将该 DC 的会话上限设为该值。会话池按账号和 DC 建立，供该 DC 的下载任务共同使用。这里的 session 是 MTProto 下载网络会话，不是 CPU 线程，也不等同于单个文件独占的线程数。修改后重启客户端。你已实测手动设置为 8 时出现了 8 个下载会话，这确认设置生效；具体连接数仍可能受 DC、CDN、代理和其他活动影响。

建议按同一个大文件做对照：

1. 使用同一账号、网络、代理和大文件，暂停其他下载。每轮开始前，在“设置 → 高级 → 数据与存储 → 管理本地存储”清除 Telegram 媒体缓存，避免读到缓存副本。
2. 先选 1 并重启，下载文件；记录完整耗时和平均速度。然后分别测试 Automatic、4 和 8，每次切换后重启。
3. 尽可能每种设置测 3 次，比较中位耗时。确认下载文件能打开，并校验各副本的 SHA-256 一致。

抓包里的 4 条 TCP 连接只能说明捕获到 4 条网络流，不足以证明正好有 4 个下载会话。主连接、其他 DC、CDN、代理和多账号都会影响连接数。固定选择 4 时，在同一个 DC 的下载日志中看到 session index 0–3，能确认这 4 个会话都处理过请求；要确认请求实际重叠并发，还要检查同一时段的活跃连接或请求。可用 Debug 构建查看 Download (dcId,index) 日志。单纯连接数相符只能作为旁证。网络路线、服务器响应和账号限速都会影响速度，因此一次抓包或单次下载不能证明加速效果。

## 构建

工作流文件：[build-v7.3.1-semantic-v3-msys2.yml](.github/workflows/build-v7.3.1-semantic-v3-msys2.yml)。

1. 在仓库 Settings → Secrets and variables → Actions 设置 TDESKTOP_API_ID 和 TDESKTOP_API_HASH。
2. 打开 Actions → Build Telegram Desktop Patched Portable，点击 Run workflow。
3. 选择 Release 或 Debug 并手动启动。
4. 成功后下载 Telegram-Patched-v7.3.1-Win64-Release 或 Telegram-Patched-v7.3.1-Win64-Debug artifact。便携 ZIP 附带 SHA-256 文件。

push 在 v7.3.1 与 v7.3.1-ux 分支的补丁、工具或该 workflow 文件变化时触发；也可以从 Actions 手动运行 workflow_dispatch。构建依赖 Windows、Visual Studio、Qt 和较长时间的依赖编译；artifact 保留 14 天，源码差异和补丁清单保留 30 天。

工作流将上游 x64 便携包固定为 [td-portable-win-x64-7.3.1.zip](https://github.com/telegramdesktop/tdesktop/releases/download/v7.3.1/td-portable-win-x64-7.3.1.zip)，并核对其 SHA-256：e3ec293ecadce43aab947e8ef274456529e634a6841e6b661eca6efe600ffcda。该包用于提取 D3D 编译器 DLL，不是本项目生成的补丁客户端。

## 适配与验证状态

v7.3.1 基线五项补丁已由 public 仓库的 [Release run #3](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38262024061) 全量构建成功。加入 0006 和 0007 后，[Release run #6](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38406495730) 通过 Windows Release 构建；加入 0008 后，[Release run #7](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38562517440) 也成功，你已确认 exe 可启动并实测 8 个下载会话生效。0009 加入后的 Windows Release 构建、portable 打包和产物上传已由 [Release run #8](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38655275048) 全部通过。0010 已通过本地补丁匹配与差异检查；加入它后的 [Release run #10](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38724066310) 已通过 Windows x64 / Qt6 / Release 全量编译、portable 包校验和产物上传。portable artifact `Telegram-Patched-v7.3.1-Win64-Release`（约 85 MB，保留 14 天）可从该 run 的 Artifacts 下载。

脚本按 v7.3.1 的 prepare.py 适配：上游已使用 MSYS2 UCRT64 软件包名称，因此没有照搬 v7.2.10 的 diffutils/NASM 改写；Qt ICU、Windows SDK ICU、VS2026 Breakpad 工具集和 Qt 单配置步骤则保留并加了锚点检查。转发上限与内存调研见 [UX-IMPROVEMENTS.md](UX-IMPROVEMENTS.md)。

## 版本分支约定

每个 vX.Y.Z 分支对应一个上游版本，固定其 tag/commit、补丁目录、构建 workflow 和 README。这样可以隔离源码上下文与构建工具链变化；补丁不可只改版本号后直接复用。随着支持版本增加，可把重复的构建逻辑抽成共享脚本，但每个版本仍应保留独立的补丁集和上游 commit 锁定。

仓库中的 build-noads.yml 是另一条手动前移流程，来源与本分支的十个固定补丁不同；它不能替代本分支的适配和验证。
