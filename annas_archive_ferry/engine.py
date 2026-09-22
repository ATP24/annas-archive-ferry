"""
Anna's Archive Ferry (安娜书渡) - Core Engine
=============================================
Automated book retrieval, smart disambiguation, local neural OCR,
and single-stream streaming download engine.

Licensed under MIT. Copyright (c) 2026 ATP24.
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
import shutil
import urllib.parse
from pathlib import Path
import urllib3
urllib3.disable_warnings()

from .config import (
    load_config,
    save_dynamic_config,
    CACHE_DIR,
    USER_CONFIG_DIR
)

# Defensive UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CONFIG = load_config()

def detect_proxy():
    """Smartly detects the best HTTP/HTTPS proxy to use."""
    cfg_proxy = CONFIG.get("proxy", "auto")
    if cfg_proxy and cfg_proxy != "auto":
        return cfg_proxy

    for env_var in ["HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"]:
        val = os.environ.get(env_var)
        if val:
            return val

    import socket
    test_ports = [7890, 10808, 10809, 1080, 20171]
    for port in test_ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            res = s.connect_ex(("127.0.0.1", port))
            if res == 0:
                s.close()
                return f"http://127.0.0.1:{port}"
        except Exception:
            pass
        finally:
            s.close()
    return None

def detect_browser_channel():
    """Detects if Edge or Chrome is installed on the host system across OS platforms."""
    if sys.platform == "win32":
        edge_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
        ]
        for p in edge_paths:
            if os.path.exists(p):
                return "msedge"
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
        ]
        for p in chrome_paths:
            if os.path.exists(p):
                return "chrome"
    elif sys.platform == "darwin":
        if os.path.exists("/Applications/Google Chrome.app"):
            return "chrome"
        if os.path.exists("/Applications/Microsoft Edge.app"):
            return "msedge"
    elif sys.platform.startswith("linux"):
        for b in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
            if shutil.which(b):
                return "chrome"
    return None

def find_djvu_tool():
    """Finds ddjvu executable for lossless DjVu-to-PDF transcoding."""
    p = shutil.which("ddjvu") or shutil.which("ddjvu.exe")
    if p:
        return p
    home = Path.home()
    candidates = [
        home / "djvulibre" / "ddjvu.exe",
        Path(r"C:\Program Files\DjVuLibre\ddjvu.exe"),
        Path(r"C:\Program Files (x86)\DjVuLibre\ddjvu.exe"),
        Path("/usr/bin/ddjvu"),
        Path("/usr/local/bin/ddjvu"),
        Path("/opt/homebrew/bin/ddjvu")
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None

def discover_beacon_mirrors():
    """Recovers alive mirrors from external official beacons when primary fails."""
    import requests
    proxy = detect_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    beacons = CONFIG.get("beacons", ["https://shadowlibraries.github.io/DirectDownloads/AnnasArchive/"])

    print("[*] 正在从官方信标获取存活镜像...", flush=True)
    for beacon in beacons:
        try:
            r = requests.get(beacon, proxies=proxies, timeout=6.0, verify=False)
            if r.status_code == 200:
                found = re.findall(r"https://annas-archive\.[a-z]{2,4}", r.text)
                if found:
                    unique = list(dict.fromkeys(found))
                    print(f"[+] 信标捕获最新可用镜像: {unique}", flush=True)
                    save_dynamic_config({
                        "primary_mirror": unique[0],
                        "official_fallbacks": unique[1:]
                    })
                    CONFIG["primary_mirror"] = unique[0]
                    CONFIG["official_fallbacks"] = unique[1:]
                    return unique[0]
        except Exception:
            pass
    return None

def get_active_mirror():
    """Returns the primary locked mirror; triggers automatic fallback if offline."""
    mirror = CONFIG.get("primary_mirror", "https://zh.annas-archive.gl")
    import requests
    proxy = detect_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        r = requests.head(mirror, proxies=proxies, timeout=4.0, verify=False, allow_redirects=True)
        if r.status_code in (200, 301, 302, 403):
            return mirror
    except Exception:
        pass

    # Fallback to secondary official mirrors
    fallbacks = CONFIG.get("official_fallbacks", [])
    for fb in fallbacks:
        try:
            r = requests.head(fb, proxies=proxies, timeout=4.0, verify=False, allow_redirects=True)
            if r.status_code in (200, 301, 302, 403):
                print(f"[!] 主站响应受阻，自动故障转移至可用备份镜像: {fb}", flush=True)
                save_dynamic_config({"primary_mirror": fb})
                CONFIG["primary_mirror"] = fb
                return fb
        except Exception:
            pass

    # Beacon discovery as final safeguard
    beacon_mirror = discover_beacon_mirrors()
    return beacon_mirror or mirror

def bypass_ddos_guard(page, ocr=None):
    """Automatically navigates past DDoS-Guard challenges with local neural OCR."""
    for _ in range(15):
        t = page.title().strip()
        if "DDoS-Guard" not in t and "DDOS-GUARD" not in t and not t.startswith("Loading") and t != "":
            return True
        print(f"  [*] 处理安全防护 (状态: {t})...", flush=True)
        frame = page.frame_locator("#ddg-iframe")
        try:
            frame.locator(".ddg-captcha__checkbox").click(timeout=3000)
            page.wait_for_timeout(2000)
        except Exception:
            pass

        try:
            c_img = frame.locator(".ddg-modal__captcha-image")
            if c_img.is_visible():
                if not ocr:
                    import ddddocr
                    ocr = ddddocr.DdddOcr(show_ad=False)
                code = ocr.classification(c_img.screenshot())
                inp = frame.locator(".ddg-modal__input")
                inp.fill(code)
                inp.press("Enter")
                page.wait_for_timeout(3500)
            else:
                page.wait_for_timeout(1500)
        except Exception:
            page.wait_for_timeout(1500)

    t = page.title().strip()
    return "DDoS-Guard" not in t and "DDOS-GUARD" not in t and not t.startswith("Loading")

def run_doctor(fix=False):
    """Performs an extensive environment and network connectivity diagnosis."""
    print("=" * 65)
    print("  [安娜书渡 / Anna's Archive Ferry] 环境与镜像诊断")
    print("=" * 65)
    all_ok = True
    py_ver = sys.version.split()[0]
    print(f"  [+] Python 版本: {py_ver} -> 正常")

    req_pkgs = {
        "requests": "requests",
        "playwright": "playwright",
        "ddddocr": "ddddocr",
        "fitz": "PyMuPDF",
        "bs4": "beautifulsoup4"
    }
    missing_pkgs = []
    for mod, pkg in req_pkgs.items():
        try:
            __import__(mod)
            print(f"  [+] 依赖库 {pkg:16s} -> 已安装")
        except ImportError:
            print(f"  [-] 依赖库 {pkg:16s} -> 未安装")
            missing_pkgs.append(pkg)
            all_ok = False

    if missing_pkgs and fix:
        print(f"\n[*] 正在自动修复并安装缺失依赖: {missing_pkgs} ...")
        for pkg in missing_pkgs:
            cmd = [sys.executable, "-m", "pip", "install", pkg]
            print(f"  -> 执行: {' '.join(cmd)}")
            res = subprocess.run(cmd)
            if res.returncode != 0:
                # Fallback to Tsinghua mirror
                cmd.extend(["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
                subprocess.run(cmd)

    browser_ch = detect_browser_channel()
    if browser_ch:
        print(f"  [+] 系统原生浏览器探针   -> 已检测到 {browser_ch.upper()} (免额外下载 Chromium)")
    else:
        print(f"  [?] 未检测到系统 Edge/Chrome，将依赖 Playwright 内置 Chromium")

    proxy = detect_proxy()
    if proxy:
        print(f"  [+] 本地代理探针         -> 已匹配: {proxy}")
    else:
        print(f"  [!] 本地代理探针         -> 直连模式")

    djvu_tool = find_djvu_tool()
    if djvu_tool:
        print(f"  [+] DjVu 无损转码引擎   -> 已就绪 ({djvu_tool})")
    else:
        print(f"  [?] DjVu 无损转码引擎   -> 未就绪 (仅影响 .djvu 格式转 PDF)")

    curl_bin = shutil.which("curl.exe") or shutil.which("curl")
    if curl_bin:
        print(f"  [+] 系统原生下载引擎     -> 已就绪 ({curl_bin})")
    else:
        print(f"  [-] 系统原生下载引擎     -> 未找到 curl (将使用内置流式下载)")

    print("-" * 65)
    mirror = get_active_mirror()
    print(f"  [*] 检查主站连通性: {mirror} ...")
    import requests
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        t0 = time.time()
        r = requests.head(mirror, proxies=proxies, timeout=5.0, verify=False, allow_redirects=True)
        ms = int((time.time() - t0) * 1000)
        print(f"  [+] 主站响应正常 [{r.status_code}]，延迟: {ms} ms")
    except Exception as e:
        print(f"  [-] 主站连通异常: {e}")
        all_ok = False

    print("=" * 65)
    return all_ok

def search_books(query, ext=None, limit=10, as_json=False):
    """Searches Anna's Archive with locked primary mirror and returns structured results."""
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
    import ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)

    proxy_server = detect_proxy()
    browser_ch = detect_browser_channel()

    launch_args = {
        "headless": CONFIG.get("headless", True),
        "args": ["--disable-blink-features=AutomationControlled"]
    }
    if browser_ch:
        launch_args["channel"] = browser_ch
    if proxy_server:
        launch_args["proxy"] = {"server": proxy_server}

    mirror = get_active_mirror()
    results = []
    print(f"[*] 正在检索: 「{query}」 (站点: {mirror})...", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        search_url = f"{mirror}/search?q={urllib.parse.quote(query)}"
        if ext:
            search_url += f"&ext={urllib.parse.quote(ext)}"

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            bypass_ddos_guard(page, ocr=ocr)
            try:
                page.wait_for_selector('a.js-vim-focus, a[href^="/md5/"]', timeout=12000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            html_content = page.content()
        except Exception as e:
            print(f"[-] 访问异常 ({e})", flush=True)
            browser.close()
            return []

        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")
    seen_md5 = set()
    cards = soup.find_all("a", class_=lambda c: c and "js-vim-focus" in c)
    if not cards:
        cards = soup.find_all("a", href=lambda h: h and h.startswith("/md5/"))

    for a in cards:
        href = a.get("href", "")
        if not href.startswith("/md5/"):
            continue
        md5 = href.replace("/md5/", "").strip()
        if not re.match(r"^[a-f0-9]{32}$", md5) or md5 in seen_md5:
            continue
        seen_md5.add(md5)

        raw_title = a.get_text(strip=True)
        title = raw_title.splitlines()[0] if raw_title else "未知标题"
        parent = a.find_parent("div")
        meta_info = parent.get_text(separator=" | ", strip=True) if parent else ""

        fmt_match = re.search(r'\b(pdf|djvu|epub|mobi|azw3)\b', meta_info, re.IGNORECASE)
        fmt = fmt_match.group(1).upper() if fmt_match else "UNKNOWN"
        size_match = re.search(r'([\d\.]+\s*(?:MB|KB|GB))', meta_info, re.IGNORECASE)
        size_str = size_match.group(1) if size_match else "未知大小"

        results.append({
            "index": len(results) + 1,
            "md5": md5,
            "title": title,
            "format": fmt,
            "size": size_str,
            "meta": meta_info,
            "url": f"{mirror}/md5/{md5}"
        })
        if len(results) >= limit:
            break

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return results

    if not results:
        print(f"[-] 未找到与「{query}」相关的书籍资源。")
        return results

    print(f"\n[+] 找到以下 {len(results)} 个匹配版本：\n")
    print(f"{'序号':<4} | {'格式':<6} | {'大小':<10} | {'标题'}")
    print("-" * 80)
    for r in results:
        print(f"[{r['index']:02d}]  | {r['format']:<6} | {r['size']:<10} | {r['title']}")
        if r['meta']:
            print(f"       详情: {r['meta'][:75]}")
        print(f"       MD5:  {r['md5']}")
    print("-" * 80)
    print("探测指令: python scripts/ferry_engine.py probe --md5 <MD5值>")
    print("下载指令: python scripts/ferry_engine.py download --md5 <MD5值>\n")
    return results

def resolve_direct_url(md5):
    """Sniffs the direct CDN download URL and handles cookie pre-warming."""
    cache_file = CACHE_DIR / f"{md5}.url"
    import requests
    proxy_server = detect_proxy()
    proxies = {"http": proxy_server, "https": proxy_server} if proxy_server else None

    # Check valid cached URL (within 2-hour TTL)
    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if (time.time() - mtime) < 7200:  # 2 hours
                cached_url = cache_file.read_text(encoding="utf-8").strip()
                if cached_url.startswith("http"):
                    r = requests.head(cached_url, proxies=proxies, timeout=5.0, verify=False)
                    if r.status_code in (200, 206, 302):
                        print(f"[+] 命中缓存的有效直链: {cached_url[:70]}...", flush=True)
                        return cached_url
        except Exception:
            pass

    from playwright.sync_api import sync_playwright
    import ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)
    browser_ch = detect_browser_channel()

    launch_args = {
        "headless": CONFIG.get("headless", True),
        "args": ["--disable-blink-features=AutomationControlled"]
    }
    if browser_ch:
        launch_args["channel"] = browser_ch
    if proxy_server:
        launch_args["proxy"] = {"server": proxy_server}

    mirror = get_active_mirror()
    slow_routes = [
        f"{mirror}/slow_download/{md5}/0/0",
        f"{mirror}/slow_download/{md5}/0/1",
        f"{mirror}/slow_download/{md5}/0/2"
    ]

    cdn_url = None
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Pre-warm homepage to acquire cookies and pass DDoS challenges cleanly
        print(f"[*] 预热主站安全信标: {mirror} ...", flush=True)
        try:
            page.goto(mirror, wait_until="domcontentloaded", timeout=35000)
            bypass_ddos_guard(page, ocr=ocr)
        except Exception:
            pass

        for route in slow_routes:
            print(f"[*] 进入慢速免登录通道: {route} ...", flush=True)
            try:
                page.goto(route, wait_until="domcontentloaded", timeout=45000)
                bypass_ddos_guard(page, ocr=ocr)

                for _ in range(40):
                    page.wait_for_timeout(2000)
                    try:
                        links = page.query_selector_all("a")
                        for a in links:
                            href = a.get_attribute("href") or ""
                            text = a.inner_text().strip().lower()

                            # Handle relative URLs cleanly
                            if href.startswith("/"):
                                href = urllib.parse.urljoin(mirror, href)

                            if ('wbsg' in href or 'duxiu_files' in href or href.endswith('.pdf') or 'fast_download' in href or '/dyn/download' in href) and href.startswith('http'):
                                cdn_url = href
                                break
                            if 'download now' in text or '立刻下载' in text or text == '下载':
                                if href.startswith('http'):
                                    cdn_url = href
                                    break
                    except Exception:
                        pass
                    if cdn_url:
                        break
                if cdn_url:
                    break
            except Exception:
                continue
        browser.close()

    if cdn_url:
        try:
            cache_file.write_text(cdn_url, encoding="utf-8")
        except Exception:
            pass
    return cdn_url

def probe_book(md5, as_json=False):
    """Probes file metadata, rate limits, and estimated download duration upfront."""
    import requests
    proxy_server = detect_proxy()
    proxies = {"http": proxy_server, "https": proxy_server} if proxy_server else None

    print(f"[*] 正在前置嗅探书籍直链与体积 (MD5: {md5})...", flush=True)
    cdn_url = resolve_direct_url(md5)
    if not cdn_url:
        print("[-] 直链嗅探失败，请检查网络代理。", flush=True)
        return None

    try:
        r = requests.head(cdn_url, proxies=proxies, timeout=8.0, verify=False, allow_redirects=True)
        size_bytes = int(r.headers.get("content-length", 0))
        size_mb = round(size_bytes / (1024 * 1024), 2)
        accept_ranges = r.headers.get("accept-ranges", "none").strip().lower()

        url_path = urllib.parse.unquote(urllib.parse.urlparse(cdn_url).path)
        filename = Path(url_path).name or f"book_{md5}.pdf"

        # Rate baseline: 55 KB/s
        est_seconds = int(size_bytes / (55 * 1024)) if size_bytes > 0 else 0
        est_minutes = round(est_seconds / 60, 1)

        heavy_threshold = CONFIG.get("heavy_threshold_mb", 30)
        is_heavy = size_mb > heavy_threshold

        result = {
            "md5": md5,
            "filename": filename,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "is_heavy": is_heavy,
            "accept_ranges": accept_ranges,
            "estimated_minutes": est_minutes,
            "direct_url": cdn_url
        }

        if as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return result

        print("=" * 65)
        print("  【安娜书渡】前置决策与体积账单")
        print("=" * 65)
        print(f"  书名文件: {filename}")
        print(f"  精确体积: {size_mb} MB ({size_bytes:,} 字节)")
        print(f"  分块支持: {accept_ranges}")
        print(f"  通道限速: 约 40 ~ 70 KB/s (慢速通道 QoS)")
        print(f"  预计耗时: 约 {est_minutes} 分钟")
        if is_heavy:
            print(f"  [!] 提示: 该文件体积超过阈值 ({heavy_threshold} MB)，属于大文献，建议后台静默挂机。")
        else:
            print(f"  [+] 提示: 小型文献 (<= {heavy_threshold} MB)，可立即完成下载。")
        print("=" * 65)
        return result
    except Exception as e:
        print(f"[-] 头部探测异常: {e}", flush=True)
        return None

def download_book(md5=None, direct_url=None, output_dir=None, custom_filename=None, quiet=False):
    """Downloads book using native curl or requests, with strict protocol validation and DjVu transcoding."""
    if not md5 and not direct_url:
        print("[-] 错误: 必须提供 MD5 或直链")
        return False

    raw_dir = output_dir or CONFIG.get("default_download_dir") or (Path.home() / "Downloads" / "AnnasFerry")
    target_output_dir = Path(os.path.expandvars(os.path.expanduser(str(raw_dir))))
    target_output_dir.mkdir(parents=True, exist_ok=True)
    proxy_server = detect_proxy()

    cdn_url = direct_url or resolve_direct_url(md5)
    if not cdn_url:
        print("[-] 获取下载直链失败。")
        return False

    url_path = urllib.parse.unquote(urllib.parse.urlparse(cdn_url).path)
    orig_ext = Path(url_path).suffix.lower()
    if not orig_ext or len(orig_ext) > 5:
        orig_ext = ".pdf"

    # Clean filename without double extensions
    if custom_filename:
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', custom_filename)
        if clean_name.lower().endswith(orig_ext):
            target_file = target_output_dir / clean_name
        else:
            target_file = target_output_dir / f"{clean_name}{orig_ext}"
    else:
        base_name = Path(url_path).stem or f"book_{md5}"
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', base_name)
        target_file = target_output_dir / f"{clean_name}{orig_ext}"

    # Check existing valid file
    if target_file.exists() and target_file.stat().st_size > 1024 * 50:
        try:
            if target_file.suffix.lower() == ".pdf":
                import fitz
                doc = fitz.open(str(target_file))
                if len(doc) > 0:
                    print(f"[+] 本地已存在完整有效文件: {target_file.name} ({len(doc)} 页)", flush=True)
                    doc.close()
                    return str(target_file)
                doc.close()
            else:
                print(f"[+] 本地已存在完整有效文件: {target_file.name}", flush=True)
                return str(target_file)
        except Exception:
            pass

    import requests
    proxies = {"http": proxy_server, "https": proxy_server} if proxy_server else None
    range_supported = False
    try:
        r_test = requests.get(
            cdn_url,
            headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-10"},
            proxies=proxies,
            timeout=5.0,
            verify=False,
            stream=True
        )
        range_supported = (r_test.status_code == 206)
    except Exception:
        pass

    curl_bin = shutil.which("curl.exe") or shutil.which("curl")
    if curl_bin:
        cmd = [
            curl_bin,
            "-g",
            "-k",
            "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "--retry", "5",
            "--retry-delay", "3",
            "-o", str(target_file),
            cdn_url
        ]
        if proxy_server:
            cmd.extend(["-x", proxy_server])
        if quiet:
            cmd.append("-s")
        if range_supported:
            cmd.extend(["-C", "-"])

        if not quiet:
            print(f"[*] 启动单流下载引擎 -> {target_file.name}...", flush=True)

        t0 = time.time()
        res = subprocess.run(cmd)
        elapsed = round(time.time() - t0, 1)

        if res.returncode != 0:
            print(f"[-] 下载异常中断，curl 退出码: {res.returncode}", flush=True)
            return False

        if not quiet:
            print(f"[+] 下载完成！耗时: {elapsed} 秒", flush=True)
    else:
        print("[*] 系统 curl 未就绪，切入内置流式引擎...", flush=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(cdn_url, headers=headers, stream=True, proxies=proxies, timeout=(15, 30), verify=False) as r:
            with open(target_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=512 * 1024):
                    if chunk:
                        f.write(chunk)

    if not target_file.exists():
        return False

    # True DjVu to PDF Transcoding implementation
    if target_file.suffix.lower() == ".djvu" and CONFIG.get("auto_convert_djvu", True):
        djvu_tool = find_djvu_tool()
        if djvu_tool:
            pdf_target = target_file.with_suffix(".pdf")
            print(f"[*] 正在调用 ddjvu 进行高质量转码 -> {pdf_target.name} ...", flush=True)
            conv_res = subprocess.run([djvu_tool, "-format=pdf", str(target_file), str(pdf_target)])
            if conv_res.returncode == 0 and pdf_target.exists():
                print(f"[+] DjVu 转码 PDF 成功！已生成: {pdf_target.name}", flush=True)
                target_file = pdf_target
        else:
            print(f"[!] 提示: 未检测到 ddjvu 工具，保留原始 .djvu 格式交付。", flush=True)

    size_mb = round(target_file.stat().st_size / (1024 * 1024), 2)
    if target_file.suffix.lower() == ".pdf":
        try:
            import fitz
            doc = fitz.open(str(target_file))
            pages = len(doc)
            doc.close()
            print(f"🎉 校验成功: 《{target_file.name}》完整落盘 (体积: {size_mb} MB，共 {pages} 页)！", flush=True)
            return str(target_file)
        except Exception as e:
            print(f"[-] PDF 开卷核验提示: {e}", flush=True)
            return str(target_file)
    else:
        print(f"🎉 校验成功: 《{target_file.name}》完整落盘 (体积: {size_mb} MB)！", flush=True)
        return str(target_file)

def main():
    parser = argparse.ArgumentParser(description="安娜书渡 / Anna's Archive Ferry 核心引擎")
    subparsers = parser.add_subparsers(dest="command")

    doc_parser = subparsers.add_parser("doctor", help="环境体检与主站网络诊断")
    doc_parser.add_argument("--fix", action="store_true", help="自动安装缺失依赖")

    s_parser = subparsers.add_parser("search", help="检索书籍资源")
    s_parser.add_argument("query", help="书名、作者或关键词")
    s_parser.add_argument("--ext", help="指定格式，如 pdf, djvu, epub")
    s_parser.add_argument("--limit", type=int, default=10, help="返回条数限制")
    s_parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    p_parser = subparsers.add_parser("probe", help="前置嗅探书籍体积与挂机耗时")
    p_parser.add_argument("--md5", required=True, help="书籍 MD5 码")
    p_parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    d_parser = subparsers.add_parser("download", help="下载指定书籍（纯净单流下载与校验）")
    d_parser.add_argument("--md5", help="书籍 MD5 码")
    d_parser.add_argument("--direct-url", help="直接传入已知直链")
    d_parser.add_argument("--output", help="自定义保存目录")
    d_parser.add_argument("--name", help="自定义保存文件名")
    d_parser.add_argument("--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    if args.command == "doctor":
        run_doctor(fix=args.fix)
    elif args.command == "search":
        search_books(args.query, ext=args.ext, limit=args.limit, as_json=args.json)
    elif args.command == "probe":
        probe_book(args.md5, as_json=args.json)
    elif args.command == "download":
        download_book(
            md5=args.md5,
            direct_url=args.direct_url,
            output_dir=args.output,
            custom_filename=args.name,
            quiet=args.quiet
        )
    else:
        run_doctor()

if __name__ == "__main__":
    main()
