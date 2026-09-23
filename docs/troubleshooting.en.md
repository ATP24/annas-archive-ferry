# Troubleshooting

## `annas-ferry` is not found

Activate the virtual environment and run `python -m pip install -e .` in it. From the repository directory, `python scripts/ferry_engine.py --help` works without the installed command.

## Browser unavailable

Run `annas-ferry doctor`. A compatible Chrome or Edge can be used, or install Chromium with `python -m playwright install chromium`. CI checks offline behavior; it does not prove this machine can reach the live site.

## Search finds nothing or fails

An empty array `[]` means parsing found no result. A nonzero exit code means the search failed. Try a shorter title and check your network and proxy. Page or challenge changes may require a parser update.

## Probe cannot get size or link

The server may omit `Content-Length`, or the access challenge may fail. Probe does not fetch a sample to measure speed. Temporary links expire; retry inspection later.

## A `.part` file remains

Interrupted transfers remain for a retry against the same resource. If the server ignores byte ranges, the tool starts again. A partial file is never a delivered result.

## JSON cannot be parsed

Parse stdout only. Do not merge stderr into it. `search` and `probe` should each emit one JSON value on stdout. Report any reproducible log contamination.

When filing an issue, include OS, Python version, command, exit code, relevant error, proxy presence, and reproduction steps. Remove signed URLs, credentials, private paths, and file content. See [Security](../SECURITY.md).
