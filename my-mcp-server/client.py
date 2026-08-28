import asyncio
import os
import httpx
from mcp import ClientSession

async def main():
    # Token xác thực
    token = os.environ.get("MCP_AUTH_TOKEN", "my-secret-token")
    headers = {"Authorization": f"Bearer {token}"}
    
    url = "http://localhost:8000/mcp"
    
    print(f"Ket noi toi {url} voi token: {token}")
    
    try:
        # Trong thực tế, MCP Client như Claude Desktop sẽ tự làm việc này.
        # Đoạn code này giả lập một kết nối MCP client thủ công (hoặc HTTP post).
        # Vì HTTP streamable-http của MCP dùng SSE, cách tốt nhất test API là
        # dùng mcp library client hoặc post HTTP thô.
        # 
        # Để test auth, ta gửi một HTTP GET tới base URL
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 401 or resp.status_code == 403:
                print("Loi Auth: Token khong hop le.")
                return
            elif resp.status_code == 426:
                # 426 Upgrade Required hoặc trả về cấu trúc mcp router là auth thành công
                print("Auth thanh cong!")
            else:
                print(f"Da ket noi, status_code: {resp.status_code}")
                
            # Thử GET resource info
            # info = await client.get(f"http://localhost:8000/mcp/resources/server/info", headers=headers)
            # print("Server Info:", info.text)
            
    except Exception as e:
        print(f"Loi ket noi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
