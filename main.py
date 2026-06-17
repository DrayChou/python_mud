import asyncio
import sys
import os

# Ensure python_mud/ is on the path regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.network import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] 服务器已关闭。")
