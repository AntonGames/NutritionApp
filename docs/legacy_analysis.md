# Why the previous approach was fragile

The files in [`nutrition_tracker_system_bundle`](../nutrition_tracker_system_bundle) show a Google Apps Script based design:

- [`Code.gs`](../nutrition_tracker_system_bundle/Code.gs) turned the spreadsheet into a web app.
- [`openapi.yaml`](../nutrition_tracker_system_bundle/openapi.yaml) exposed it as a single GPT Action endpoint.
- [`README_setup.md`](../nutrition_tracker_system_bundle/README_setup.md) depended on manual deployment inside Google Apps Script.

That approach was useful as a prototype, but it had several weak points for the workflow you actually want:

1. The spreadsheet was the database.
   Excel/Sheets are great for reporting, but they are a poor system of record when multiple automations start writing to them.

2. There was no real photo-upload flow.
   The old API accepted already-structured meal JSON, but it did not accept an uploaded image and turn it into components.

3. It depended on the Apps Script web-app behavior.
   That layer is okay for hobby automations, but it is harder to secure, debug, test, and monitor than a normal HTTP service on your own Pi.

4. The workbook design was English-first and template-driven.
   It created per-day sheets and relied on fixed ranges, which becomes awkward once the log grows.

5. There was no durable local storage.
   If you ever want better reporting, corrections, or Home Assistant integration, you really want a database first and an Excel export second.

The new implementation in this repo fixes that by using:

- FastAPI for a normal upload/API layer
- SQLite as the durable source of truth
- an automatically regenerated Russian-friendly Excel workbook
- optional Home Assistant REST hooks

