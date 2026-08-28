"""Custom MCP Server cho nghiệp vụ Tra cứu đơn hàng.

Tính năng:
- Lấy thông tin đơn hàng (get_order v1, get_order_v2)
- Tìm kiếm đơn hàng theo trạng thái (search_orders)
- Authentication bằng Bearer Token
- Versioning qua server://info
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

SERVER_VERSION = "2.0.0"

# Dữ liệu JSON
DATA_PATH = Path(__file__).parent / "data" / "orders.json"

def load_orders() -> list[dict]:
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

# --- Authentication Setup ---
VALID_TOKENS: dict[str, str] = {
    os.environ.get("MCP_AUTH_TOKEN", "my-secret-token"): "order-client",
}

class StaticTokenVerifier(TokenVerifier):
    """Kiểm tra bearer token tĩnh."""
    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = VALID_TOKENS.get(token)
        if client_id is None:
            return None
        return AccessToken(token=token, client_id=client_id, scopes=["order:read"])

# --- Init MCP Server ---
mcp = MCPServer(
    "order-mcp",
    auth=AuthSettings(
        issuer_url="http://localhost:8000",
        resource_server_url="http://localhost:8000",
    ),
    token_verifier=StaticTokenVerifier(),
    instructions=f"Order Tracking MCP Server v{SERVER_VERSION}.",
)

# --- Tools ---

@mcp.tool()
def get_order(order_id: str) -> str:
    """[v1] Lấy thông tin cơ bản của đơn hàng. Khuyên dùng get_order_v2."""
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            return json.dumps({
                "status": o["status"],
                "message": "success"
            }, ensure_ascii=False)
    
    return json.dumps({"status": "not_found", "message": "Order not found"})

@mcp.tool()
def get_order_v2(order_id: str, include_items: bool = False) -> str:
    """[v2] Lấy thông tin chi tiết của đơn hàng.
    
    Args:
        order_id: Mã đơn hàng (VD: ORD001)
        include_items: Có trả về danh sách sản phẩm không (mặc định: False)
    """
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            result = {
                "id": o["id"],
                "status": o["status"],
                "customer": o["customer"],
                "updated_at": o["updated_at"],
                "api_version": "2.0"
            }
            if include_items:
                result["items"] = o.get("items", [])
                result["total"] = o.get("total", 0)
            return json.dumps(result, ensure_ascii=False)
            
    return json.dumps({"error": "Order not found", "api_version": "2.0"})

@mcp.tool()
def search_orders(status: str) -> str:
    """Tìm kiếm danh sách các đơn hàng theo trạng thái.
    
    Args:
        status: Trạng thái đơn hàng (VD: done, processing, cancelled)
    """
    orders = load_orders()
    results = [o for o in orders if o["status"].lower() == status.lower()]
    return json.dumps(results, ensure_ascii=False)

# --- Resources ---
@mcp.resource("server://info")
def server_info() -> str:
    """Metadata của server (versioning, tools)."""
    return json.dumps(
        {
            "name": "order-mcp",
            "version": SERVER_VERSION,
            "tools": {
                "get_order": {
                    "version": "1.0.0",
                    "deprecated": True
                },
                "get_order_v2": {
                    "version": "2.0.0",
                    "deprecated": False
                },
                "search_orders": {
                    "version": "1.0.0",
                    "deprecated": False
                }
            }
        },
        ensure_ascii=False,
    )

if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 8000))
    # Sử dụng streamable-http port 8000
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
