# CapCut UI screenshots (only for `render.backend: capcut_ui`)

CapCut's buttons move between versions, so the exporter finds them by image.
Take tight screenshots (Win+Shift+S) at your normal display scaling and save them here:

- `export_button.png`  — the blue **Export** button in the editor's top-right corner
- `export_confirm.png` — the **Export** button inside the export dialog

Set the export settings once in CapCut (1080p, 30 fps, H.264/HEVC, recommended bitrate);
CapCut remembers them. Exports must land in `render.capcut_export_dir` (config.yaml).
