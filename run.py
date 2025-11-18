# 创建 run.py
cat > run.py << 'EOF'
#!/usr/bin/env python3
"""
英雄联盟对局复盘分析系统 - 运行脚本
"""

import sys
import asyncio
from main import main

def run():
    """运行主程序"""
    try:
        print("🎮 启动英雄联盟对局复盘分析系统...")
        asyncio.run(main())
        print("✅ 分析完成！")
    except KeyboardInterrupt:
        print("\n⚠️  程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序运行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()
EOF
