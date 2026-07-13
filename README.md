# Paper Report MCP

一个用于解析本地 PDF 学术论文并生成中文 Markdown 汇总报告的 MCP Server。

## 功能

- `inspect_paper`：读取 PDF 元数据、页数、章节和文本统计。
- `generate_paper_report`：生成结构化报告，可直接返回，也可保存为 Markdown。
- 默认离线抽取式总结，不需要 API Key。
- 设置 `use_llm=true` 后，通过 MCP Sampling 请求客户端所连接的模型生成深度报告。

> 当前版本针对含文本层的 PDF。纯扫描 PDF 需要先用 OCR 工具处理。

## 安装

需要 Python 3.10+。推荐使用 `uv`：

```powershell
uv sync
```

也可以使用 pip：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## 启动

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

## 调用示例

生成离线报告：

```json
{
  "pdf_path": "D:\\papers\\example.pdf",
  "output_path": "D:\\papers\\example-report.md",
  "use_llm": false,
  "max_pages": 100
}
```

若客户端支持 MCP Sampling，可将 `use_llm` 设为 `true`。这会把提取出的论文文本交给客户端模型总结，无需在服务端配置模型密钥。`max_pages` 控制最多解析页数；超长文本在 LLM 模式下最多提交前 80,000 个字符。

## 演示案例

仓库中的 [`examples/demo.py`](examples/demo.py) 是一个完整的 MCP 客户端案例。它会自动启动本项目的 MCP Server，依次调用 `inspect_paper` 和 `generate_paper_report`。

把论文 PDF 放到任意位置，例如项目根目录下的 `论文.pdf`，然后执行：

```powershell
uv run python examples/demo.py ".\论文.pdf"
```

默认会在 PDF 所在目录生成 `论文-report.md`。也可以指定输出文件和最大页数：

```powershell
uv run python examples/demo.py ".\论文.pdf" --output ".\reports\论文汇总.md" --max-pages 50
```

查看全部参数：

```powershell
uv run python examples/demo.py --help
```

该独立演示客户端使用离线总结模式。`--use-llm` 需要客户端实现 MCP Sampling，因此通常应在 Claude Desktop、VS Code 等支持 Sampling 的 MCP 客户端中使用，而不是在此脚本中启用。

## 测试

```powershell
uv run --with pytest pytest
```

本项目基于官方 MCP Python SDK v1.x；依赖限制为 `<2`，避免未来 v2 稳定版带来的不兼容变化。
