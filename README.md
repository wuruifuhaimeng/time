# Time Tracker 时间记录器

一个简洁高效的时间记录与任务管理工具，支持时间块、日记、任务、心情等多维度记录，支持自然语言解析与可视化统计。

## 目录结构

```
time_tracker/           # 主程序包
    main.py            # 程序主入口
    run.py             # 启动脚本
    core/              # 数据模型与分析
    ui/                # 界面与控件
        widgets/
    ...
data/                   # 用户数据（自动生成）
requirements.txt        # 依赖库
README.md               # 项目说明
setup.py                # 安装脚本
.gitignore              # 忽略配置
```

## 主要功能
- 时间块记录与自然语言解析
- 日记与心情管理
- 任务清单与完成状态
- 自动保存与数据导出
- 可视化统计与鼓励机制

## 使用方法
1. 安装依赖：`pip install -r requirements.txt`
2. 启动程序：`python -m time_tracker.run`
3. 或打包为exe后直接双击运行

## 打包为exe
```
pip install pyinstaller
pyinstaller --onefile --noconsole time_tracker/run.py -n TimeTracker
```

## 许可证
MIT License
