# 英雄联盟对局复盘分析系统

这是一个自动化的英雄联盟对局复盘分析系统，能够自动获取对局数据、分析玩家表现、生成AI分析报告并发送到微信群。

## 功能特性

- 🎮 自动获取英雄联盟对局数据
- 📊 深度分析玩家表现和团队配合
- 🤖 AI智能评分和改进建议
- 💬 自动发送到微信群聊
- 🔄 支持定时任务和批量分析
- 📈 生成详细的数据报告

## 项目结构
├── src\                    # 源码目录
│   ├── __init__.py
│   ├── riot_api.py
│   ├── game_analyzer.py
│   ├── prompt_generator.py
│   ├── ai_analyzer.py
│   ├── wechat_sender.py
│   └── utils.py
├── tests\                   # 测试目录
│   ├── __init__.py
│   └── test_game_analyzer.py
├── logs\                    # 日志目录
│   └── .gitkeep
├── data\                    # 数据目录
│   └── .gitkeep
├── config.py               # 配置文件
├── main.py                 # 主程序
├── run.py                  # 运行脚本
├── requirements.txt        # 依赖文件
├── .env.example           # 环境变量示例
└── README.md              # 项目说明

# 测试方法
1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env` 并填写必要的环境变量
3. 运行测试：`python -m unittest discover tests`