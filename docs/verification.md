# 真实站点验证记录 / Live verification record

**日期：2026-09-23。** 这是一项当时的端到端验证，不保证站点未来持续可用。测试对象是检索结果中标注为 Project Gutenberg 的 *Pride and Prejudice* EPUB。

| 阶段 | 结果 |
| --- | --- |
| 环境诊断 | Python、浏览器、依赖、镜像连接正常 |
| 检索 | 返回多个 EPUB 版本，供人工选择 |
| 探测 | 服务器报告 24,837,384 字节并支持字节范围 |
| 下载 | 同步下载完成；显示基于实际传输的动态剩余时间 |
| 完整性 | MD5 为 `fb73d4fd19b0da98923365cb85a03a2b`，与书目一致 |
| 格式 | EPUB ZIP 可完整读取，182 个条目，MIME 文件为 `application/epub+zip` |
| 清理 | 成功后没有残留 `.part` 或 `.part.meta` |
| 机器输出 | `probe --json` 的标准输出可直接解析；日志在标准错误输出 |

测试中的一次下载耗时约 25 秒。实际速度取决于镜像、通道、代理和网络；此数值不能用于预测其他下载。完整的临时直链未记录在本文中。

本地自动测试使用模拟 HTTP 响应覆盖有效下载、截断、MD5 不符、断点续传、资源身份变化及 JSON 输出。运行：

DjVu 转 PDF 另以本机 DjVuLibre 工具和合成的 1 页 DjVu 做了实际转换检查：生成的 PDF 可打开且包含 1 页，原始 DjVu 保留。此项不代表所有 DjVu 文件或文字层都能无损转换。

```bash
python -m unittest discover -s tests -v
```
