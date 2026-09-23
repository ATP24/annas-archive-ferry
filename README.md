# Anna's Archive Ferry · 安娜书渡

**一个可供 Agent 调用的本地图书检索与下载工具。** 检索 Anna's Archive 书目、比较版本、探测文件信息，并将用户选定的文件下载到本地。提供 `SKILL.md`、命令行和 Python 接口。

[English](README_EN.md) · [Skill 指令](SKILL.md) · [问题反馈](https://github.com/ATP24/annas-archive-ferry/issues)

> 项目处于持续改进中。镜像、页面结构、验证码和下载通道可能变化；检索或下载失败时会明确报错。请仅获取你有权访问的资料。

## 快速开始

需要 Python 3.9+。检索和解析直链需要 Playwright 可用的 Chromium、Chrome 或 Edge；DjVu 转 PDF 另需 `ddjvu`。

```bash
git clone https://github.com/ATP24/annas-archive-ferry.git
cd annas-archive-ferry
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
annas-ferry doctor
```

浏览器未安装时，运行 `python -m playwright install chromium`。

## 三步使用

```bash
annas-ferry search "书名或作者" --limit 5 --json
annas-ferry probe --md5 <32位MD5> --json
annas-ferry download --md5 <32位MD5> --output "./downloads"
```

先从检索结果选择正确版本，再探测大小，最后下载。`probe` 不额外请求文件片段测速，因此不会增加预先下载的流量或时间；下载开始后，CLI 会根据实际传输速度更新剩余时间。服务器不提供长度时，剩余时间无法计算。

下载先写入 `.part` 文件，并用 `.part.meta` 记录资源身份；服务端支持有效字节范围时可续传。完成后核对传输长度和书目 MD5；PDF 还会检查能否打开及页数。没有 MD5 的直链下载需要服务器提供可核对的长度。校验通过才会成为最终文件。CLI **同步运行**，没有自动后台唤醒机制。

可用 `--name` 指定文件名，`--output` 指定目录。`download --direct-url` 接受公网 HTTPS 地址；请只对可信来源使用。完整参数见 `annas-ferry --help` 和各子命令的 `--help`。

## 作为 Agent Skill 安装

将仓库放入 Agent 支持的 skills 目录，使 `SKILL.md` 位于该技能目录顶层；随后在对话中明确提出检索、比对或下载需求。不同 Agent 的发现规则与执行权限可能不同，请以各自文档为准。Skill 只指导 Agent 调用本地 CLI，不授予额外网络或文件权限。

## 工作范围与限制

- 检索结果来自站点页面解析，格式、体积和书目信息可能不完整；下载前请确认版本。
- 站点防护或镜像变更可能使自动解析失败；本工具不保证验证码一定通过。
- DjVu 转 PDF 依赖外部 `ddjvu`。未安装时保留原文件。
- `doctor --fix` 会安装缺失依赖，请在了解其行为后主动运行。
- 软件采用 [MIT 许可证](LICENSE)。使用者需自行确认资料的访问与使用权限。

## 开发与反馈

运行 `python -m unittest discover -s tests -v` 检查关键下载行为。欢迎通过 [Issue](https://github.com/ATP24/annas-archive-ferry/issues) 报告复现步骤，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
