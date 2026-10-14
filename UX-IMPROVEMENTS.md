# v7.3.1 UX patch research

This branch keeps the five patches from the successful v7.3.1 baseline, adds the main-DC label, conservative download acceleration, and an adjustable per-DC download-session policy.

## Implemented

- **Show the main data center in Settings → Advanced → Connection type.** Patch 0006 appends the active account's main DC number and refreshes when that DC changes. Individual media can be served from a different DC, so this is a connection diagnostic, not a per-file route indicator. It does not change routing.
  - [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - [mtp_instance.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/mtp_instance.h)

- **Automatic download-start acceleration (patch 0007).** The default profile starts with two MTProto download sessions per DC, preserves the upstream per-session startup window of 4 × 128 KiB, and can adapt upward to eight sessions. Upstream timeout and success logic can remove sessions after repeated slow requests and later add them back. Upload concurrency is unchanged. This can help a high-latency link with spare bandwidth, but does not guarantee a higher rate.
  - [TDesktop download manager at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.cpp)
  - [TDesktop download part size at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.h)

- **Choose the download-session policy (patch 0008).** Settings → Advanced → Data & Storage offers Automatic (2–8) or a manual value from 1 to 8. Automatic keeps the existing two-session start and eight-session adaptive ceiling. A manual value starts that many sessions and caps the pool at that count. The existing timeout recovery can temporarily reduce the pool to one; successful transfers can grow it again up to the configured cap. The preference applies after restart.
  - The pool is per account and per DC. Active downloads using the same DC share it; this is not an OS thread count or a separate guaranteed thread allocation for each file.
  - The UI preference is clamped to the supported range. A missing or malformed preference uses Automatic.
  - [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - [download_manager_mtproto.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.cpp)

## Verifying transfer acceleration

Packet capture counts TCP flows, not Telegram's internal download-session indexes. Four visible flows can include the main account connection, sessions for multiple DCs, CDN traffic, proxy connections, or multiple accounts. The count alone cannot confirm that the custom download policy is active.

For a controlled comparison:

1. Use one account, one proxy setting, and a large file not already cached locally. Pause all other downloads.
2. Set the policy to 1 and restart. Download the file three times, recording full elapsed time and average throughput.
3. Repeat with Automatic, 4, and optionally 8. Compare median time/throughput rather than one run; verify the downloaded file opens and that repeated downloads of the same content produce matching SHA-256 hashes.
4. For connection evidence, capture only during the transfer and correlate flows to the Telegram process. A Debug build's Download (dcId,index) logs identify the DC and session index; indexes 0–3 confirm that all four pool slots handled requests for that DC; overlapping active requests or flows are needed to confirm they were concurrent at the same moment. In Automatic mode the pool can grow gradually, so observe the log over the whole transfer.
5. Keep the route stable. A proxy, CDN redirection, different Telegram DC, changing server load, or Premium speed limit can dominate the measured result.

A faster result is evidence for the tested route and file, not a universal speed guarantee. Telegram's file documentation also describes server-provided limits for parallel downloads of multiple files from one DC; this patch adjusts the MTProto session pool and does not increase the number of queued files.
- [Telegram file download guidance](https://core.telegram.org/api/files)

## Forwarding more than 100 messages

Telegram Desktop defines MaxSelectedItems = 100 in its shared configuration, and the history selection code applies that cap. The forwarding API method accepts a vector of message IDs; its public method schema does not document a 100-ID maximum. The desktop client currently forwards selected IDs as a vector for each source range.

A forward-only bulk operation is technically feasible by collecting more than 100 IDs and queueing multiple requests of at most 100 IDs. It should preserve source order and grouped media, show progress, and handle partial failure without duplicating already-sent batches. Raising the shared MaxSelectedItems constant would also affect other selection operations such as deleting or grouping items, so that is not a safe shortcut. Server-side restrictions, slow mode, flood waits, and anti-spam rules still apply. This feature is not part of the current patch set.
- [TDesktop MaxSelectedItems in config.h](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/config.h)
- [TDesktop history selection cap](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/history/view/history_view_list_widget.cpp)
- [TDesktop forward request construction](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/apiwrap.cpp)
- [Telegram messages.forwardMessages method](https://core.telegram.org/method/messages.forwardMessages)

## Memory use

Telegram Desktop has explicit in-memory media thresholds in storage/file_download.h: 10 MiB for a file, 2 MiB for stickers, and 10 MiB for animated wallpapers and animations. The downloader's largest configured per-session window is 16 × 128 KiB = 2 MiB. Eight sessions can therefore represent up to 16 MiB of requested in-flight data per account/DC at the adaptive ceiling. Automatic starts with two sessions (about 1 MiB of requested part data); manual 8 starts with eight (about 4 MiB). These are transfer windows, not total process memory or a guaranteed resident allocation. Image decoding, Qt caches, visible media, and other accounts add separate usage.

Reducing media thresholds blindly could change inline playback and cache behavior. A safe low-memory option should first be profiled against scrolling, animated media, and simultaneous downloads, then reduce preloading or cache budgets with a visible preference and long-run testing.
- [TDesktop file memory thresholds](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/file_download.h)

## Other open-source client references

- **SereinGram** provides a user opt-in faster-transfers switch. Its transfer hook starts at four download sessions, uses the maximum per-session download window, and multiplies the upload window by four; its generated setting defaults to false. This branch borrows only a conservative download-side control and leaves upload behavior unchanged.
  - [SereinGram transfer hook](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/network/transfer.cpp)
  - [SereinGram setting definition](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/schema/gen/settings/services.h)

- **Kotatogram** lists local folders, compact chat list, custom fonts, and forwarding to multiple chats among its features. Its issue tracker has a 2025 request for a user setting to limit simultaneous downloads, with 1 as the minimum; that is evidence of user demand, not an implemented feature in Kotatogram.
  - [Kotatogram README](https://github.com/kotatogram/kotatogram-desktop)
  - [Kotatogram simultaneous-download limit request](https://github.com/kotatogram/kotatogram-desktop/issues/467)

- **AyuGram Desktop** emphasizes privacy and appearance options such as ghost mode and font customization. Those may suit a separate preferences-focused patch, but are not download or memory optimizations by themselves.
  - [AyuGram Desktop project](https://github.com/TelegramDevs/tdesktop-ayugram)

- **SereinGram's DC status dialog** makes bounded, on-demand probes to the five DCs and applies a 10-second overall deadline through the currently selected non-Web proxy when enabled. It is a connectivity diagnostic, not proof of the route used by one media file. Continuous probes would add traffic and connections, so any port should remain user-triggered.
  - [SereinGram DC status probe at pinned commit](https://github.com/eltavine/SereinGram/blob/09887d863799262d05810c18faa1bfbc5917f5c6/Telegram/SourceFiles/serein/network/dc_status.cpp)

### Candidate next work

1. **Bulk forward above 100.** Add a dedicated action that chunks requests and reports progress; do not raise the global selection cap.
2. **DC reachability test.** A manual, bounded diagnostic could report which DCs are reachable through the current proxy. The current patch only labels the account's main DC.
3. **Memory profile first.** Measure idle, scrolling, animated media, and concurrent downloads before changing media thresholds or caches.

## Validation

- Patch 0008 passes git apply --check against the pinned v7.3.1 source after patches 0006 and 0007.
- The repository semantic patch parser matched all ten hunks uniquely and strictly; git diff --check passed.
- The previous UX build with patches 0006–0007 passed the public Windows Release workflow [run #6](https://github.com/Tea1me/Telegram-Patches-Public/actions/runs/38406495730), and the executable launched successfully.
- Patch 0008 still needs the public Windows Release workflow build before it can be called verified.