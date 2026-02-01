# Video4Doc

Convert MP4 videos to animated WebP/GIF for documentation, with powerful comparison tools.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nj-1015/video4doc/blob/master/mp4_to_webp_converter.ipynb)

## Features

### Single Video Converter
- Trim start/end frames
- Crop region selection
- Quality and scale controls
- Speed adjustment (0.25x - 4x)
- Ping-pong (boomerang) loop
- Brightness/contrast adjustment
- Add colored border
- Export as WebP or GIF
- Save thumbnail as PNG

### Side-by-Side Converter
- Compare multiple videos
- Interactive ROI selection with sync option
- Three layout modes:
  - **Horizontal** - Videos side by side
  - **Vertical** - Videos stacked
  - **Split Screen** - Overlay with adjustable split line
- Add captions to each video
- Animated preview before conversion
- **Interactive HTML export** - Draggable before/after comparison slider

### Output Options
- Save locally or to Google Drive
- Interactive folder picker with create folder
- WebP or GIF format
- Adjustable quality and max size

## Quick Start

1. **Open in Colab**: Click the badge above or [open directly](https://colab.research.google.com/github/nj-1015/video4doc/blob/master/mp4_to_webp_converter.ipynb)

2. **Run Setup cell** to install dependencies

3. **Upload your video(s)**

4. **Adjust settings** using the interactive UI

5. **Preview and Convert**

## Usage Examples

### Single Video to WebP
```python
from video2webp import VideoInfo, WebPConverter

video = VideoInfo("input.mp4")
converter = WebPConverter(video)
converter.show()
```

### Side-by-Side Comparison
```python
from video2webp import VideoInfo, SideBySideConverter

videos = [VideoInfo("before.mp4"), VideoInfo("after.mp4")]
sbs = SideBySideConverter(videos)
sbs.show()
```

## UI Controls

### Playback
| Control | Description |
|---------|-------------|
| Frame Range | Trim start/end frames |
| Every Nth | Use every Nth frame (1 = all frames) |
| Speed | Playback speed (0.25x - 4x) |
| Loop | Enable animation loop |
| Ping-pong | Play forward then reverse |

### Adjustments
| Control | Description |
|---------|-------------|
| Brightness | Adjust brightness (0.5 - 2.0) |
| Contrast | Adjust contrast (0.5 - 2.0) |
| Border | Add colored border |
| Max Size | Limit output dimensions |

### Output
| Control | Description |
|---------|-------------|
| Format | WebP or GIF |
| Quality | Output quality (WebP only) |
| Save to GDrive | Save directly to Google Drive |

### Side-by-Side Specific
| Control | Description |
|---------|-------------|
| Layout | Horizontal / Vertical / Split Screen |
| Split % | Position of split line (split mode) |
| Sync ROI | Synchronize crop position across videos |
| Caption | Add text label to each video |

## Output Buttons

| Button | Description |
|--------|-------------|
| Preview | Show animated preview |
| Convert | Create WebP/GIF animation |
| Thumbnail | Save single frame as PNG |
| Interactive HTML | Create draggable comparison slider (2 videos) |

## Interactive HTML Comparison

The "Interactive HTML" button creates a standalone HTML file with a draggable slider for before/after comparison. Perfect for embedding in documentation or sharing.

## Requirements

- Python 3.7+
- OpenCV
- Pillow
- ipywidgets (for Colab UI)

## License

MIT
