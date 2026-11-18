# Series

Each series lives in `series/<slug>/`:

- `bible.md`: story summary, characters (and which look each one uses), places, and the episode plan.
- `ep01.json`, `ep02.json`, ...: each episode is a normal story file plus a `series` field:

```json
"series": {
  "name": "The Vanishing of Room 4B",
  "part": 2,
  "episode_title": "The Eleventh Viewer",
  "previously": "A streamer vanished live at 3:17 a.m. ...",
  "final": false
}
```

The render adds automatically: a "Previously..." recap (from part 2 on), a title card with the
series name and part number, and "To be continued..." at the end ("The end." when `final` is true).
The YouTube title becomes: `SERIES NAME | Part 2: Episode title`, and every part goes in one playlist.

Episode length: 3–5 minutes (better for watch time and ad revenue than 2-minute videos),
and each episode ends on a strong cliffhanger.
