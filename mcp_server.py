import json
import os
import sys
from typing import Any, Dict, Optional

from code_quality_mcp import analyze_path


class CodeQualityMCPServer:
    def __init__(self) -> None:
        self.initialized = False

    def _send_message(self, message: Dict[str, Any]) -> None:
        payload = json.dumps(message, ensure_ascii=False)
        header = f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n"
        sys.stdout.write(header + payload)
        sys.stdout.flush()

    def _read_message(self) -> Optional[Dict[str, Any]]:
        headers = {}
        while True:
            line = sys.stdin.buffer.readline().decode("utf-8")
            if line in {"\n", "\r\n", ""}:
                break
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()

        length = headers.get("content-length")
        if length is None:
            return None

        body = sys.stdin.buffer.read(int(length)).decode("utf-8")
        if not body:
            return None
        return json.loads(body)

    def _handle_request(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "paper-code-quality-mcp", "version": "0.1.0"},
                },
            }

        if method == "notifications/initialized":
            self.initialized = True
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "analyze_code_quality",
                            "description": "Analyze code comment rate, redundancy, and basic structural characteristics.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "The file or directory to analyze"}
                                },
                                "required": ["path"],
                            },
                        }
                    ]
                },
            }

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name != "analyze_code_quality":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }

            target_path = arguments.get("path")
            if not target_path:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Missing required argument: path"},
                }

            result = analyze_path(target_path)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ]
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not supported: {method}"},
        }

    def run(self) -> None:
        while True:
            message = self._read_message()
            if message is None:
                continue
            response = self._handle_request(message)
            if response is not None:
                self._send_message(response)


if __name__ == "__main__":
    CodeQualityMCPServer().run()
