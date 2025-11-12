import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
import re
from config import get_settings


class YouTubeDownloader:
    """YouTube视频下载器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.download_dir = Path(self.settings.download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_video(self, url: str, download_subtitles: bool = True) -> Dict[str, Any]:
        """
        下载YouTube视频和字幕
        
        Args:
            url: YouTube视频URL
            download_subtitles: 是否下载字幕
            
        Returns:
            下载结果信息
        """
        # 配置yt-dlp选项 - 解决403错误和兼容性问题
        ydl_opts = {
            # 格式选择：简化格式选择，避免复杂过滤
            'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            
            # 字幕配置
            'writesubtitles': download_subtitles,
            'writeautomaticsub': download_subtitles,
            'subtitleslangs': ['en'],  
            'subtitlesformat': 'srt',
            
            # 输出配置
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,  # 设置为False以获取真实错误
            
            # 解决403错误的配置
            'throttledratelimit': 1024,  # 限制下载速度
            'ratelimit': 2097152,  # 2MB/s 限制
            'sleep_interval': 2,  # 请求间隔
            'max_sleep_interval': 5,
            
            # 网络和重试配置
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'retry_sleep_functions': {
                'http': lambda n: 2 ** n,  # 指数退避
            },
            
            # 兼容性配置
            'extractaudio': False,
            'keepvideo': True,
            'noplaylist': True,
            
            # 格式排序：简化排序
            'format_sort': ['res:720', 'res:480'],
            
            # 高级配置
            'hls_prefer_native': True,
            'hls_use_mpegts': False,
            'http_chunk_size': 5242880,  # 5MB chunks
            
            # 用户代理和cookies配置
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            
            # 避免触发反爬虫机制
            'no_check_certificate': True,
            'prefer_insecure': False,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
        }
        
        try:
            # 下载视频
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # 检查下载结果
                if info:
                    # 获取实际下载的文件名
                    actual_filename = ydl.prepare_filename(info)
                    video_file = Path(actual_filename)
                    
                    # 检查文件是否实际存在且大小合理
                    if video_file.exists() and video_file.stat().st_size > 1024:  # 至少1KB
                        result = {
                            'success': True,
                            'video_file': str(video_file),
                            'title': info['title'],
                            'duration': info.get('duration', 0),
                            'filesize': video_file.stat().st_size,
                            'subtitles': {}
                        }
                        
                        # 查找字幕文件
                        if download_subtitles:
                            subtitle_files = self._find_subtitle_files(info['title'])
                            result['subtitles'] = subtitle_files
                            
                        # 查找字幕文件（兼容旧格式）
                        subtitle_files_list = list(self.download_dir.glob(f"{info['title']}.*.vtt"))
                        subtitle_files_list += list(self.download_dir.glob(f"{info['title']}.*.srt"))
                        result['subtitle_files'] = [str(f) for f in subtitle_files_list]
                        
                        return result
                    else:
                        error_msg = f"视频文件下载失败，文件不存在或大小异常。文件路径: {video_file}"
                        # 如果文件存在但大小异常，删除它
                        if video_file.exists():
                            video_file.unlink()
                        raise Exception(error_msg)
                else:
                    raise Exception("无法获取视频信息")
                    
        except Exception as e:
            # 记录详细错误信息
            import traceback
            error_info = f"下载视频失败: {str(e)}\n{traceback.format_exc()}"
            raise Exception(error_info)
    
    def _find_subtitle_files(self, video_title: str) -> Dict[str, str]:
        """查找字幕文件"""
        subtitle_files = {}
        
        # 可能的字幕文件扩展名
        subtitle_extensions = ['.srt', '.vtt', '.ass']
        
        # 清理文件名中的特殊字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
        
        for ext in subtitle_extensions:
            # 查找英文字幕
            subtitle_file = self.download_dir / f"{safe_title}.en{ext}"
            if subtitle_file.exists():
                subtitle_files['en'] = str(subtitle_file)
            
            # 查找中文字幕
            for lang in ['zh', 'zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW']:
                subtitle_file = self.download_dir / f"{safe_title}.{lang}{ext}"
                if subtitle_file.exists():
                    subtitle_files[lang] = str(subtitle_file)
        
        # 如果没找到，尝试原始文件名
        if not subtitle_files:
            for ext in subtitle_extensions:
                subtitle_file = self.download_dir / f"{video_title}.en{ext}"
                if subtitle_file.exists():
                    subtitle_files['en'] = str(subtitle_file)
        
        return subtitle_files
    
    def get_available_subtitles(self, url: str) -> Dict[str, str]:
        """获取可用的字幕列表"""
        ydl_opts = {
            'writesubtitles': False,
            'writeautomaticsub': False,
            'listsubtitles': True,
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                return info_dict.get('subtitles', {}) or info_dict.get('automatic_captions', {})
        except Exception as e:
            raise Exception(f"获取字幕列表失败: {str(e)}")


def download_youtube_video(url: str) -> Dict[str, Any]:
    """下载YouTube视频的便捷函数"""
    downloader = YouTubeDownloader()
    return downloader.download_video(url)