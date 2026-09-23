import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from annas_archive_ferry.downloader import download, validate_md5, validate_public_https


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self.body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size):
        yield self.body

    def raise_for_status(self):
        raise RuntimeError(f"HTTP {self.status_code}")


class DownloadTests(unittest.TestCase):
    URL = "https://example.com/book.epub"
    DATA = b"a complete sample document"

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.md5 = hashlib.md5(self.DATA).hexdigest()

    def run_download(self, response):
        with patch("annas_archive_ferry.downloader.validate_public_https"), patch(
            "annas_archive_ferry.downloader.checked_get", return_value=response
        ):
            return download(self.URL, self.folder.name, md5=self.md5)

    def write_partial(self, data, identity=None):
        (Path(self.folder.name) / "book.epub.part").write_bytes(data)
        (Path(self.folder.name) / "book.epub.part.meta").write_text(
            json.dumps({"identity": identity or self.md5, "validator": None}), encoding="utf-8"
        )

    def test_valid_download_is_published(self):
        result = self.run_download(FakeResponse(200, self.DATA, {"Content-Length": str(len(self.DATA))}))
        self.assertEqual(Path(result).read_bytes(), self.DATA)
        self.assertFalse(Path(result + ".part").exists())

    def test_truncated_body_is_not_published(self):
        with self.assertRaisesRegex(ValueError, "Content-Length"):
            self.run_download(FakeResponse(200, self.DATA[:4], {"Content-Length": str(len(self.DATA))}))
        self.assertFalse((Path(self.folder.name) / "book.epub").exists())

    def test_invalid_md5_is_not_published(self):
        with self.assertRaisesRegex(ValueError, "MD5"):
            self.run_download(FakeResponse(200, b"wrong"))
        self.assertFalse((Path(self.folder.name) / "book.epub").exists())

    def test_resume_checks_range_and_total(self):
        self.write_partial(self.DATA[:4])
        rest = self.DATA[4:]
        response = FakeResponse(206, rest, {
            "Content-Range": f"bytes 4-{len(self.DATA)-1}/{len(self.DATA)}",
            "Content-Length": str(len(rest)),
        })
        result = self.run_download(response)
        self.assertEqual(Path(result).read_bytes(), self.DATA)

    def test_wrong_range_does_not_publish(self):
        self.write_partial(self.DATA[:4])
        with self.assertRaisesRegex(ValueError, "Content-Range"):
            self.run_download(FakeResponse(206, self.DATA[4:], {"Content-Range": "bytes 0-9/10"}))
        self.assertFalse((Path(self.folder.name) / "book.epub").exists())

    def test_ignoring_range_restarts_cleanly(self):
        self.write_partial(b"old")
        result = self.run_download(FakeResponse(200, self.DATA, {"Content-Length": str(len(self.DATA))}))
        self.assertEqual(Path(result).read_bytes(), self.DATA)

    def test_other_resource_partial_is_discarded(self):
        self.write_partial(b"other", identity="different")
        result = self.run_download(FakeResponse(200, self.DATA, {"Content-Length": str(len(self.DATA))}))
        self.assertEqual(Path(result).read_bytes(), self.DATA)

    def test_unidentified_partial_is_discarded(self):
        (Path(self.folder.name) / "book.epub.part").write_bytes(b"unknown")
        result = self.run_download(FakeResponse(200, self.DATA, {"Content-Length": str(len(self.DATA))}))
        self.assertEqual(Path(result).read_bytes(), self.DATA)

    def test_direct_url_without_length_is_rejected(self):
        with patch("annas_archive_ferry.downloader.validate_public_https"), patch(
            "annas_archive_ferry.downloader.checked_get", return_value=FakeResponse(200, self.DATA)
        ):
            with self.assertRaisesRegex(ValueError, "无法验证"):
                download(self.URL, self.folder.name)

    def test_bad_md5_and_local_url_rejected(self):
        with self.assertRaises(ValueError):
            validate_md5("../bad")
        with self.assertRaises(ValueError):
            validate_public_https("http://127.0.0.1/file")


if __name__ == "__main__":
    unittest.main()
