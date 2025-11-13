from ..video_processor import VideoProcessor
from typing import Optional

def test_burn_english_subtitle(video_file: str, subtitle_file: str, output_file: Optional[str] = None) -> str:
    processor = VideoProcessor()
    return processor.burn_english_subtitle(
        video_file,
        subtitle_file,
        output_file,
        font_size=22,
        font_color="white",
        wrap_style=2,
    )

if __name__ == "__main__":
    video = "/Users/ning/www/reclipper/test_gen.mp4"
    srt = "/Users/ning/www/reclipper/test_subtitle.en.srt"
    output = test_burn_english_subtitle(video, srt)
    print(f"Generated video with English subtitles: {output}")