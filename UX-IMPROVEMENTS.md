# v7.3.1 UX patch research

This branch keeps the five patches from the successful v7.3.1 build baseline, adds the main-DC label, and adds conservative download-start acceleration.

## Implemented

- **Show the main data center in Settings → Advanced → Connection type.** Patch 0006 appends the active account's main DC number and refreshes when that DC changes. Individual media can be served from a different DC, so this is a connection diagnostic, not a per-file route indicator. It does not change routing.
  - [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - [mtp_instance.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/mtp_instance.h)

- **Start downloads with two MTProto sessions.** Patch 0007 starts with two sessions while keeping a separate one-session minimum for failure recovery. The per-session startup window (4 × 128 KiB), maximum window (16 × 128 KiB), maximum session count (8), success-based scale-up, and timeout-based scale-down remain at upstream values. It gives large downloads more request slots immediately, which can help on high-latency links; it cannot guarantee a higher rate on every network.
  - Upstream download manager: [download_manager_mtproto.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.cpp)
  - Part size: [download_manager_mtproto.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/download_manager_mtproto.h)
  - SereinGram uses a more aggressive, opt-in profile: four starting sessions, the maximum per-session window, and a larger upload window. Its setting is off by default. This branch adopts the same idea at a smaller scale and leaves upload concurrency unchanged.
  - [SereinGram transfer hooks](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/network/transfer.cpp)
  - [SereinGram transfer setting](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/schema/gen/settings/services.h)

## Forwarding more than 100 messages

Telegram Desktop defines `MaxSelectedItems = 100` in its shared configuration, and the history selection code applies that cap. The forwarding API method accepts a vector of message IDs; its public method schema does not document a 100-ID maximum. The desktop client currently forwards selected IDs as a vector for each source range.

A forward-only bulk operation is technically feasible by collecting more than 100 IDs and queueing multiple requests of at most 100 IDs. It should preserve source order and grouped media, show progress, and handle partial failure without duplicating already-sent batches. Raising the shared `MaxSelectedItems` constant would also affect other selection operations such as deleting or grouping items, so that is not a safe shortcut. Telegram's server-side content restrictions, slow mode, flood waits, and anti-spam rules still apply.

- [TDesktop MaxSelectedItems in config.h](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/config.h)
- [TDesktop history selection cap](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/history/view/history_view_list_widget.cpp)
- [TDesktop forward request construction](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/apiwrap.cpp)
- [Telegram messages.forwardMessages method](https://core.telegram.org/method/messages.forwardMessages)

## Memory use

Telegram Desktop has explicit in-memory media thresholds in `storage/file_download.h`: 10 MiB for a file, 2 MiB for stickers, and 10 MiB for animated wallpapers and animations. Its MTProto download manager can request up to 16 parts per session across at most 8 sessions for one DC (a theoretical 16 MiB outstanding-part window per DC). This is not the full process memory limit; image decoding, Qt caches, visible media, and other accounts add separate usage.

Patch 0007 doubles only the initial per-DC download slots from four 128 KiB parts to eight (about 0.5 MiB to 1 MiB of requested part data while starting). It does not raise the adaptive maximum. Lowering media thresholds blindly could change inline playback and cache behavior; a proper low-memory option should first be profiled against message scrolling, animated media, and simultaneous downloads, then reduce preloading or cache budgets with a visible preference and soak testing.

- [TDesktop file memory thresholds](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/storage/file_download.h)
- [Telegram API file download queue guidance](https://core.telegram.org/api/files)

## Other client references

AyuGram Desktop, Kotatogram, and SereinGram are public Telegram Desktop based projects. Kotatogram documents local folders, a compact chat list, custom fonts, multi-chat forwarding, and proxy auto-rotation. SereinGram has inspectable source for DC latency/status probes and the transfer profile above. These projects target different upstream revisions, so their changes should be ported selectively rather than copied wholesale.

SereinGram's DC status dialog creates one temporary connection to each of the five DCs, reports each connection's ping or failure, and applies a 10-second overall timeout. It measures through the currently selected non-Web proxy when enabled, otherwise directly. This is useful as an on-demand connectivity diagnostic; it does not prove which DC serves a particular media file. Running such probes continuously would add connections and traffic, so a future implementation should stay user-triggered and bounded.

- [AyuGram Desktop source](https://github.com/AyuGram/AyuGramDesktop)
- [Kotatogram Desktop README and feature list](https://github.com/kotatogram/kotatogram-desktop)
- [SereinGram feature matrix](https://github.com/eltavine/SereinGram/blob/main/docs/serein/features.md)
- [SereinGram DC status probe](https://github.com/eltavine/SereinGram/blob/09887d863799262d05810c18faa1bfbc5917f5c6/Telegram/SourceFiles/serein/network/dc_status.cpp)

## Validation

- Patch 0007 passes `git apply --check` against the pinned v7.3.1 download-manager source.
- The repository semantic patch parser matched and applied its hunk uniquely; `git diff --check` passed.
- Patch 0007 has not yet passed the Windows build workflow. This branch's workflow is being configured to build on changes to its v7.3.1 patches and tooling.
