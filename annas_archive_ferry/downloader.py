"""Validated, resumable document downloads."""

import hashlib
import ipaddress
import json
import os
import re
import socket
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests

MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
CONTENT_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+|\*)$")
EXTENSIONS = {".pdf", ".djvu", ".epub", ".mobi", ".azw3", ".fb2", ".cbr", ".cbz", ".txt"}


def validate_md5(value):
    if value is not None and not MD5_RE.fullmatch(value):
        raise ValueError("MD5 必须是 32 位十六进制字符串")


def validate_public_https(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("下载地址必须是不含凭据的 HTTPS URL")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("下载地址解析到非公网地址")
    return url


def checked_get(session, url, **kwargs):
    for _ in range(6):
        validate_public_https(url)
        response = session.get(url, allow_redirects=False, **kwargs)
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        location = response.headers.get("Location")
        response.close()
        if not location:
            raise ValueError("重定向缺少 Location")
        url = urljoin(url, location)
    raise ValueError("重定向次数过多")


def target_path(url, output_dir, name=None, md5=None):
    source_name = Path(unquote(urlparse(url).path)).name
    extension = Path(source_name).suffix.lower()
    if extension not in EXTENSIONS:
        raise ValueError("无法从下载地址判断支持的文件格式")
    if name:
        stem = Path(name).stem if Path(name).suffix.lower() in EXTENSIONS else name
    else:
        stem = Path(source_name).stem or md5
    stem = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "_", stem or "download").strip(" .")
    if not stem or stem in {".", ".."}:
        raise ValueError("文件名无效")
    return Path(output_dir).expanduser() / (stem + extension)


def file_md5(path):
    digest = hashlib.md5()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_document(path, md5=None, file_type=None):
    if path.stat().st_size == 0:
        raise ValueError("下载文件为空")
    if md5 and file_md5(path).lower() != md5.lower():
        raise ValueError("文件 MD5 与书目记录不符")
    if (file_type or path.suffix).lower() == ".pdf":
        import fitz
        with fitz.open(path) as document:
            if document.page_count < 1:
                raise ValueError("PDF 没有页面")


def download(url, output_dir, name=None, md5=None, proxy=None, session=None, progress=None):
    """Download to a .part file; publish only after transport and file checks pass."""
    validate_md5(md5)
    validate_public_https(url)
    destination = target_path(url, output_dir, name, md5)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if md5 and destination.exists():
        try:
            validate_document(destination, md5)
            return str(destination)
        except Exception:
            pass

    partial = destination.with_name(destination.name + ".part")
    metadata_path = destination.with_name(destination.name + ".part.meta")
    identity = md5.lower() if md5 else hashlib.sha256(url.encode("utf-8")).hexdigest()
    previous = None
    if metadata_path.exists():
        try:
            previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    if partial.exists() and (not previous or previous.get("identity") != identity):
        partial.unlink()
        metadata_path.unlink(missing_ok=True)
        previous = None
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "AnnaArchiveFerry/1.1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        if previous and previous.get("validator"):
            headers["If-Range"] = previous["validator"]
    client = session or requests.Session()
    if proxy:
        client.proxies.update({"http": proxy, "https": proxy})
    try:
        with checked_get(client, url, headers=headers, stream=True, timeout=(15, 60)) as response:
            if response.status_code not in (200, 206):
                response.raise_for_status()
                raise ValueError(f"意外的 HTTP 状态: {response.status_code}")
            mode = "wb"
            total = None
            if response.status_code == 206:
                match = CONTENT_RANGE_RE.fullmatch(response.headers.get("Content-Range", ""))
                if not match or int(match.group(1)) != offset:
                    raise ValueError("续传的 Content-Range 与本地文件不匹配")
                first, last = int(match.group(1)), int(match.group(2))
                if last < first:
                    raise ValueError("无效的 Content-Range")
                if match.group(3) != "*":
                    total = int(match.group(3))
                    if total <= last:
                        raise ValueError("无效的文件总长度")
                mode = "ab" if offset else "wb"
            validator = response.headers.get("ETag") or response.headers.get("Last-Modified")
            if offset and previous and previous.get("validator") and validator != previous["validator"]:
                raise ValueError("续传资源标识已变化")
            metadata_path.write_text(json.dumps({"identity": identity, "validator": validator}), encoding="utf-8")
            expected_body = response.headers.get("Content-Length")
            expected_body = int(expected_body) if expected_body is not None else None
            if md5 is None and expected_body is None and total is None:
                raise ValueError("未提供 MD5 且服务器未提供长度，无法验证下载完整性")
            received = 0
            started = time.monotonic()
            last_report = started
            last_bytes = 0
            full_size = total if total is not None else (expected_body if response.status_code == 200 else None)
            with open(partial, mode) as stream:
                for block in response.iter_content(chunk_size=512 * 1024):
                    if block:
                        stream.write(block)
                        received += len(block)
                        now = time.monotonic()
                        if progress and now - started >= 3 and now - last_report >= 5:
                            rate = (received - last_bytes) / (now - last_report)
                            completed = (offset if mode == "ab" else 0) + received
                            remaining = (full_size - completed) / rate if full_size and rate > 0 else None
                            progress(completed, full_size, rate, remaining)
                            last_report, last_bytes = now, received
            if expected_body is not None and received != expected_body:
                raise ValueError("实际接收字节数与 Content-Length 不符")
            if total is not None and partial.stat().st_size != total:
                raise ValueError("续传后文件长度与 Content-Range 不符")
        try:
            validate_document(partial, md5, destination.suffix)
        except Exception:
            partial.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            raise
        os.replace(partial, destination)
        metadata_path.unlink(missing_ok=True)
        return str(destination)
    except Exception:
        # Keep a partial transfer for a later retry; never expose it as completed.
        raise
