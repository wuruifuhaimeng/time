import tkinter as tk
import logging
import sys
from pathlib import Path
from time_tracker.ui.main_window import TimeTracker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('time_tracker.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # 确保数据目录存在
        data_dir = Path.cwd() / "data"
        data_dir.mkdir(exist_ok=True)
        logger.info(f"数据目录: {data_dir}")

        # 创建主窗口
        root = tk.Tk()
        app = TimeTracker(root)
        
        # 设置窗口大小和位置
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 启动主循环
        logger.info("启动主程序")
        root.mainloop()
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 