# utils.py
import sys
import os


def get_base_path():
    """获取基础路径，兼容开发环境和打包环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller创建的单文件环境
            return sys._MEIPASS
        else:
            # 其他打包工具或没有_MEIPASS
            return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """获取资源文件的完整路径"""
    base_path = get_base_path()

    # 处理路径分隔符
    if os.path.sep == '\\':  # Windows
        relative_path = relative_path.replace('/', '\\')
    else:  # Linux/Mac
        relative_path = relative_path.replace('\\', '/')

    full_path = os.path.join(base_path, relative_path)

    # 调试信息
    # print(f"资源路径: {full_path}")

    return full_path


def file_exists(file_path):
    """检查文件是否存在（使用资源路径）"""
    abs_path = resource_path(file_path)
    return os.path.exists(abs_path)