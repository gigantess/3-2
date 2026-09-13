"""
Model Context Protocol (MCP) Server for Samsung Stock Analysis (Bonus Mission 1-B)
Allows external MCP clients (e.g. Claude Desktop, cursor, custom agents) to access
Samsung stock time-series data, summaries, and statistics.
"""

import sys
import json
from typing import Dict, Any
from backend.services.data_service import DataService

def handle_tools_list() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": "get_data_summary",
                "description": "삼성전자 주가 시계열 데이터의 전체 요약 통계(기간, 건수, 평균/최고/최저/최신가, 최근 추세)를 반환합니다.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_data_statistics",
                "description": "삼성전자 주가의 심층 금융 통계(변동성, 20일 및 60일 이동평균, 14일 RSI, 최고/최저가 및 전체 기간 수익률)를 반환합니다.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_recent_data_items",
                "description": "최근 N개의 일별 주가 기록(날짜, 종가, 메모)을 반환합니다.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "조회할 최근 거래일 수 (기본 5개)",
                            "default": 5
                        }
                    }
                }
            }
        ]
    }

def handle_tools_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    ds = DataService()
    if name == "get_data_summary":
        summary = ds.get_summary()
        return {"content": [{"type": "text", "text": json.dumps(summary.model_dump(), ensure_ascii=False, indent=2)}]}
    elif name == "get_data_statistics":
        stats = ds.get_statistics()
        return {"content": [{"type": "text", "text": json.dumps(stats, ensure_ascii=False, indent=2)}]}
    elif name == "get_recent_data_items":
        limit = arguments.get("limit", 5)
        items, _ = ds.get_items(limit=limit, sort_by="date", sort_order="desc")
        result = [item.model_dump() for item in items]
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}
    else:
        raise ValueError(f"Unknown tool: {name}")

def run_stdio_mcp_server():
    """
    Standard JSON-RPC 2.0 stdio loop for MCP clients.
    """
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "tools/list":
                res = {"jsonrpc": "2.0", "id": req_id, "result": handle_tools_list()}
            elif method == "tools/call":
                params = req.get("params", {})
                tool_res = handle_tools_call(params.get("name"), params.get("arguments", {}))
                res = {"jsonrpc": "2.0", "id": req_id, "result": tool_res}
            else:
                res = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_res, ensure_ascii=False) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_mcp_server()
