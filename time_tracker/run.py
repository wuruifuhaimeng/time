import os
import sys
import logging
from pathlib import Path

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
        # 切换到脚本所在目录
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        logger.info(f"工作目录: {script_dir}")
        
        # 添加项目根目录到 Python 路径
        project_root = script_dir.parent
        sys.path.insert(0, str(project_root))
        
        # 导入并运行主程序
        from time_tracker.main import main as run_app
        run_app()
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        print(f"\n程序运行出错: {e}")
        print("\n请检查以下可能的问题：")
        print("1. Python 版本是否为 3.8 或更高")
        print("2. 是否已安装所有依赖（pip install -r requirements.txt）")
        print("3. 是否有足够的权限访问数据目录")
        print("4. 项目结构是否正确")
        print("\n详细错误信息：")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 