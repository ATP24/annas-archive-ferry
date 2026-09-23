# Live-site verification record

**Date: 2026-09-23.** This is a point-in-time end-to-end check, not a guarantee of future site availability. The test used a *Pride and Prejudice* EPUB listed as a Project Gutenberg edition.

| Stage | Observation |
| --- | --- |
| Environment | Python, browser, dependencies, and mirror connectivity available |
| Search | Several EPUB editions returned for user selection |
| Probe | Server reported 24,837,384 bytes and byte-range support |
| Download | Synchronous transfer completed with observed speed and changing ETA |
| Integrity | MD5 `fb73d4fd19b0da98923365cb85a03a2b` matched the catalog |
| Format | EPUB ZIP passed integrity check; 182 entries; MIME file `application/epub+zip` |
| Cleanup | No `.part` or `.part.meta` remained after success |
| Machine output | `probe --json` stdout parsed directly; logs appeared on stderr |

One download took about 25 seconds. Speed varies by mirror, route, proxy, and network. No temporary signed link is included here.

Offline tests use simulated responses to cover length mismatch, MD5 mismatch, byte ranges, partial-file identity, and JSON output:

```bash
python -m unittest discover -s tests -v
```
