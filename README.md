# Telegram Desktop v7.3.1 补丁版构建

本分支将本仓库的十六项客户端补丁适配到 Telegram Desktop 上游 **v7.3.1**，并提供 Windows x64 便携版构建工作流。它不是 Telegram 官方发行版。

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
| 0011 | 聊天记录最多可选择 1000 条消息并按服务器 `forwarded_count_max` 分批转发；超过 100 条时隐藏删除操作并在删除入口再次拦截。该补丁不改变服务器单次转发上限。 |
| 0012 | 在群组和超级群组的单条用户消息菜单中增加 **Search messages**，直接在当前聊天按发送者筛选历史。多选、广播频道及匿名/非用户发送者不显示该入口。 |
| 0013 | 启动时可通过 `TDESKTOP_API_ID` 与 `TDESKTOP_API_HASH` 环境变量覆盖内置凭据；两者必须同时有效，否则成对使用构建时默认值。 |
| 0014 | 可通过 `TDESKTOP_HIDE_FROM_CAPTURE=1` 在 Windows 上隐藏 Telegram 顶层窗口及通知窗口的屏幕捕获内容；默认关闭。 |
| 0015 | 在“设置 → 高级 → 数据与存储”显示当前实际采用的 API ID 及来源；点击复制 ID，不显示 API_HASH。 |
| 0016 | 对已保存的非 Web 代理执行有并发上限和总超时的握手测速；可按延迟排序，或在二次确认后清理已确认不可达的代理。当前选中代理、Web 代理及未完成测试的代理都会保留，不自动切换线路。 |

### 按需检查 DC 连通性

入口位于“设置 → 高级 → 数据与存储 → Test data center connections”。打开后并行检查 DC1–DC5，显示连接延迟或失败，并标记当前账号的主 DC。每次检查最多运行 10 秒，使用启用的 Telegram 代理（Web 代理除外），否则直连；关闭对话框会结束检查。这只是网络诊断，不代表某个文件的实际 DC，也不会改变正常路由。

### 测速与整理已保存代理

在“设置 → 高级 → 数据与存储”使用 **Sort saved proxies by latency**，会通过当前账号的主 DC 测试已保存的 SOCKS5、HTTP 和 MTProto 代理，先按成功握手的延迟从低到高排列；Web 代理及未测完的代理保留在可测速代理之后，确认不可达的代理排在最后。一次最多并发测试 4 个代理，总时限 15 秒。该操作只调整列表顺序，不启用或切换代理，并保留代理轮换的优先级设置。

**Remove unavailable proxies** 会做同样的检查，并在确认后删除已确认不可达且未选中的代理。当前选中的代理、Web 代理以及超时或尚未测试的代理不会被删除。测速结果反映当前账号到 Telegram 主 DC 的握手情况，不保证所有账号或后续时刻表现相同。

### 查看消息 ID

在“设置 → 高级 → 数据与存储”启用 **Show message IDs in timestamp tooltip**（默认关闭）。悬停消息时间戳即可查看正数服务器消息 ID；频道消息原有的浏览量或转发量提示会保留并另起一行显示 ID。该设置即时生效，不需要重启。

### 批量转发超过 100 条

在聊天记录中选择多于 100 条消息后，转发会按服务器提供的 `forwarded_count_max` 自动拆成多个请求，最多支持一次选择 1000 条。媒体组能完整放入单个请求时会尽量保持在同一批次。超过 100 条的选择不会提供删除操作，删除入口也会再次拦截。服务器限速、慢速模式、FloodWait 和反垃圾规则仍然有效；如果某一批失败，前面已成功的批次不会自动重发。

这些改动只修改客户端行为，不能变更服务器端的权限、订阅状态或限制。邀请链接、账号数、受保护内容等仍可能受服务器规则约束。

### 按发送者搜索群聊消息

在群组或超级群组的单条用户消息上打开右键菜单，选择 **Search messages**，客户端会在当前聊天中按该发送者筛选消息。多选、广播频道以及匿名或非用户发送者不会显示入口。该功能沿用 Telegram Desktop 内置的 sender-filter 搜索接口，结果仍由 Telegram 服务器返回。

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

1. 工作流从仓库 Settings → Secrets and variables → Actions 读取 `TDESKTOP_API_ID` 和 `TDESKTOP_API_HASH`，并将其作为客户端的构建默认值。未设置时工作流使用 Telegram 官方文档标记为测试用途的值；它们只适合测试，不适合日常账号登录。上游要求构建时通过 CMake 提供一组值：[telegram_options.cmake](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/cmake/telegram_options.cmake)。
2. 打开 Actions → Build Telegram Desktop Patched Portable，点击 Run workflow。
3. 选择 Release 或 Debug 并手动启动。
4. 成功后下载 Telegram-Patched-v7.3.1-Win64-Release 或 Telegram-Patched-v7.3.1-Win64-Debug artifact。便携 ZIP 附带 SHA-256 文件。

### 用自己的 API_ID/API_HASH 启动

无需为这两个值重新编译。完全退出所有 Telegram 进程后，在 `Telegram.exe` 同目录创建一个本地 `.bat` 文件，填入你从 Telegram 官方页面申请的 API ID 和 API hash：

```bat
@echo off
setlocal
set "TDESKTOP_API_ID=12345678"
set "TDESKTOP_API_HASH=替换成32位十六进制hash"
start "" "%~dp0Telegram.exe"
endlocal
```

ID 必须是正整数，hash 必须是 32 位十六进制字符；两个变量都有效时才会同时采用。任何一个缺失或格式无效，客户端会改用构建时的默认凭据。客户端在本次进程首次读取凭据后缓存结果，修改变量后需彻底退出并通过该 `.bat` 重启。不要把含有个人凭据的 `.bat` 上传到公开仓库。

### 查看当前使用的 API ID

打开“设置 → 高级 → 数据与存储”，查看 **Current API ID**。副标题会标注凭据来自 **Runtime environment** 还是 **Build default**；点击该行会复制 API ID。这里显示的是进程实际缓存并用于 API 请求的 ID；API_HASH 不会显示或复制。

### 屏幕共享隐私模式（可选）

如果使用 Windows 10 2004 或更新版本进行屏幕共享，可在启动 `.bat` 中加入下面一行：

```bat
set "TDESKTOP_HIDE_FROM_CAPTURE=1"
```

补丁调用 Telegram Desktop 已有的截图保护管理器，将所有顶层窗口（包括通知窗口）从遵循 Windows 窗口捕获排除设置的录屏/共享结果中排除。删除该变量或关闭当前启动脚本后重新启动，恢复正常捕获。Windows 10 2004 以前的系统会回退为黑色窗口区域；部分捕获软件可能忽略系统请求，因此这不是绝对的隐私保证。它不会遮挡你本机屏幕上的窗口。

push 在 v7.3.1、v7.3.1-ux、v7.3.1-bulk-forward、v7.3.1-search-from-sender、v7.3.1-api-credentials、v7.3.1-screen-share-privacy 与 v7.3.1-proxy-tools 分支的补丁、工具或该 workflow 文件变化时触发；也可以从 Actions 手动运行 workflow_dispatch。构建依赖 Windows、Visual Studio、Qt 和较长时间的依赖编译；artifact 保留 14 天，源码差异和补丁清单保留 30 天。

工作流将上游 x64 便携包固定为 [td-portable-win-x64-7.3.1.zip](https://github.com/telegramdesktop/tdesktop/releases/download/v7.3.1/td-portable-win-x64-7.3.1.zip)，并核对其 SHA-256：e3ec293ecadce43aab947e8ef274456529e634a6841e6b661eca6efe600ffcda。该包用于提取 D3D 编译器 DLL，不是本项目生成的补丁客户端。

## 适配与验证状态

v7.3.1 基线五项补丁已由 public 仓库的 [Release run #3](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38262024061) 全量构建成功。加入 0006 和 0007 后，[Release run #6](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38406495730) 通过 Windows Release 构建；加入 0008 后，[Release run #7](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38562517440) 也成功，你已确认 exe 可启动并实测 8 个下载会话生效。0009 加入后的 Windows Release 构建、portable 打包和产物上传已由 [Release run #8](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38655275048) 全部通过。0010 加入后的 [Release run #10](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38724066310) 已通过 Windows x64 / Qt6 / Release 全量编译、portable 包校验和产物上传。portable artifact `Telegram-Patched-v7.3.1-Win64-Release`（约 85 MB，保留 14 天）可从该 run 的 Artifacts 下载。0011 的 14 个语义补丁块已在本地与固定 v7.3.1 源码逐一匹配。run #11 在编译 `share_box.cpp` 时因缺少 `mtproto_config.h` 报 MSVC C2027；已补上显式 include。修复后的 [Release run #13](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/39004771173) 已通过 Windows x64 / Qt6 / Release 全量编译、portable 启动烟测、ZIP 校验和 artifact 上传；Release artifact 约 85 MB，可从该 run 的 Artifacts 下载。加入 0012–0016 后，[Release run #21](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/39057712528) 通过 Windows x64 / Qt6 / Release 全量编译、便携包校验和 artifact 上传；这确认该分支当前代码可编译并完成打包。

脚本按 v7.3.1 的 prepare.py 适配：上游已使用 MSYS2 UCRT64 软件包名称，因此没有照搬 v7.2.10 的 diffutils/NASM 改写；Qt ICU、Windows SDK ICU、VS2026 Breakpad 工具集和 Qt 单配置步骤则保留并加了锚点检查。转发上限与内存调研见 [UX-IMPROVEMENTS.md](UX-IMPROVEMENTS.md)。

## 版本分支约定

每个 vX.Y.Z 分支对应一个上游版本，固定其 tag/commit、补丁目录、构建 workflow 和 README。这样可以隔离源码上下文与构建工具链变化；补丁不可只改版本号后直接复用。随着支持版本增加，可把重复的构建逻辑抽成共享脚本，但每个版本仍应保留独立的补丁集和上游 commit 锁定。

仓库中的 build-noads.yml 是另一条手动前移流程，来源与本分支的十六个固定补丁不同；它不能替代本分支的适配和验证。
