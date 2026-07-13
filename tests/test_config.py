import json

from paper_mcp.config import load_llm_config


def test_load_json_config(tmp_path, monkeypatch) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "llm": {
                    "api_key": "test-key",
                    "model": "test-model",
                    "base_url": "https://example.test/v1/",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PAPER_MCP_CONFIG", str(path))
    config = load_llm_config()
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.base_url == "https://example.test/v1"


def test_missing_config_uses_defaults(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PAPER_MCP_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.delenv("PAPER_LLM_API_KEY", raising=False)
    config = load_llm_config()
    assert config.api_key == ""
    assert config.model == "gpt-4.1-mini"
