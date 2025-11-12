#!/usr/bin/env python3
"""
安装脚本 - 自动安装依赖和配置环境
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print("✓ Python版本检查通过")


def check_ffmpeg():
    """检查ffmpeg是否安装"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ ffmpeg已安装")
            return True
        else:
            print("⚠ ffmpeg未找到或不可用")
            return False
    except FileNotFoundError:
        print("⚠ ffmpeg未安装")
        return False


def install_dependencies():
    """安装Python依赖"""
    print("正在安装Python依赖...")
    
    try:
        # 使用pip安装requirements.txt中的包
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Python依赖安装完成")
        else:
            print(f"⚠ 依赖安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠ 安装过程中出错: {str(e)}")
        return False
    
    return True


def setup_environment():
    """设置环境配置"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        # 复制.env.example到.env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✓ 已创建.env配置文件")
        print("  请编辑.env文件设置你的OpenAI API密钥")
    elif env_file.exists():
        print("✓ .env配置文件已存在")
    else:
        print("⚠ 未找到.env.example文件")


def create_downloads_dir():
    """创建下载目录"""
    downloads_dir = Path('downloads')
    downloads_dir.mkdir(exist_ok=True)
    print("✓ 下载目录已创建")


def main():
    """主安装函数"""
    print("=" * 50)
    print("YouTube视频下载和字幕翻译工具 - 安装程序")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 检查ffmpeg
    ffmpeg_installed = check_ffmpeg()
    if not ffmpeg_installed:
        print("\n⚠ 警告: ffmpeg未安装")
        print("请手动安装ffmpeg:")
        print("- macOS: brew install ffmpeg")
        print("- Ubuntu/Debian: sudo apt install ffmpeg")
        print("- Windows: 下载并添加到PATH")
        print("\n程序将继续安装，但视频处理功能将不可用")
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 依赖安装失败")
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 创建下载目录
    create_downloads_dir()
    
    print("\n" + "=" * 50)
    print("安装完成!")
    print("=" * 50)
    print("\n下一步操作:")
    print("1. 编辑 .env 文件，设置你的OpenAI API密钥")
    print("2. 运行测试: python test.py")
    print("3. 查看使用说明: python main.py --help")
    print("\n示例用法:")
    print('python main.py "https://www.youtube.com/watch?v=视频ID"')


if __name__ == "__main__":
    main()