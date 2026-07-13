# PaperMCP

这是一个面向代码规范性检查的 MCP 示例，提供一个简单的工具用于分析代码注释率、冗余程度以及基础代码统计信息。

## 功能特点

- 分析单个文件或整个目录
- 统计注释率（按行数估算）
- 统计冗余程度（重复 token 比例）
- 输出每个文件的结果与整体汇总

## 项目结构

- code_quality_mcp.py：核心分析逻辑
- mcp_server.py：一个简化版的 MCP stdio 服务
- tests/test_code_quality_analysis.py：基础回归测试

## 快速开始

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 运行测试
   ```bash
   python -m unittest discover -s tests -v
   ```

3. 启动 MCP 服务
   ```bash
   python mcp_server.py
   ```

## 工具说明

### analyze_code_quality

输入参数：
- path：要分析的文件或目录路径

返回结果示例：
```json
{
  "file_count": 1,
  "files": [
    {
      "path": "sample.py",
      "comment_rate": 0.2,
      "redundancy_ratio": 0.1,
      "lines": 10
    }
  ],
  "overall": {
    "comment_rate": 0.2,
    "redundancy_ratio": 0.1,
    "files_analyzed": 1
  }
}
```

## 说明

这个示例偏向“可运行的最小原型”，适合你继续扩展为更完整的代码规范 MCP，例如增加：
- 复杂度分析
- 命名规范检查
- 长函数/长类检测
- 风格规则（PEP8 / ESLint / Prettier 风格）
- 结果输出为 JSON 或 Markdown 报告
