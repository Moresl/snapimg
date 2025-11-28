"""
启动图片压缩服务
运行: python main.py
"""
import socket
import uvicorn

def get_local_ips():
    """获取本机所有 IP 地址"""
    ips = []
    try:
        # 获取主机名对应的 IP
        hostname = socket.gethostname()
        ips.append(socket.gethostbyname(hostname))
    except:
        pass

    try:
        # 获取所有网络接口的 IP
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except:
        pass

    # 尝试通过连接外部获取本机 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ip not in ips:
            ips.append(ip)
        s.close()
    except:
        pass

    return ips

def print_startup_info(port: int):
    """打印启动信息"""
    print("\n  \033[32m图片压缩服务已启动\033[0m\n")
    print(f"  ➜  Local:   \033[36mhttp://localhost:{port}/\033[0m")
    print(f"  ➜  API文档: \033[36mhttp://localhost:{port}/api/docs\033[0m")

    for ip in get_local_ips():
        print(f"  ➜  Network: \033[36mhttp://{ip}:{port}/\033[0m")

    print()

if __name__ == "__main__":
    PORT = 8001
    print_startup_info(PORT)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        reload_dirs=["app"],  # 只监听 app 目录
        log_level="warning"   # 减少日志输出
    )
