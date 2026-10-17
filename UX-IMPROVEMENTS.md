# v7.3.1 UX patch research

This branch keeps the five patches from the successful v7.3.1 baseline and carries thirteen patches total. It includes the download-session controls, batch forwarding above 100 messages, sender-filtered group search, and launch-time API credential overrides.

## Implemented

- **Override API credentials at launch (patch 0013).** Set both `TDESKTOP_API_ID` and `TDESKTOP_API_HASH` in the process environment before launch. A positive decimal ID and a 32-character hexadecimal hash are required; invalid or partial overrides fall back together to the compiled pair. The values are loaded once and are not written to Telegram settings. This supports personal credentials without rebuilding the executable.
  - Adapted from Kotatogram’s [runtime environment override at a pinned commit](https://github.com/kotatogram/kotatogram-desktop/blob/4561e1a33bb55feb692282d8ae5ba1bf6f7a72f3/Telegram/SourceFiles/core/launcher.cpp).
  - The override covers phone login, QR login, Passkey initialization, and MTProto connection initialization.

- **Show the main data center in Settings → Advanced → Connection type.** Patch 0006 appends the active account's main DC number and refreshes when that DC changes. Individual media can be served from a different DC, so this is a connection diagnostic, not a per-file route indicator. It does not change routing.
  - [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - [mtp_instance.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/mtp_instance.h)

- **Check data-center connectivity on demand (patch 0009).** Settings → Advanced → Data & Storage opens a one-shot test for DC1–DC5, reports connection latency or failure, and marks the account's current main DC. It uses the enabled Telegram proxy except Web proxies, then falls back to a direct connection. The total deadline is 10 seconds; closing the dialog releases active probes. It does not poll in the background, change routing, or identify the DC that serves an individual media file.
  - Adapted from [SereinGram's DC status probe at pinned commit](https://github.com/eltavine/SereinGram/blob/09887d863799262d05810c18faa1bfbc5917f5c6/Telegram/SourceFiles/serein/network/dc_status.cpp).
  - TDesktop connection APIs: [connection_abstract.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/connection_abstract.h), [mtproto_dc_options.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/mtproto_dc_options.h).

- **Show server message IDs in the timestamp tooltip (patch 0010).** Settings → Advanced → Data & Storage includes an opt-in checkbox, off by default. Hover a message timestamp to see its positive server message ID; channels that already show view/forward counts retain those details and add the ID on a separate tooltip line. The preference applies immediately and does not widen message bubbles.
  - Inspired by 64Gram's [feature list](https://github.com/jolygmanka/64gram/blob/715612054aa9e3ec94b5ab7e748d3000320a671e/features.md) and [timestamp implementation](https://github.com/jolygmanka/64gram/blob/715612054aa9e3ec94b5ab7e748d3000320a671e/Telegram/SourceFiles/history/view/history_view_bottom_info.cpp). This branch uses Telegram Desktop's existing custom-tooltip path and a separate default-off preference.

- **Search a group by message sender (patch 0012).** On a single user-authored message in a basic group or megagroup, the context menu opens that chat's search with the sender filter already selected. The entry is hidden for multi-selection, broadcast channels, and anonymous or non-user senders. It uses TDesktop's existing search navigation and server-side `from_id` filter instead of constructing a `from:` text query.
  - Ported from 64Gram's [message context-menu action at the pinned commit](https://github.com/jolygmanka/64gram/blob/715612054aa9e3ec94b5ab7e748d3000320a671e/Telegram/SourceFiles/history/view/history_view_context_menu.cpp).
  - TDesktop APIs: [searchInChat at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/window/window_session_controller.h), [MessagesSearch request at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/api/api_messages_search.cpp).

- **Automatic download-start acceleration (patch 0007).** The default profile starts with two MTProto download sessions per DC, preserves the upstream per-session startup window of 4 × 128 KiB, and can adapt upward to eight sessions. Upstream timeout and success logic can remove sessions after repeated slow requests and later add them back. Upload concurrency is unchanged. This can help a high-latency link with spare bandwidth, but does not guarantee a higher rate.
  - [TDesktop download manager at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.cpp)
  - [TDesktop download part size at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.h)

- **Choose the download-session policy (patch 0008).** Settings → Advanced → Data & Storage offers Automatic (2–8) or a manual value from 1 to 8. Automatic keeps the existing two-session start and eight-session adaptive ceiling. A manual value starts that many sessions and caps the pool at that count. The existing timeout recovery can temporarily reduce the pool to one; successful transfers can grow it again up to the configured cap. The preference applies after restart.
  - The pool is per account and per DC. Active downloads using the same DC share it; this is not an OS thread count or a separate guaranteed thread allocation for each file.
  - The UI preference is clamped to the supported range. A missing or malformed preference uses Automatic.
  - [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - [download_manager_mtproto.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.cpp)

## API credentials

The workflow maps the repository Actions secrets `TDESKTOP_API_ID` and `TDESKTOP_API_HASH` into the executable as build-time defaults. Patch 0013 also reads the runtime pair `TDESKTOP_API_ID` + `TDESKTOP_API_HASH` once, when credentials are first requested. Set both values before launch; a positive decimal ID and a 32-character hexadecimal hash are required. If either value is missing or invalid, the client uses the compiled pair. This lets a downloaded executable use your own credentials without another build.

For Windows, fully exit Telegram, then create a local `.bat` file next to `Telegram.exe`:

```bat
@echo off
setlocal
set "TDESKTOP_API_ID=12345678"
set "TDESKTOP_API_HASH=replace_with_32_hex_characters"
start "" "%~dp0Telegram.exe"
endlocal
```

Do not commit or share the file containing your personal values. The branch supports environment variables only; it does not put the hash on the command line.

- Adapted from Kotatogram’s environment override in [launcher.cpp at the pinned commit](https://github.com/kotatogram/kotatogram-desktop/blob/4561e1a33bb55feb692282d8ae5ba1bf6f7a72f3/Telegram/SourceFiles/core/launcher.cpp); its documented feature also allows startup parameters, which this branch omits.
- [Upstream v7.3.1 CMake options](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/cmake/telegram_options.cmake)
- [Telegram Desktop API credential instructions](https://github.com/telegramdesktop/tdesktop/blob/dev/docs/api_credentials.md)

## Verifying transfer acceleration

Packet capture counts TCP flows, not Telegram's internal download-session indexes. Four visible flows can include the main account connection, sessions for multiple DCs, CDN traffic, proxy connections, or multiple accounts. The count alone cannot confirm that the custom download policy is active.

For a controlled comparison:

1. Use one account, one proxy setting, and the same large file. Pause all other downloads. Before each trial, clear Telegram's media cache in Settings → Advanced → Data & Storage → Manage Local Storage so the test cannot read a cached copy.
2. Set the policy to 1 and restart. Download the file three times, recording full elapsed time and average throughput.
3. Repeat with Automatic, 4, and optionally 8. Compare median time/throughput rather than one run; verify the downloaded file opens and that repeated downloads of the same content produce matching SHA-256 hashes.
4. For connection evidence, capture only during the transfer and correlate flows to the Telegram process. A Debug build's Download (dcId,index) logs identify the DC and session index; indexes 0–3 confirm that all four pool slots handled requests for that DC; overlapping active requests or flows are needed to confirm they were concurrent at the same moment. In Automatic mode the pool can grow gradually, so observe the log over the whole transfer.
5. Keep the route stable. A proxy, CDN redirection, different Telegram DC, changing server load, or Premium speed limit can dominate the measured result.

A faster result is evidence for the tested route and file, not a universal speed guarantee. Telegram's file documentation also describes server-provided limits for parallel downloads of multiple files from one DC; this patch adjusts the MTProto session pool and does not increase the number of queued files.
- [Telegram file download guidance](https://core.telegram.org/api/files)

Your manual test with the policy set to 8 observed eight download sessions, confirming that the configured pool size is applied. This verifies session creation, not a universal speed increase; compare transfer times separately.

## Forwarding more than 100 messages

TDesktop's shared `MaxSelectedItems` is 100, while Telegram publishes the server-side `forwarded_count_max` in its configuration. Patch 0011 raises only history-message selection to a local safety cap of 1000, then splits both the normal ShareBox forward flow and the API forwarding path into requests no larger than the configured server value. A grouped-media batch boundary is moved to keep an album together when the whole group fits within the server limit. The delete action remains limited to 100 selected messages and has a second defensive check.

This supports selecting and forwarding 101–1000 messages in one user operation; it does not raise the server's per-request limit or bypass slow mode, flood waits, or anti-spam controls. Requests are submitted as batches. If Telegram rejects a batch, already accepted batches are not automatically resent, so a manual retry could duplicate messages that already arrived. The current UI does not show per-batch progress.

- [TDesktop selection cap in config.h](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/config.h)
- [TDesktop history selection and forwardability](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/history/history_inner_widget.cpp)
- [TDesktop API forwarding path](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/apiwrap.cpp)
- [TDesktop recipient ShareBox forwarding path](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/boxes/share_box.cpp)
- [Telegram's server-provided forwarded_count_max](https://core.telegram.org/api/config)
- [Telegram messages.forwardMessages method](https://core.telegram.org/method/messages.forwardMessages)
## Memory use

Telegram Desktop has explicit in-memory media thresholds in storage/file_download.h: 10 MiB for a file, 2 MiB for stickers, and 10 MiB for animated wallpapers and animations. The downloader's largest configured per-session window is 16 × 128 KiB = 2 MiB. Eight sessions can therefore represent up to 16 MiB of requested in-flight data per account/DC at the adaptive ceiling. Automatic starts with two sessions (about 1 MiB of requested part data); manual 8 starts with eight (about 4 MiB). These are transfer windows, not total process memory or a guaranteed resident allocation. Image decoding, Qt caches, visible media, and other accounts add separate usage.

Reducing media thresholds blindly could change inline playback and cache behavior. A safe low-memory option should first be profiled against scrolling, animated media, and simultaneous downloads, then reduce preloading or cache budgets with a visible preference and long-run testing.
- [TDesktop file memory thresholds](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/file_download.h)

## Other open-source client references

- **SereinGram** provides a user opt-in faster-transfers switch. Its transfer hook starts at four download sessions, uses the maximum per-session download window, and multiplies the upload window by four; its generated setting defaults to false. This branch borrows only a conservative download-side control and leaves upload behavior unchanged.
  - [SereinGram transfer hook](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/network/transfer.cpp)
  - [SereinGram setting definition](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/schema/gen/settings/services.h)

- **Kotatogram** lists local folders, custom text replacements, compact chat list, custom fonts, and other personal workflow controls. The multi-recipient forward option is already present in this TDesktop version, so it is not duplicated here. Local folders and text replacements are stronger next candidates than diagnostic-only UI; each still needs a separate scope and migration/settings review.
  - [Kotatogram README](https://github.com/kotatogram/kotatogram-desktop)
  - [TDesktop recipient selection and multi-forward](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/boxes/share_box.cpp)
  - [Kotatogram simultaneous-download limit request](https://github.com/kotatogram/kotatogram-desktop/issues/467)

- **AyuGram Desktop** emphasizes privacy and appearance options such as ghost mode and font customization. Those may suit a separate preferences-focused patch, but are not download or memory optimizations by themselves.
  - [AyuGram Desktop project](https://github.com/TelegramDevs/tdesktop-ayugram)

- **SereinGram's DC status dialog** makes bounded, on-demand probes to the five DCs and applies a 10-second overall deadline through the currently selected non-Web proxy when enabled. It is a connectivity diagnostic, not proof of the route used by one media file. Continuous probes would add traffic and connections, so any port should remain user-triggered.
  - [SereinGram DC status probe at pinned commit](https://github.com/eltavine/SereinGram/blob/09887d863799262d05810c18faa1bfbc5917f5c6/Telegram/SourceFiles/serein/network/dc_status.cpp)

### Already available upstream

64Gram's feature list includes showing a user's total sent-message count before a moderator deletes that sender's messages. No new patch is needed for this branch: Telegram Desktop v7.3.1 already queries `Api::MessagesSearch` with the sender filter, stores the server's `found.total`, and exposes the count in its moderation confirmation UI.
- [TDesktop v7.3.1 moderation count query](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/boxes/moderate_messages_box.cpp)
- [64Gram feature list](https://github.com/jolygmanka/64gram/blob/715612054aa9e3ec94b5ab7e748d3000320a671e/features.md)

### Candidate next work

1. **Custom text replacements.** Kotatogram supports replacements for repeated replies and snippets. This has a direct daily-use benefit; next review the input pipeline, edit UI, and persistence format before porting.
   - [Kotatogram feature list](https://github.com/kotatogram/kotatogram-desktop)
   - [Kotatogram source at the pinned commit](https://github.com/kotatogram/kotatogram-desktop/tree/4561e1a33bb55feb692282d8ae5ba1bf6f7a72f3/Telegram/SourceFiles)
2. **Local folders.** Kotatogram supports folders stored locally; these could organize chat views without changing Telegram's synced folders. The port needs separate storage and clear account/folder behavior.
   - [Kotatogram feature list](https://github.com/kotatogram/kotatogram-desktop)
3. **AyuGram streamer and privacy controls.** AyuGram lists Streamer mode, message history, anti-recall, and flexible ghost mode. Streamer mode looks worth inspecting for screen-sharing privacy; the history and ghost-mode options need a separate review of local retention and read/online-state effects.
   - [AyuGram Desktop README](https://github.com/AyuGram/AyuGramDesktop)
   - [AyuGram Desktop feature documentation](https://docs.ayugram.one/desktop/)
## Validation

- Patch 0013’s 11 semantic hunks apply uniquely to exact v7.3.1 source files for configuration, phone login, QR login, passkeys, MTProto session initialization, and crash annotations; local `git diff --check` passes. Runtime override behavior still needs a Windows build and launch test.

- Patches 0008 and 0009 pass local application and diff-format checks against the pinned v7.3.1 source after the earlier patches; patch 0009's seven hunks each resolve uniquely.
- The semantic patch parser matched all patch 0009 source blocks uniquely; the patch was applied to a clean local source worktree and `git diff --check` passed.
- Patch 0010 was applied after patches 0008 and 0009 in a source fixture. All six hunks matched exactly one source span; its C++ hunks also pass `git apply --check` against that post-0009 fixture.
- Patches 0001–0009 passed the public Windows Release build, portable packaging, and artifact upload in [run #8](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38655275048).
- Patches 0001–0010 passed the public Windows Release build, portable packaging, and artifact upload in [run #10](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38724066310); you confirmed the executable starts and verified 8 download sessions in-app.
- Patch 0012's two semantic hunks match uniquely against the pinned v7.3.1 context-menu source; the repository's semantic parser applies them and local `git diff --check` passes.
- Patch 0011's 14 old-code blocks match uniquely against the post-0010 v7.3.1 fixtures, and its unified-diff hunk counts are consistent. The first build exposed a missing `mtproto_config.h` include in `share_box.cpp` (MSVC C2027); the include was added. [Run #13](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/39004771173) passed Windows x64 / Qt6 / Release compilation, startup smoke test, portable ZIP validation, and artifact upload. The 101+ message in-app forwarding test remains pending.
