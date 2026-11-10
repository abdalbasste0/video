# Fonts (all SIL Open Font License 1.1 — free for commercial video use)

| File | Used for | Source |
|------|----------|--------|
| NotoSansArabic-Bold.ttf / -Regular.ttf | Arabic titles / text | Noto Project (notofonts/arabic) |
| Fredoka-Bold.ttf / -Medium.ttf | English, French, Spanish | Fredoka Project (Google Fonts) |

Arabic note: arabic-reshaper outputs "presentation form" letters (U+FB50–U+FEFF).
A font must contain those glyphs or you will see empty boxes. Noto Sans Arabic does.
`python make.py doctor` checks every language font for missing glyphs.
