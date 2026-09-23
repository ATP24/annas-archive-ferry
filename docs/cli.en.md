# CLI and configuration

Run commands in an active Python 3.9+ environment. `annas-ferry` is installed by `python -m pip install -e .`; from a clone, `python scripts/ferry_engine.py` also works.

| Command | Purpose | Useful options |
| --- | --- | --- |
| `annas-ferry doctor` | Check dependencies, browser, proxy, and mirror | `--fix` installs missing Python packages |
| `annas-ferry search "keywords"` | List candidate editions | `--ext pdf`, `--limit 5`, `--json` |
| `annas-ferry probe --md5 <MD5>` | Resolve a link and inspect server metadata | `--json` |
| `annas-ferry download --md5 <MD5>` | Download and verify a catalog item | `--output`, `--name`, `--quiet` |
| `annas-ferry download --direct-url <URL>` | Download from a known public HTTPS URL | `--output`, `--name` |

`search` and `probe` support `--json`: stdout contains one JSON value, stderr contains diagnostics. Failures return a nonzero exit code. `download` has no JSON mode. Probe does not sample speed; `estimated_minutes` is `null`. Non-quiet downloads show observed speed and a changing remaining-time estimate.

## Local files

The default output directory is `~/Downloads/AnnasFerry`; override it with `--output`. Incomplete transfers use `<name>.part` and `<name>.part.meta`. Do not treat `.part` as a final file. Successful downloads validate transfer length and catalog MD5, and PDFs are checked for readable pages. DjVu-to-PDF conversion is enabled by default (`auto_convert_djvu: true`) and needs DjVuLibre's `ddjvu`. The generated PDF is opened for validation, while the original DjVu remains. Missing tools or conversion failures return the DjVu. Lossless conversion and searchable-text preservation are not guaranteed.

## Configuration

User settings live in `~/.annas_ferry/config.json`; cache files live in `~/.annas_ferry_cache/`. Defaults are defined in `annas_archive_ferry/config.py`.

```json
{
  "primary_mirror": "https://<trusted-mirror>",
  "proxy": "auto",
  "default_download_dir": "~/Downloads/AnnasFerry",
  "auto_convert_djvu": true,
  "headless": true
}
```

Automatic proxy detection checks environment variables and common local ports. Only configure trusted mirrors and proxies. Cached links can contain temporary access parameters: do not publish full links or cache files.

Direct URLs must use HTTPS and resolve to public addresses; redirects are checked too. Without an MD5, a server-provided length is required, but length verification is weaker than a content hash.
