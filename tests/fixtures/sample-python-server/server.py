#!/usr/bin/env python3
"""Minimal stub MCP server for testing — stdlib only."""
import sys
import json


def main():
    """Run a minimal MCP server responding to initialize and tools/list."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            msg_id = msg.get("id")
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0", "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "sample-python-server", "version": "1.0.0"},
                    },
                }
            elif method == "tools/list":
                response = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": []}}
            else:
                response = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(response), flush=True)
        except Exception:
            continue


if __name__ == "__main__":
    main()
