import os
import subprocess
from pathlib import Path
from typing import Optional, List
from config import get_settings


class VideoProcessor:
    """视频处理器，用于合成字幕到视频"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ffmpeg_path = self.settings.ffmpeg_path or "ffmpeg"
    
    def embed_subtitle(self, video_file: str, subtitle_file: str, 
                      output_file: Optional[str] = None,
                      subtitle_language: str = "chi") -> str:
        """
        将字幕嵌入到视频中
        
        Args:
            video_file: 视频文件路径
            subtitle_file: 字幕文件路径
            output_file: 输出文件路径，如果为None则自动生成
            subtitle_language: 字幕语言代码
            
        Returns:
            输出文件路径
        """
        video_path = Path(video_file)
        subtitle_path = Path(subtitle_file)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
        
        # 生成输出文件路径
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}")
        
        # 构建ffmpeg命令
        cmd = [
            self.ffmpeg_path,
            '-i', video_file,
            '-i', subtitle_file,
            '-c', 'copy',  # 复制视频和音频流
            '-c:s', 'mov_text',  # 字幕编码器
            '-metadata:s:s:0', f'language={subtitle_language}',
            output_file,
            '-y'  # 覆盖输出文件
        ]
        
        try:
            # 执行ffmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg执行失败: {result.stderr}")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"ffmpeg处理失败: {str(e)}")
        except FileNotFoundError:
            raise Exception("未找到ffmpeg，请确保已安装ffmpeg并添加到PATH环境变量")
    
    def burn_subtitle(self, video_file: str, subtitle_file: str,
                     output_file: Optional[str] = None,
                     font_size: int = 24,
                     font_color: str = "white") -> str:
        """
        将字幕烧录到视频中（硬字幕）
        
        Args:
            video_file: 视频文件路径
            subtitle_file: 字幕文件路径
            output_file: 输出文件路径
            font_size: 字体大小
            font_color: 字体颜色
            
        Returns:
            输出文件路径
        """
        video_path = Path(video_file)
        subtitle_path = Path(subtitle_file)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
        
        # 生成输出文件路径
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_burned_subtitles{video_path.suffix}")
        
        # 构建ffmpeg命令（硬字幕）
        cmd = [
            self.ffmpeg_path,
            '-i', video_file,
            '-vf', f"subtitles={subtitle_file}:force_style='FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)}'",
            '-c:a', 'copy',
            output_file,
            '-y'
        ]
        
        try:
            # 执行ffmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg执行失败: {result.stderr}")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"ffmpeg处理失败: {str(e)}")
        except FileNotFoundError:
            raise Exception("未找到ffmpeg，请确保已安装ffmpeg并添加到PATH环境变量")
    
    def _color_to_hex(self, color_name: str) -> str:
        """颜色名称转十六进制"""
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': 'FF0000',
            'green': '00FF00',
            'blue': '0000FF',
            'yellow': 'FFFF00'
        }
        return color_map.get(color_name.lower(), 'FFFFFF')
    
    def get_video_info(self, video_file: str) -> dict:
        """获取视频信息"""
        cmd = [
            self.ffmpeg_path,
            '-i', video_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析输出信息
            info = {}
            lines = result.stderr.split('\n')
            
            for line in lines:
                if 'Duration:' in line:
                    # 解析时长
                    duration_match = re.search(r'Duration: (\d+:\d+:\d+\.\d+)', line)
                    if duration_match:
                        info['duration'] = duration_match.group(1)
                elif 'Stream' in line and 'Video:' in line:
                    # 解析视频信息
                    video_match = re.search(r'(\d+x\d+)', line)
                    if video_match:
                        info['resolution'] = video_match.group(1)
                elif 'Stream' in line and 'Audio:' in line:
                    # 解析音频信息
                    audio_match = re.search(r'(\d+ Hz)', line)
                    if audio_match:
                        info['audio_sample_rate'] = audio_match.group(1)
            
            return info
            
        except Exception as e:
            raise Exception(f"获取视频信息失败: {str(e)}")


def embed_subtitle_to_video(video_file: str, subtitle_file: str, output_file: str = None) -> str:
    """将字幕嵌入视频的便捷函数"""
    processor = VideoProcessor()
    return processor.embed_subtitle(video_file, subtitle_file, output_file)


def burn_subtitle_to_video(video_file: str, subtitle_file: str, output_file: str = None) -> str:
    """将字幕烧录到视频的便捷函数"""
    processor = VideoProcessor()
    return processor.burn_subtitle(video_file, subtitle_file, output_file)


# 导入re模块用于正则表达式
import re