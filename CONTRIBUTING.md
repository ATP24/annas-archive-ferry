# Contributing to Anna's Archive Ferry (安娜书渡)

Thank you for your interest in contributing to **Anna's Archive Ferry**! This guide outlines how to get started, make contributions, and submit Pull Requests.

---

## 🛠️ Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/ATP24/annas-archive-ferry.git
   cd annas-archive-ferry
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r scripts/requirements.txt
   ```

4. **Verify Environment**:
   ```bash
   python scripts/ferry_engine.py doctor
   ```

---

## 🌿 Branching & Git Workflow

- Main development branch is `main`.
- Create descriptive feature or bugfix branches:
  - `feat/feature-name`
  - `fix/bug-description`
  - `docs/documentation-update`
- Ensure your commits follow conventional commit formats:
  - `feat: add support for EPUB cover extraction`
  - `fix: handle 429 rate limit backoff in CDN sniffer`
  - `docs: clarify probe protocol in README`

---

## 🧪 Testing Guidelines

Before opening a PR, ensure:
1. `python scripts/ferry_engine.py --help` runs without error across supported Python versions (3.8+).
2. Code follows standard PEP 8 formatting conventions.
3. Any new features are accompanied by updates in `SKILL.md`, `README.md`, and `README_EN.md`.

---

## 📬 Submitting a Pull Request

1. Push your branch to your forked repository.
2. Open a Pull Request against `main`.
3. Provide a clear explanation of what changed and reference any relevant issues.
4. Verify that the GitHub Actions CI workflow passes.
