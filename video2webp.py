"""MP4 to Animated WebP Converter Module"""

import cv2
import numpy as np
from PIL import Image
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import io
import base64
import os


class VideoInfo:
    """Stores video metadata."""
    def __init__(self, filename):
        self.filename = filename
        cap = cv2.VideoCapture(filename)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        cap.release()

    def __repr__(self):
        return (f"Video: {self.filename}\n"
                f"  Resolution: {self.width} x {self.height}\n"
                f"  Frames: {self.total_frames}\n"
                f"  FPS: {self.fps:.2f}\n"
                f"  Duration: {self.duration:.2f}s")


class WebPConverter:
    """Interactive MP4 to WebP converter with UI controls."""

    def __init__(self, video_info):
        self.video = video_info
        self._create_widgets()
        self._setup_preview()

    def _create_widgets(self):
        style = {'description_width': '120px'}
        layout = widgets.Layout(width='500px')

        self.frame_range = widgets.IntRangeSlider(
            value=[0, self.video.total_frames - 1],
            min=0, max=self.video.total_frames - 1,
            step=1, description='Frame Range:',
            style=style, layout=layout, continuous_update=False
        )

        self.crop_x = widgets.IntRangeSlider(
            value=[0, self.video.width],
            min=0, max=self.video.width,
            step=1, description='Crop X (L-R):',
            style=style, layout=layout, continuous_update=False
        )

        self.crop_y = widgets.IntRangeSlider(
            value=[0, self.video.height],
            min=0, max=self.video.height,
            step=1, description='Crop Y (T-B):',
            style=style, layout=layout, continuous_update=False
        )

        self.quality = widgets.IntSlider(
            value=70, min=1, max=100,
            step=1, description='Quality (%):',
            style=style, layout=layout
        )

        self.scale = widgets.FloatSlider(
            value=1.0, min=0.1, max=2.0,
            step=0.1, description='Output Scale:',
            style=style, layout=layout
        )

        self.frame_skip = widgets.IntSlider(
            value=1, min=1, max=10,
            step=1, description='Frame Skip:',
            style=style, layout=layout
        )

        self.loop = widgets.Checkbox(
            value=True, description='Loop Animation', style=style
        )

        self.preview_output = widgets.Output()
        self.preview_btn = widgets.Button(description='Preview Frame', button_style='info')
        self.convert_btn = widgets.Button(description='Convert to WebP', button_style='success')
        self.status_output = widgets.Output()

    def _setup_preview(self):
        self.preview_btn.on_click(self._show_preview)
        self.convert_btn.on_click(self._convert)

    def _get_frame(self, frame_num):
        """Extract and process a single frame."""
        cap = cv2.VideoCapture(self.video.filename)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        x1, x2 = self.crop_x.value
        y1, y2 = self.crop_y.value
        frame = frame[y1:y2, x1:x2]

        if self.scale.value != 1.0:
            new_w = int(frame.shape[1] * self.scale.value)
            new_h = int(frame.shape[0] * self.scale.value)
            frame = cv2.resize(frame, (new_w, new_h))

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _show_preview(self, _=None):
        with self.preview_output:
            clear_output(wait=True)
            frame_rgb = self._get_frame(self.frame_range.value[0])
            if frame_rgb is not None:
                img = Image.fromarray(frame_rgb)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                display(HTML(f'<img src="data:image/png;base64,{img_str}" style="max-width:600px"/>'))
                print(f"Preview: Frame {self.frame_range.value[0]}, Size: {img.width}x{img.height}")

    def _convert(self, _=None):
        with self.status_output:
            clear_output(wait=True)
            print("Converting to animated WebP...")

            start_frame, end_frame = self.frame_range.value
            frames = []

            for i in range(start_frame, end_frame + 1):
                if (i - start_frame) % self.frame_skip.value != 0:
                    continue

                frame_rgb = self._get_frame(i)
                if frame_rgb is not None:
                    frames.append(Image.fromarray(frame_rgb))

                if len(frames) % 50 == 0:
                    print(f"Processed {len(frames)} frames...")

            if not frames:
                print("Error: No frames extracted!")
                return

            effective_fps = self.video.fps / self.frame_skip.value
            duration_ms = int(1000 / effective_fps)

            self.output_filename = os.path.splitext(self.video.filename)[0] + '.webp'

            frames[0].save(
                self.output_filename, 'WEBP',
                save_all=True, append_images=frames[1:],
                duration=duration_ms,
                loop=0 if self.loop.value else 1,
                quality=self.quality.value
            )

            file_size = os.path.getsize(self.output_filename) / (1024 * 1024)
            print(f"\nDone! Saved: {self.output_filename}")
            print(f"Frames: {len(frames)}, Size: {file_size:.2f} MB")

    def show(self):
        """Display the converter UI."""
        display(widgets.VBox([
            widgets.HTML('<h4>Trim Frames</h4>'),
            self.frame_range,
            widgets.HTML('<h4>Crop Region</h4>'),
            self.crop_x, self.crop_y,
            widgets.HTML('<h4>Output Settings</h4>'),
            self.quality, self.scale, self.frame_skip, self.loop,
            widgets.HBox([self.preview_btn, self.convert_btn]),
            self.preview_output,
            self.status_output
        ]))

    def preview_result(self):
        """Display the converted WebP animation."""
        if not hasattr(self, 'output_filename') or not os.path.exists(self.output_filename):
            print("No output file. Run conversion first.")
            return

        with open(self.output_filename, 'rb') as f:
            webp_data = base64.b64encode(f.read()).decode()
        display(HTML(f'<img src="data:image/webp;base64,{webp_data}" style="max-width:800px"/>'))

    def download(self):
        """Trigger file download in Colab."""
        from google.colab import files
        if hasattr(self, 'output_filename') and os.path.exists(self.output_filename):
            files.download(self.output_filename)
        else:
            print("No output file. Run conversion first.")
