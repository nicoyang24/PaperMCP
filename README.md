# Paper Report MCP

解析本地 PDF 学术论文，生成一份让没有读过原文的人也能看懂的中文 Markdown 汇总报告。

## 报告内容

深度报告默认包含：

- 一句话总结
- 论文要解决的问题及其重要性
- 作者提出的方法及分步骤解释
- 实验数据、对比方法、评价指标和关键数值
- 主要结果以及结果意味着什么
- 创新点、局限和实际价值
- 专业术语的通俗中文解释

英文论文会被翻译、改写为自然中文。生成过程采用“分章节阅读，再综合成文”的方式，避免只总结论文开头。

## 安装

需要 Python 3.10+，推荐使用 `uv`：

```powershell
uv sync
```

## 启动与 MCP 配置

启动命令：

```powershell
uv run paper-report-mcp
```

stdio MCP 客户端配置示例：

```json
{
  "mcpServers": {
    "paper-report": {
      "command": "uv",
      "args": ["--directory", "D:\\nicoyang\\PracticePlace\\PaperMCP", "run", "paper-report-mcp"]
    }
  }
}
```

## 模型配置

中文翻译和深度解读需要语言模型。复制示例配置文件：

```powershell
Copy-Item paper_mcp.config.example.json paper_mcp.config.json
```

打开项目根目录的 `paper_mcp.config.json`，填入配置：

```json
{
  "llm": {
    "api_key": "你的 API Key",
    "model": "gpt-4.1-mini",
    "base_url": "https://api.openai.com/v1"
  }
}
```

- `api_key`：模型服务的 API Key。
- `model`：模型服务支持的模型名称。
- `base_url`：OpenAI 兼容接口的 `/v1` 地址。

真实配置文件已经加入 `.gitignore`，不会被 Git 提交。服务没有读取到 API Key 时，会尝试请求当前 MCP 客户端提供 Sampling 能力。

默认从当前工作目录读取 `paper_mcp.config.json`。如果配置文件放在其他位置，可通过 `PAPER_MCP_CONFIG` 指定路径：

```powershell
$env:PAPER_MCP_CONFIG="D:\config\paper-mcp.json"
```

## MCP 工具

### `inspect_paper`

读取 PDF 元数据、总页数、章节和文本统计。

### `generate_paper_report`

调用示例：

```json
{
  "pdf_path": "D:\\papers\\example.pdf",
  "output_path": "D:\\papers\\example-report.md",
  "use_llm": true,
  "max_pages": 100
}
```

- `pdf_path`：论文 PDF 的路径。
- `output_path`：可选，Markdown 报告保存路径。
- `use_llm`：默认 `true`，生成易懂的中文深度报告。设为 `false` 时只生成离线抽取版，不保证翻译。
- `max_pages`：最多解析页数，范围为 1～1000。

## 演示案例

[`examples/demo.py`](examples/demo.py) 会自动启动 MCP Server，然后调用论文检查和报告生成工具。

创建 `paper_mcp.config.json` 后直接运行：

```powershell
uv run python examples/demo.py ".\论文.pdf"
```

独立演示客户端本身不提供 MCP Sampling。如果 JSON 中没有配置 `llm.api_key`，脚本会显示提示并自动降级为离线抽取模式。

默认在 PDF 同目录生成 `论文-report.md`。指定输出路径：

```powershell
uv run python examples/demo.py ".\论文.pdf" --output ".\reports\论文汇总.md" --max-pages 50
```

没有可用模型时，可以显式运行离线演示：

```powershell
uv run python examples/demo.py ".\论文.pdf" --offline
```

离线模式只抽取原文关键句，无法可靠地把英文翻译成中文，主要用于检查 PDF 解析功能。

## 限制

- PDF 必须包含可提取的文本层，纯扫描 PDF 需要先进行 OCR。
- 公式、图片和复杂多栏排版可能无法完整还原。
- 自动报告可能有遗漏，重要数字和结论应回查原文。

## 测试

```powershell
uv run pytest
```
