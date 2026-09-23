# Anna's Archive Ferry

A local CLI and agent skill for searching Anna's Archive records, comparing editions, probing download metadata, and saving a selected document.

[中文说明](README.md) · [Skill instructions](SKILL.md) · [Issues](https://github.com/ATP24/annas-archive-ferry/issues)

## Install

Python 3.9+ is required. Searching and link resolution require a Playwright-compatible browser. DjVu-to-PDF conversion additionally requires `ddjvu`.

```bash
git clone https://github.com/ATP24/annas-archive-ferry.git
cd annas-archive-ferry
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -e .
annas-ferry doctor
```

If needed, install Chromium with `python -m playwright install chromium`.

## Use

```bash
annas-ferry search "title or author" --limit 5 --json
annas-ferry probe --md5 <32-character-MD5> --json
annas-ferry download --md5 <32-character-MD5> --output "./downloads"
```

Choose the right record before downloading. Probe does not fetch a sample or predict download time. During a download, remaining time is updated from observed transfer speed. Downloads run synchronously. The tool keeps incomplete transfers in `.part` files with `.part.meta` resource identity, validates the transfer length and catalog MD5, and opens PDFs before publishing the final file. Direct URL downloads without an MD5 require a server-provided length.

Place the repository in an agent's supported skills directory with `SKILL.md` at its top level. Agent discovery and execution permissions depend on that agent's documentation.

Site layout, mirrors, challenges, and availability can change. Only access material you are permitted to use. See [the Chinese README](README.md) for current limitations, development instructions, and licensing.
