# Animated Image Format Comparison: WebP vs GIF vs APNG

## Test Setup

- **Source Videos**: 6 MP4 clips from `gt/` directory
- **Resolutions**: 864x480 (2 videos), 1280x720 (4 videos)
- **Frame counts**: 16 frames (5 videos), 60 frames (1 video)
- **FPS**: 8 (5 videos), 25 (1 video)
- **WebP quality levels tested**: 50, 70, 90
- **Metrics**: File size, PSNR (dB), SSIM, encoding time
- **Tool**: Pillow (PIL) for encoding/decoding

## Results Per Video

### 40.mp4 (864x480, 16 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 5,031 | 40.13 | 0.9996 | 1.18 |
| APNG | 8,683 | Lossless | 1.0000 | 0.52 |
| WebP q=50 | 826 | 33.38 | 0.9962 | 1.06 |
| WebP q=70 | 1,026 | 35.24 | 0.9976 | 0.33 |
| WebP q=90 | 1,764 | 41.23 | 0.9994 | 0.46 |

### 8.mp4 (864x480, 16 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 2,806 | 40.87 | 0.9998 | 0.84 |
| APNG | 4,033 | Lossless | 1.0000 | 0.37 |
| WebP q=50 | 225 | 36.22 | 0.9992 | 0.19 |
| WebP q=70 | 271 | 37.73 | 0.9995 | 0.21 |
| WebP q=90 | 456 | 41.28 | 0.9998 | 0.29 |

### animal.mp4 (1280x720, 16 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 6,864 | 40.22 | 0.9984 | 1.55 |
| APNG | 10,727 | Lossless | 1.0000 | 1.04 |
| WebP q=50 | 408 | 37.82 | 0.9957 | 0.44 |
| WebP q=70 | 525 | 39.25 | 0.9970 | 0.46 |
| WebP q=90 | 1,021 | 43.23 | 0.9989 | 0.64 |

### closeshot.mp4 (1280x720, 16 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 6,045 | 40.45 | 0.9995 | 1.40 |
| APNG | 6,940 | Lossless | 1.0000 | 0.82 |
| WebP q=50 | 357 | 37.25 | 0.9977 | 0.45 |
| WebP q=70 | 433 | 40.43 | 0.9991 | 0.46 |
| WebP q=90 | 828 | 45.38 | 0.9997 | 0.62 |

### face.mp4 (1280x720, 60 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 20,362 | 36.30 | 0.9987 | 7.79 |
| APNG | 29,646 | Lossless | 1.0000 | 3.10 |
| WebP q=50 | 1,330 | 37.78 | 0.9982 | 1.54 |
| WebP q=70 | 1,748 | 39.57 | 0.9989 | 1.64 |
| WebP q=90 | 3,564 | 43.97 | 0.9996 | 2.20 |

### view.mp4 (1280x720, 16 frames)
| Format | Size (KB) | PSNR (dB) | SSIM | Encode (s) |
|--------|-----------|-----------|------|------------|
| GIF | 3,832 | 36.89 | 0.9992 | 2.38 |
| APNG | 6,216 | Lossless | 1.0000 | 0.66 |
| WebP q=50 | 541 | 35.28 | 0.9963 | 0.48 |
| WebP q=70 | 649 | 37.93 | 0.9980 | 0.49 |
| WebP q=90 | 1,101 | 42.93 | 0.9995 | 0.64 |

## Summary: Average Across All Videos

| Format | Avg Size (KB) | Avg PSNR (dB) | Avg SSIM | Avg Encode (s) |
|--------|---------------|---------------|----------|-----------------|
| GIF | 7,490 | 39.14 | 0.9992 | 2.52 |
| APNG | 11,041 | Lossless | 1.0000 | 1.09 |
| WebP q=50 | 614 | 36.29 | 0.9972 | 0.69 |
| WebP q=70 | 775 | 38.36 | 0.9984 | 0.60 |
| WebP q=90 | 1,456 | 43.00 | 0.9995 | 0.81 |

## Size Ratios (GIF = 100% baseline)

| Format | Size vs GIF |
|--------|-------------|
| GIF | 100% |
| APNG | 147% (+47%) |
| WebP q=50 | 8.2% (-92%) |
| WebP q=70 | 10.3% (-90%) |
| WebP q=90 | 19.4% (-81%) |

## Key Findings

### 1. File Size: WebP wins overwhelmingly
- **WebP q=70 is ~10x smaller than GIF** and ~14x smaller than APNG on average
- Even WebP q=90 (highest quality tested) is **~5x smaller than GIF**
- APNG is the largest format, averaging **47% larger than GIF**
- GIF's LZW compression cannot compete with WebP's VP8 lossy codec

### 2. Visual Quality: APNG > WebP q=90 >= GIF > WebP q=70 > WebP q=50
- **APNG is lossless** (PSNR = infinity, SSIM = 1.0000) - pixel-perfect reproduction
- **WebP q=90 matches or exceeds GIF quality** (avg 43.00 vs 39.14 dB PSNR) at 1/5th the size
- **GIF's 256-color palette** causes color banding but still achieves decent PSNR (~39 dB) because dithering distributes the error
- **WebP q=70** achieves near-GIF quality (38.36 vs 39.14 dB) at 1/10th the file size
- All formats achieve SSIM > 0.99, meaning structural similarity is excellent across the board

### 3. Encoding Speed: APNG is fastest
- APNG encodes fastest on average (1.09s) due to simple PNG compression per frame
- WebP encoding is moderate (0.60-0.81s) and scales well
- GIF is slowest (2.52s) due to palette quantization overhead per frame

### 4. Quality-per-Byte Efficiency
WebP provides the best quality-per-byte ratio by far:
- WebP q=70 delivers **98.4% of GIF's SSIM** at **10% of GIF's file size**
- WebP q=90 delivers **99.97% SSIM** (near-lossless) at **19% of GIF's file size**

## Recommendations

| Use Case | Recommended Format |
|----------|-------------------|
| Documentation & blog posts | **WebP q=70** - best size/quality balance |
| Maximum compatibility (older browsers) | **GIF** - universal support, but huge files |
| Quality-critical, size doesn't matter | **APNG** - lossless, perfect reproduction |
| High quality, reasonable size | **WebP q=90** - near-lossless at ~1/5 GIF size |
| Bandwidth-constrained / mobile | **WebP q=50** - acceptable quality, tiny files |

## Browser Support (as of 2025)

| Format | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| WebP | Yes | Yes | Yes (14+) | Yes |
| GIF | Yes | Yes | Yes | Yes |
| APNG | Yes | Yes | Yes | Yes |

All three formats now have broad browser support. WebP was the last to achieve universal coverage (Safari 14, released 2020), but this is no longer a concern for modern browsers.
