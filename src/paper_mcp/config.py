from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMConfig:
    api_key: str = ""
    model: str = "gpt-4.1-mini"
    base_url: str = "https://api.openai.com/v1"


def config_path() -> Path:
    """返回配置路径；可用 PAPER_MCP_CONFIG 指向其他 JSON 文件。"""
    custom = os.environ.get("PAPER_MCP_CONFIG")
    return Path(custom).expanduser().resolve() if custom else Path.cwd() / "paper_mcp.config.json"


def load_llm_config() -> LLMConfig:
    path = config_path()
    data: dict = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法读取配置文件 {path}: {exc}") from exc
        if not isinstance(loaded, dict) or not isinstance(loaded.get("llm", {}), dict):
            raise ValueError(f"配置文件 {path} 中的 llm 必须是 JSON 对象")
        data = loaded.get("llm", {})

    # 环境变量仅作为兼容兜底，JSON 中的值优先。
    return LLMConfig(
        api_key=str(data.get("api_key") or os.environ.get("PAPER_LLM_API_KEY", "")).strip(),
        model=str(data.get("model") or os.environ.get("PAPER_LLM_MODEL", "gpt-4.1-mini")).strip(),
        base_url=str(
            data.get("base_url")
            or os.environ.get("PAPER_LLM_BASE_URL", "https://api.openai.com/v1")
        ).strip().rstrip("/"),
    )
