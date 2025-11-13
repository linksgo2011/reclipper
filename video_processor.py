import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
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
        print(f"🔧 开始嵌入软字幕...")
        print(f"   视频文件: {video_file}")
        print(f"   字幕文件: {subtitle_file}")
        print(f"   字幕语言: {subtitle_language}")
        
        video_path = Path(video_file)
        subtitle_path = Path(subtitle_file)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
        
        # 生成输出文件路径
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}")
        
        print(f"   输出文件: {output_file}")
        
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
        
        print(f"   FFmpeg命令: {' '.join(cmd[:6])}... [命令已简化显示]")
        
        try:
            print(f"   🚀 开始执行FFmpeg命令...")
            
            # 执行ffmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode != 0:
                print(f"   ❌ FFmpeg执行失败，退出码: {result.returncode}")
                print(f"   错误信息: {result.stderr}")
                raise Exception(f"ffmpeg执行失败: {result.stderr}")
            
            print(f"   ✅ FFmpeg命令执行成功")
            print(f"   标准输出: {result.stdout}" if result.stdout else "   标准输出: [空]")
            print(f"   🎉 字幕处理完成: {output_file}")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ FFmpeg处理失败: {str(e)}")
            print(f"   错误输出: {e.stderr}" if hasattr(e, 'stderr') else "   无错误输出")
            raise Exception(f"ffmpeg处理失败: {str(e)}")
        except FileNotFoundError:
            print(f"   ❌ 未找到ffmpeg，请确保已安装ffmpeg并添加到PATH环境变量")
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
        print(f"🔥 开始烧录硬字幕...")
        print(f"   视频文件: {video_file}")
        print(f"   字幕文件: {subtitle_file}")
        print(f"   字体大小: {font_size}")
        print(f"   字体颜色: {font_color}")
        
        video_path = Path(video_file)
        subtitle_path = Path(subtitle_file)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
        
        # 生成输出文件路径
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_burned_subtitles{video_path.suffix}")
        
        print(f"   输出文件: {output_file}")
        
        # 构建ffmpeg命令（硬字幕）
        cmd = [
            self.ffmpeg_path,
            '-i', video_file,
            '-vf', f"subtitles={subtitle_file}:force_style='FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)}'",
            '-c:a', 'copy',
            output_file,
            '-y'
        ]
        
        print(f"   FFmpeg命令: {' '.join(cmd[:4])}... [命令已简化显示]")
        
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

    def _deoverlap_srt(self, srt_path: str, epsilon: float = 0.02) -> str:
        """生成去重叠版SRT并返回新文件路径"""
        content = Path(srt_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        out_lines = []
        i = 0
        prev_end = None
        prev_time_line_index = -1
        while i < len(content):
            line = content[i].strip()
            if re.match(r"^\d+$", line):
                out_lines.append(content[i])
                i += 1
                if i >= len(content):
                    break
                tline = content[i].strip()
                m = re.match(r"^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", tline)
                if not m:
                    out_lines.append(content[i])
                    i += 1
                    continue
                start = self._parse_time_srt(m.group(1))
                end = self._parse_time_srt(m.group(2))
                
                # 检测到重叠时，修改前一个字幕的结束时间而不是当前字幕的开始时间
                if prev_end is not None and start < prev_end:
                    # 找到前一个字幕的时间轴行并修改结束时间
                    if prev_time_line_index >= 0:
                        # 提前前一个字幕的结束时间，留出epsilon间隙
                        new_prev_end = start - epsilon
                        if new_prev_end > self._parse_time_srt(m.group(1)):
                            new_prev_end = self._parse_time_srt(m.group(1)) - epsilon
                        # 更新前一个字幕的时间轴行
                        prev_time_line = out_lines[prev_time_line_index]
                        prev_m = re.match(r"^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", prev_time_line)
                        if prev_m:
                            prev_start_str = prev_m.group(1)
                            new_prev_end_str = self._format_time_srt(new_prev_end)
                            out_lines[prev_time_line_index] = f"{prev_start_str} --> {new_prev_end_str}"
                            prev_end = new_prev_end
                
                out_lines.append(f"{self._format_time_srt(start)} --> {self._format_time_srt(end)}")
                prev_time_line_index = len(out_lines) - 1  # 记录当前时间轴行的索引
                i += 1
                while i < len(content) and content[i].strip() != "":
                    out_lines.append(content[i])
                    i += 1
                out_lines.append("")
                prev_end = end
            else:
                out_lines.append(content[i])
                i += 1
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".srt")
        Path(tmp.name).write_text("\n".join(out_lines), encoding="utf-8")
        tmp.close()
        return tmp.name
    
    def burn_bilingual_subtitle(self, video_file: str, chinese_subtitle_file: str, 
                               english_subtitle_file: str,
                               output_file: Optional[str] = None,
                               chinese_font_size: int = 20,
                               english_font_size: int = 16,
                               chinese_font_color: str = "white",
                               english_font_color: str = "yellow",
                               wrap_style: int = 2,
                               play_res_y: Optional[int] = None) -> str:
        video_path = Path(video_file)
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_bilingual{video_path.suffix}")

        # 预处理以消除时间重叠
        eng_srt = self._deoverlap_srt(english_subtitle_file)
        chi_srt = self._deoverlap_srt(chinese_subtitle_file)

        # 组装样式字符串
        eng_style = f"FontSize={english_font_size},PrimaryColour=&H{self._color_to_hex(english_font_color)},Alignment=2,WrapStyle={wrap_style},MarginV=40"
        chi_style = f"FontSize={chinese_font_size},PrimaryColour=&H{self._color_to_hex(chinese_font_color)},Alignment=2,WrapStyle={wrap_style},MarginV=20"
        if play_res_y is not None:
            eng_style += f",PlayResY={play_res_y}"
            chi_style += f",PlayResY={play_res_y}"

        cmd = [
            self.ffmpeg_path,
            "-i", video_file,
            "-vf",
            (
                f"subtitles='{eng_srt}':force_style='{eng_style}',"
                f"subtitles='{chi_srt}':force_style='{chi_style}'"
            ),
            "-c:a", "copy",
            output_file,
            "-y"
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_file

    def burn_english_subtitle(self, video_file: str, english_subtitle_file: str,
                             output_file: Optional[str] = None,
                             font_size: int = 20,
                             font_color: str = "white",
                             wrap_style: int = 2,
                             play_res_y: Optional[int] = None) -> str:
        video_path = Path(video_file)
        if output_file is None:
            output_file = str(video_path.parent / f"{video_path.stem}_english{video_path.suffix}")

        # 预处理以消除时间重叠
        eng_srt = self._deoverlap_srt(english_subtitle_file)

        style = f"FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)},Alignment=2,WrapStyle={wrap_style},MarginV=20"
        if play_res_y is not None:
            style += f",PlayResY={play_res_y}"

        cmd = [
            self.ffmpeg_path,
            "-i", video_file,
            "-vf", f"subtitles='{eng_srt}':force_style='{style}'",
            "-c:a", "copy",
            output_file,
            "-y"
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_file
    
    def create_bilingual_subtitle_file(self, chinese_subtitle_file: str, 
                                      english_subtitle_file: str = None,
                                      output_file: Optional[str] = None) -> str:
        """
        创建中英双语字幕文件（ASS格式）
        
        Args:
            chinese_subtitle_file: 中文字幕文件路径
            english_subtitle_file: 英文字幕文件路径（可选）
            output_file: 输出文件路径
            
        Returns:
            输出文件路径
        """
        print(f"📝 开始创建双语字幕文件...")
        print(f"   中文字幕文件: {chinese_subtitle_file}")
        print(f"   英文字幕文件: {english_subtitle_file}")
        
        chinese_subtitle_path = Path(chinese_subtitle_file)
        
        if not chinese_subtitle_path.exists():
            raise FileNotFoundError(f"中文字幕文件不存在: {chinese_subtitle_file}")
        
        # 生成输出文件路径
        if output_file is None:
            suffix = "_bilingual.ass" if english_subtitle_file else "_chinese.ass"
            output_file = str(chinese_subtitle_path.parent / f"{chinese_subtitle_path.stem}{suffix}")
        
        print(f"   输出文件: {output_file}")
        
        # 读取中文字幕
        chinese_subtitles = self._read_subtitle_file(chinese_subtitle_file)
        print(f"   读取到 {len(chinese_subtitles)} 条中文字幕")
        
        # 读取英文字幕（如果存在）
        english_subtitles = []
        if english_subtitle_file and Path(english_subtitle_file).exists():
            english_subtitles = self._read_subtitle_file(english_subtitle_file)
            print(f"   读取到 {len(english_subtitles)} 条英文字幕")
        else:
            print(f"   英文字幕文件不存在或未提供，仅创建中文字幕")
        
        # 创建ASS格式的双语字幕
        ass_content = self._create_ass_header()
        
        bilingual_count = 0
        chinese_only_count = 0
        
        for i, chinese_sub in enumerate(chinese_subtitles):
            start_time = self._format_time_ass(chinese_sub['start_time'])
            end_time = self._format_time_ass(chinese_sub['end_time'])
            chinese_text = chinese_sub['text']
            
            # 查找对应的英文字幕
            english_text = ""
            if english_subtitles:
                for eng_sub in english_subtitles:
                    if (abs(eng_sub['start_time'] - chinese_sub['start_time']) < 0.5 and 
                        abs(eng_sub['end_time'] - chinese_sub['end_time']) < 0.5):
                        english_text = eng_sub['text']
                        break
            
            # 创建双语字幕行
            if english_text:
                # 中英双语：中文在上，英文在下，添加Alignment=2确保不滚动
                chinese_style = "{\\fs28}"
                english_style = "{\\fs20\\c&H00FFFF&}"
                subtitle_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{chinese_style}{chinese_text}\\N{english_style}{english_text}"
                bilingual_count += 1
            else:
                # 只有中文，添加Alignment=2确保不滚动
                chinese_style = "{\\fs28}"
                subtitle_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{chinese_style}{chinese_text}"
                chinese_only_count += 1
            
            ass_content += subtitle_line + "\n"
        
        print(f"   生成双语字幕: {bilingual_count} 条")
        print(f"   仅中文字幕: {chinese_only_count} 条")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        print(f"✅ 双语字幕文件创建完成: {output_file}")
        
        return output_file
    
    def _read_subtitle_file(self, subtitle_file: str) -> List[dict]:
        """读取字幕文件并解析为列表"""
        subtitles = []
        
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的SRT格式解析
        if subtitle_file.endswith('.srt'):
            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 解析时间轴
                    time_line = lines[1]
                    if '-->' in time_line:
                        start_str, end_str = time_line.split(' --> ')
                        start_time = self._parse_time_srt(start_str)
                        end_time = self._parse_time_srt(end_str)
                        
                        # 合并文本行
                        text = ' '.join(lines[2:])
                        
                        subtitles.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
        
        # 简单的VTT格式解析
        elif subtitle_file.endswith('.vtt'):
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if '-->' in line:
                    start_str, end_str = line.split(' --> ')
                    start_time = self._parse_time_vtt(start_str)
                    end_time = self._parse_time_vtt(end_str)
                    
                    # 收集文本
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip() and not '-->' in lines[i]:
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        text = ' '.join(text_lines)
                        subtitles.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
                else:
                    i += 1
        
        return subtitles
    
    def _parse_time_srt(self, time_str: str) -> float:
        """解析SRT格式的时间"""
        parts = time_str.replace(',', '.').split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0
    
    def _parse_time_vtt(self, time_str: str) -> float:
        """解析VTT格式的时间"""
        time_str = time_str.split(' ')[0]  # 去除可能的对齐信息
        return self._parse_time_srt(time_str)
    
    def _format_time_srt(self, seconds: float) -> str:
        """格式化为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        s = seconds % 60
        whole = int(s)
        ms = int(round((s - whole) * 1000))
        return f"{hours:02d}:{minutes:02d}:{whole:02d},{ms:03d}"

    def _format_time_ass(self, seconds: float) -> str:
        """格式化为ASS时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def _create_ass_header(self) -> str:
        """创建ASS字幕文件头部"""
        return """[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
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