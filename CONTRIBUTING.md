# Contributing

Anna's Archive Ferry is a Python CLI with an Agent Skill entrypoint. Python 3.9+ is supported.

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q annas_archive_ferry scripts tests
```

`SKILL.md` uses `scripts/ferry_engine.py` so the cloned repository can run without an editable install. The installed command is `annas-ferry`. Keep both entrypoints working when changing CLI behavior.

Before opening a pull request, update the relevant documentation and test observable behavior. Download tests should cover response status, byte ranges, partial files, integrity checks, and failure exit codes. Avoid tests that depend on live site availability; report live compatibility checks separately.
