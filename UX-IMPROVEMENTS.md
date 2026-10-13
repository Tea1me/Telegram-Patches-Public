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
| Add a one-click connection diagnostic | Proxy settings already have a connection-check flow. A useful addition would show latency and distinguish proxy failure from Telegram reachability, but needs UI and timeout/error-path review. | Good next candidate; test with direct, SOCKS/HTTP, and MTProxy connections. |
| Increase parallel downloads or chunk concurrency | The download path uses MTProto sessions and server-directed CDN behavior. Telegram's API instructs clients to cap concurrent downloads according to server-provided small/large queue limits. Raising concurrency blindly can increase throttling, memory use, and contention; it cannot improve a bandwidth-limited route. | Do not change defaults speculatively. First benchmark the same large file over direct and proxied routes and inspect server/DC responses. |
| Add download speed/ETA visibility | File loading already tracks progress; a speed estimate needs smoothing and clear handling of paused, resumed, and cached downloads. | Low-risk UI feature, but requires auditing the existing Downloads section before adding duplicate status. |
| Automatic proxy/DC switching | Proxy and DC selection are handled in core MTProto code, where retries and authorization migration are security- and correctness-sensitive. | Do not change routing automatically without a detailed state-machine design and integration tests. |

## Third-party reference review

AyuGram Desktop and Kotatogram are public Telegram Desktop forks. The reviewed Kotatogram README lists local folders, compact chat list, custom fonts, and multi-chat forwarding; these are practical UI-level patterns, but not direct network or download-speed improvements. The search did not surface a directly reusable DC-status or safe download-concurrency implementation in those forks. The DC display here therefore uses Telegram Desktop's own exposed API and existing Advanced settings row rather than importing unrelated fork code. This is a focused source review, not an exhaustive audit of every fork.

- [AyuGram Desktop source](https://github.com/AyuGram/AyuGramDesktop)
- [Kotatogram Desktop README and feature list](https://github.com/kotatogram/kotatogram-desktop)

## Validation status

- Patch transformation uses the repository's strict semantic patch tool and is anchored to the pinned upstream v7.3.1 source.
- The branch workflow's exact patch-count checks have been updated from five to six.
- Local build and compiler validation have not yet been run for this added UI patch. GitHub Actions has not been started.
