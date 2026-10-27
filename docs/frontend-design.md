# Frontend visual direction

Reference: Anthony's dashboard image supplied on 2026-10-26. Preserve PropPilot's project name while adopting its navy navigation rail, light content canvas, property-photo header, blue actions, rounded metric cards, maintenance table, and right-hand circular assessment overview.

Adapt reference elements to actual capabilities:

| Reference element | Current implementation |
| --- | --- |
| Ticket/urgency KPI cards | Actual session analysis/category counts; ticket metric is unavailable |
| Urgent attention strip | Useful sample descriptions that fill the assistant composer |
| Ticket table | Actual successful session requests and their model classifications |
| Triage confidence chart | Actual category distribution; no confidence interpretation |
| New request | Opens a live AI assistant drawer |
| Account/navigation | Development workspace identity and functioning local sections; no authentication claim |

## Assets

`frontend/public/property-hero.jpg`: photograph by Matt Hardison, downloaded from Unsplash for the residential header. Source: [A large brick house with two garages](https://unsplash.com/photos/a-large-brick-house-with-two-garages-NAu6i-LpqWg). Download URL uses image ID `photo-1642775955817-e6613766851c` with crop/quality parameters. This is decorative imagery, not a claim that the property is managed by this application.

Icons: `lucide-react`, pinned in the frontend package manifest. Typography: DM Sans and Manrope from Google Fonts, with local sans-serif fallbacks. Font loading is optional; the image is stored locally and no external font request carries maintenance text.

## Development limits

The design is a foundation for later persisted tickets and urgency predictions. Session-only activity deliberately resets on refresh. No mock requests are shipped as live data. Browser tests may intercept API requests, but test results are separated from real-cloud evidence.
