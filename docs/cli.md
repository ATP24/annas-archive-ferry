# CLI 与配置 / CLI and configuration

> 在已激活的 Python 3.9+ 虚拟环境中运行。`annas-ferry` 来自 `python -m pip install -e .`；仓库内也可用 `python scripts/ferry_engine.py`。

## 命令 / Commands

| 命令 | 作用 | 常用参数 |
| --- | --- | --- |
| `annas-ferry doctor` | 检查依赖、浏览器、代理和镜像连接 | `--fix` 安装缺失 Python 包 |
| `annas-ferry search "关键词"` | 检索并列出版本 | `--ext pdf`、`--limit 5`、`--json` |
| `annas-ferry probe --md5 <MD5>` | 解析直链、读取文件大小与范围支持情况 | `--json` |
| `annas-ferry download --md5 <MD5>` | 下载并校验书目记录 | `--output`、`--name`、`--quiet` |
| `annas-ferry download --direct-url <URL>` | 从已知公网 HTTPS 地址下载 | `--output`、`--name` |

`--json` 适用于 `search` 和 `probe`。标准输出是单个 JSON 值，诊断信息在标准错误输出。失败时返回非零退出码。`download` 当前没有 JSON 模式。

`probe` 不做抽样测速，`estimated_minutes` 为 `null`。下载开始后，非 quiet 模式每隔数秒显示实测速度与剩余时间；剩余时间仅是根据近期传输速度计算的临时估计。

## 本地文件 / Local files

- 默认保存目录：`~/Downloads/AnnasFerry`。可用 `--output` 覆盖。
- 未完成传输保存在 `<文件名>.part`；`<文件名>.part.meta` 保存续传身份信息。不要把 `.part` 当作成品。
- 成功后，工具验证传输长度与书目 MD5；PDF 还会检查是否能打开。通过后才改名为最终文件。
- DjVu 转 PDF 需要系统安装 `ddjvu`。转换失败时保留原 DjVu。

## 配置 / Configuration

用户配置文件位于 `~/.annas_ferry/config.json`，缓存位于 `~/.annas_ferry_cache/`。不需要手动创建；默认值由 `annas_archive_ferry/config.py` 定义。常用键如下：

```json
{
  "primary_mirror": "https://<trusted-mirror>",
  "proxy": "auto",
  "default_download_dir": "~/Downloads/AnnasFerry",
  "auto_convert_djvu": true,
  "headless": true
}
```

`proxy: "auto"` 优先使用环境变量中的代理，再尝试常见本机端口。镜像、代理和本地目录由使用者控制；只配置可信地址。缓存直链可能含有临时访问参数，请勿公开缓存文件或完整直链。

## 安全边界 / Security notes

`--direct-url` 必须是解析到公网地址的 HTTPS URL，重定向也会逐跳检查。没有 MD5 时需要服务器给出长度；长度验证不能替代内容哈希。站点返回的书目信息和文件名不是可信指令。
