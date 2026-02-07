# Video4Doc

**Convert MP4 videos to animated WebP/GIF/APNG for documentation, with powerful side-by-side comparison tools.**

WebP q=70 produces files **10x smaller than GIF** with nearly identical visual quality — perfect for docs, blogs, and Google Slides.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nj-1015/video4doc/blob/master/mp4_to_webp_converter.ipynb)

---

## Features

### Single Video Converter
- **Trim & crop** — Frame range selection + interactive ROI cropping
- **3 output formats** — WebP (lossy, tiny files), GIF (universal), APNG (lossless)
- **Speed control** — 0.25x to 4x playback speed
- **Ping-pong loop** — Boomerang-style forward+reverse animation
- **Image adjustments** — Brightness, contrast, colored border
- **Flexible output** — Custom filename, save locally or to Google Drive
- **Thumbnail export** — Save any frame as PNG

### Side-by-Side Comparison
- **Compare 2+ videos** — Before/after, different settings, algorithm comparison
- **Interactive ROI** — Synced crop region across all videos with zoom
- **3 layout modes**:
  - **Horizontal** — Videos side by side
  - **Vertical** — Videos stacked
  - **Split Screen** — Overlay with draggable split line
- **Captions & separators** — Label each video, adjustable colored gap between panels
- **Animated preview** — See the result before converting
- **Interactive HTML export** — Standalone draggable before/after slider

### Output Formats

| Format | Best For | File Size | Quality |
|--------|----------|-----------|---------|
| **WebP** | Docs, blogs, slides | Smallest (10% of GIF) | Excellent (lossy) |
| **GIF** | Legacy compatibility | Large | Good (256 colors) |
| **APNG** | Pixel-perfect archival | Largest | Lossless |

---

## Quick Start

1. **Open in Colab** — Click the badge above or [open directly](https://colab.research.google.com/github/nj-1015/video4doc/blob/master/mp4_to_webp_converter.ipynb)
2. **Run Setup cell** to install dependencies
3. **Upload your video(s)**
4. **Adjust settings** using the interactive UI
5. **Preview and Convert**

---

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

---

## Format Comparison: WebP vs GIF vs APNG

We benchmarked all three formats across 6 sample videos (864x480 to 1280x720, 16-60 frames):

| Format | Avg Size | Avg PSNR | Avg SSIM | Size vs GIF |
|--------|----------|----------|----------|-------------|
| GIF | 7,490 KB | 39.14 dB | 0.9992 | 100% |
| **WebP q=70** | **775 KB** | **38.36 dB** | **0.9984** | **10%** |
| WebP q=90 | 1,456 KB | 43.00 dB | 0.9995 | 19% |
| APNG | 11,041 KB | Lossless | 1.0000 | 147% |

**Key takeaway:** WebP q=70 delivers 98.4% of GIF's visual quality at just 10% of the file size. WebP q=90 actually *exceeds* GIF quality at 1/5th the size.

| Use Case | Recommended |
|----------|-------------|
| Documentation & blog posts | WebP q=70 |
| Google Slides | WebP (animated WebP supported) |
| Pixel-perfect archival | APNG |
| Legacy browser support | GIF |

See the [detailed report](format_comparison_report.md) and [interactive HTML comparison](format_comparison.html) for full analysis with side-by-side animated examples.

---

## UI Controls Reference

<details>
<summary><strong>Playback</strong></summary>

| Control | Description |
|---------|-------------|
| Frame Range | Trim start/end frames |
| Every Nth | Use every Nth frame (1 = all) |
| Speed | Playback speed (0.25x - 4x) |
| Loop | Enable animation loop |
| Ping-pong | Play forward then reverse |

</details>

<details>
<summary><strong>Adjustments</strong></summary>

| Control | Description |
|---------|-------------|
| Brightness | Adjust brightness (0.5 - 2.0) |
| Contrast | Adjust contrast (0.5 - 2.0) |
| Border | Add colored border (size + color) |
| Max Size | Limit output dimensions |

</details>

<details>
<summary><strong>Output</strong></summary>

| Control | Description |
|---------|-------------|
| Format | WebP, GIF, or APNG |
| Quality | Output quality (WebP only) |
| Output Name | Custom filename |
| Save to GDrive | Save directly to Google Drive |

</details>

<details>
<summary><strong>Side-by-Side Specific</strong></summary>

| Control | Description |
|---------|-------------|
| Layout | Horizontal / Vertical / Split Screen |
| Split % | Position of split line (split mode) |
| Sync ROI | Synchronize crop position across videos |
| Gap | Colored separator between videos (px) |
| Caption | Add text label to each video |

</details>

### Output Buttons

| Button | Description |
|--------|-------------|
| Preview | Show animated preview |
| Convert | Create WebP/GIF/APNG animation |
| Thumbnail | Save single frame as PNG |
| Interactive HTML | Create draggable before/after comparison slider |

---

## Requirements

- Python 3.7+
- OpenCV
- Pillow
- ipywidgets (for Colab UI)

## License

MIT
