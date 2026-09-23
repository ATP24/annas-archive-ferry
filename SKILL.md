---
name: annas-archive-ferry
description: Search and compare book records on Anna's Archive, inspect file size, download a selected document, and convert downloaded DjVu to PDF when ddjvu is available. Use when the user asks to search Anna's Archive, compare editions, download a record, or convert its DjVu file.
---

# Anna's Archive Ferry

Use the CLI in `scripts/ferry_engine.py`. Check [README.md](README.md) for installation and platform requirements.

## Workflow

1. Run `python scripts/ferry_engine.py search "<title or author>" --json`. Present plausible matches with title, format, size, and MD5. Do not assume the first result is the right edition.
2. After the user selects a record, run `python scripts/ferry_engine.py probe --md5 <32-hex-MD5> --json`. Report the returned size. If the server provides no size, say so. The probe does not measure speed or predict a completion time.
3. Download only the selected record to the location the user requested. If the download is large, time consuming, or the destination is unclear, get the user's decision first. Run `python scripts/ferry_engine.py download --md5 <MD5> --output "<directory>"`.
4. Report a file only when the command succeeds. The CLI verifies the MD5 against the selected record and opens PDFs before publishing them. For DjVu, it converts to PDF when `ddjvu` is available and `auto_convert_djvu` is enabled; if conversion fails, report the retained DjVu rather than promising a PDF. On transfer failure, explain the error and leave any `.part` file for a later retry.

## Boundaries

- This CLI runs synchronously. Download progress estimates use observed transfer speed and can change. Do not promise background execution, automatic wakeup, or a fixed completion time.
- Site layout, mirrors, and access challenges can change. Stop and explain when a link cannot be resolved; do not claim success based on a partial file.
- `doctor --fix` installs Python packages and changes the environment. Use it only when the user authorizes installation.
- Follow the user's permissions and applicable access rules for the requested material.
