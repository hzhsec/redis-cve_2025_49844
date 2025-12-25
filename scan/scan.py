#!/usr/bin/env python3
# Redis 版本批量检测工具 v2
# 支持 http:// 和 https:// 前缀，兼容 password@host:port 格式
# 只检测是否为 Redis 8.2.1（saneki PoC 可利用版本）

import argparse
import threading
import queue
import sys
import re
from typing import Optional, Tuple
from redis import Redis
from redis.exceptions import AuthenticationError, ConnectionError, TimeoutError

# 目标版本（saneki PoC 支持的版本）
TARGET_VERSION = "8.2.1"

# 正则提取密码和主机端口（支持 user:pass@host:port）
AUTH_PATTERN = re.compile(r'^(?:(?:([^:]+):)?([^@]+)@)?(.+)$')

def parse_target(target_str: str) -> Optional[Tuple[str, int, Optional[str]]]:
    """
    解析目标字符串，支持多种格式
    返回: (host, port, password)
    """
    password = None

    # 去除 http:// 或 https:// 前缀
    target_str = re.sub(r'^https?://', '', target_str.strip())

    # 提取可能的认证部分：user:pass@host:port 或 pass@host:port
    match = AUTH_PATTERN.match(target_str)
    if match:
        user, pass_part, host_part = match.groups()
        if pass_part:
            password = pass_part
        target_str = host_part
    else:
        # 没有 @，直接就是 host:port
        target_str = target_str

    # 分离 host 和 port
    if ':' in target_str:
        host, port_str = target_str.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            print(f"[!] 端口格式错误: {target_str}")
            return None
    else:
        host = target_str
        port = 6379

    return host.strip(), port, password

def detect_version(host: str, port: int = 6379, password: Optional[str] = None, timeout: int = 5) -> None:
    try:
        r = Redis(host=host, port=port, password=password, socket_timeout=timeout, decode_responses=True)
        info = r.info()
        version = info.get('redis_version', '未知')
        build_id = info.get('redis_build_id', '未知')

        if version == TARGET_VERSION:
            print(f"\033[92m[+] {host}:{port} → Redis 版本: {version} (匹配目标，可被 saneki PoC 利用) \033[0m")
        else:
            print(f"[i] {host}:{port} → Redis 版本: {version} (Build ID: {build_id})")

    except AuthenticationError:
        print(f"\033[93m[-] {host}:{port} → 需要密码认证（AUTH required）\033[0m")
    except (ConnectionError, TimeoutError):
        print(f"\033[91m[-] {host}:{port} → 连接失败（超时或拒绝）\033[0m")
    except Exception as e:
        print(f"\033[91m[-] {host}:{port} → 异常: {str(e)}\033[0m")

def worker(task_queue: queue.Queue):
    while not task_queue.empty():
        item = task_queue.get()
        if item is None:
            break
        host, port, password = item
        detect_version(host, port, password)
        task_queue.task_done()

def main():
    parser = argparse.ArgumentParser(
        description="Redis 版本检测工具（支持 http/https 前缀，批量检测是否为 8.2.1）"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--target', type=str, help='单个目标，如: https://192.168.1.100:6379 或 pass@10.0.0.5')
    group.add_argument('-l', '--list', type=str, help='从文件读取目标列表，支持 http/https 和密码格式')
    parser.add_argument('--threads', type=int, default=50, help='并发线程数（默认50）')
    args = parser.parse_args()

    tasks = queue.Queue()

    if args.target:
        parsed = parse_target(args.target)
        if parsed:
            tasks.put(parsed)
        else:
            sys.exit(1)
    else:
        try:
            with open(args.list, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parsed = parse_target(line)
                    if parsed:
                        tasks.put(parsed)
                    else:
                        print(f"[!] 第{line_num}行 解析失败: {line}")
        except FileNotFoundError:
            print(f"[!] 文件未找到: {args.list}")
            sys.exit(1)

    if tasks.empty():
        print("[!] 没有有效的目标")
        sys.exit(1)

    print(f"[*] 开始检测 {tasks.qsize()} 个目标，使用 {min(args.threads, tasks.qsize())} 线程...\n")

    threads = []
    for _ in range(min(args.threads, tasks.qsize())):
        t = threading.Thread(target=worker, args=(tasks,))
        t.daemon = True
        t.start()
        threads.append(t)

    tasks.join()

    print("\n[*] 所有检测完成")

if __name__ == "__main__":
    main()