# v7.3.1 UX patch research

This branch carries the five existing v7.3.1 patches and adds one small network-diagnostics improvement.

## Implemented

- **Show the main data center in Settings → Advanced → Connection type.** The existing row already reports the effective proxy/transport state. It now appends the active account's main DC number and refreshes when that DC changes. This is the account's main DC; individual media can be served from a different DC, so the label is a connection diagnostic rather than a per-file route indicator. The source already exposes `MTP::Instance::mainDcId()`, `mainDcIdValue()`, and `dctransport()`; this is display-only and does not alter routing or protocol behavior.
  - Upstream implementation: [settings_advanced.cpp at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/settings/sections/settings_advanced.cpp)
  - MTProto API: [mtp_instance.h at v7.3.1](https://github.com/telegramdesktop/tdesktop/blob/v7.3.1/Telegram/SourceFiles/mtproto/mtp_instance.h)

## Reviewed candidates

| Idea | Source-level feasibility | Recommendation |
| --- | --- | --- |
| Display current DC and transport | Main DC and current transport are already exposed to the settings UI. | Implemented in patch 0006. |
| Add DC-by-DC latency and availability diagnostics | SereinGram implements probes for DC1–DC5 using Telegram Desktop's `MTP::details::AbstractConnection`, with a 10 second timeout and the active non-Web proxy. It marks the account's main DC and can recheck. This is richer than patch 0006's account-DC label, but creates parallel network probes and needs lifecycle, proxy, cancellation, and localization review. | Strong next candidate after the UI patch builds. Test direct, SOCKS/HTTP, MTProxy, Web proxy, offline, and proxy-switch cases. |
| Offer an opt-in faster transfer profile | SereinGram's public source routes a device setting through small hooks: start at up to four download sessions, start with the maximum per-session download window, and multiply the upload window by four; upstream still caps download sessions at eight and manages retries/timeouts. This changes transfer pressure and can help high-latency routes, but can increase memory, contention, or server throttling. Telegram's API requires respecting server-provided download queue limits. | Promising next patch with an off-by-default toggle. Port only after checking the exact v7.3.1 queue and backoff code, then benchmark direct/proxy and high/low RTT before recommending it. |
| Add download speed/ETA visibility | File loading already tracks progress; a speed estimate needs smoothing and clear handling of paused, resumed, and cached downloads. | Low-risk UI feature, but audit the existing Downloads section to avoid duplicate status. |
| Automatic proxy/DC switching | Proxy and DC selection are handled in core MTProto code, where retries and authorization migration are security- and correctness-sensitive. | Do not change routing automatically without a detailed state-machine design and integration tests. |

## Third-party reference review

AyuGram Desktop, Kotatogram, and SereinGram are public Telegram Desktop based projects. Kotatogram documents local folders, a compact chat list, custom fonts, multi-chat forwarding, and proxy auto-rotation. SereinGram provides inspectable source for a DC status panel and an opt-in transfer profile. Its transfer profile changes starting concurrency/window sizes through narrow hooks, while Telegram Desktop retains the existing session manager and retry logic. These projects demonstrate source-level approaches, but their code targets different upstream revisions and is not copied wholesale. This is a focused source review, not an exhaustive audit of every fork.

- [AyuGram Desktop source](https://github.com/AyuGram/AyuGramDesktop)
- [Kotatogram Desktop README and feature list](https://github.com/kotatogram/kotatogram-desktop)
- [SereinGram feature matrix](https://github.com/eltavine/SereinGram/blob/main/docs/serein/features.md)
- [SereinGram transfer hooks](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/network/transfer.cpp)
- [SereinGram DC status probe](https://github.com/eltavine/SereinGram/blob/main/Telegram/SourceFiles/serein/network/dc_status.cpp)

## Validation status

- Patch transformation uses the repository's strict semantic patch tool and is anchored to the pinned upstream v7.3.1 source.
- The branch workflow's exact patch-count checks have been updated from five to six.
- Local build and compiler validation have not yet been run for this added UI patch. GitHub Actions has not been started.
