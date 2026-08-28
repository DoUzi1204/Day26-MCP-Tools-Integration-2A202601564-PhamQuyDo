# Order Tracking MCP Server

MCP Server phục vụ cho Use Case: **Tra cứu đơn hàng thủ công** (Order Tracking).
- **Công việc hiện tại**: Mở file JSON / truy xuất cơ sở dữ liệu nội bộ để tìm mã đơn hàng, xem trạng thái, xem sản phẩm khách mua.
- **Giải pháp**: Xây dựng MCP Server với 2 tools chính (`get_order` và `search_orders`) để trợ lý AI (như Claude Code / Gemini) tự tra cứu theo yêu cầu bằng ngôn ngữ tự nhiên.

## MCP Tools

1. `get_order(order_id: str)`: Lấy thông tin cơ bản của đơn (v1 - deprecated).
2. `get_order_v2(order_id: str, include_items: bool)`: Lấy thông tin chi tiết đơn (v2). Trả về JSON chứa mã, khách hàng, sản phẩm, tổng tiền.
3. `search_orders(status: str)`: Tìm các đơn hàng theo trạng thái cụ thể (ví dụ: `done`, `processing`).

## Hướng dẫn cài đặt & Chạy

1. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy server:
   ```bash
   # Mặc định server sẽ chạy tại http://0.0.0.0:8000/mcp (streamable-http)
   # Sử dụng token auth: my-secret-token
   python server.py
   ```

## Kiểm thử Authentication

Chạy script `client.py` để test kết nối streamable-http với Bearer Token:
```bash
python client.py
```
Nếu gửi token đúng (`my-secret-token`), server cho phép qua. Nếu sai, trả về HTTP 401.

## Đăng ký với Claude Code (Client)

Để Claude Code gọi được server này, bạn cần sửa cấu hình MCP client (ví dụ `mcp.json` hoặc chạy qua CLI nếu có hỗ trợ `streamable-http` proxy). Với giao thức stdio mặc định của Claude Code, bạn có thể bọc server này lại qua một script SSE-to-stdio hoặc sử dụng client hỗ trợ HTTP.
Ví dụ nếu chạy stdio, có thể bỏ argument `transport="streamable-http"` trong `server.py` để Claude Code dễ dàng bind:
```json
{
  "mcpServers": {
    "order-mcp": {
      "command": "python",
      "args": ["/path/to/my-mcp-server/server.py"]
    }
  }
}
```

## Tính năng mở rộng đã áp dụng:
- **Authentication**: Xác thực mọi request bằng Token.
- **Versioning**: Dùng `server://info` để thông báo deprecated `get_order` và khuyến nghị dùng `get_order_v2`.
