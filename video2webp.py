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


class VideoROISelector:
    """Interactive ROI selector for a single video."""

    def __init__(self, video_info, index=0):
        self.video = video_info
        self.index = index
        self._create_widgets()

    def _create_widgets(self):
        style = {'description_width': '80px'}
        layout = widgets.Layout(width='400px')

        self.roi_x = widgets.IntRangeSlider(
            value=[0, self.video.width],
            min=0, max=self.video.width,
            step=1, description='ROI X:',
            style=style, layout=layout, continuous_update=False
        )

        self.roi_y = widgets.IntRangeSlider(
            value=[0, self.video.height],
            min=0, max=self.video.height,
            step=1, description='ROI Y:',
            style=style, layout=layout, continuous_update=False
        )

        self.preview_frame = widgets.IntSlider(
            value=0, min=0, max=self.video.total_frames - 1,
            step=1, description='Frame:',
            style=style, layout=layout, continuous_update=False
        )

        self.preview_output = widgets.Output()

        # Link preview updates
        self.roi_x.observe(self._update_preview, names='value')
        self.roi_y.observe(self._update_preview, names='value')
        self.preview_frame.observe(self._update_preview, names='value')

    def _get_frame_with_roi(self):
        """Get frame with ROI rectangle overlay."""
        cap = cv2.VideoCapture(self.video.filename)
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_frame.value)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        x1, x2 = self.roi_x.value
        y1, y2 = self.roi_y.value

        # Draw ROI rectangle
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # Scale down for preview if too large
        max_preview = 400
        h, w = frame_rgb.shape[:2]
        if w > max_preview or h > max_preview:
            scale = max_preview / max(w, h)
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)))

        return frame_rgb

    def _update_preview(self, _=None):
        with self.preview_output:
            clear_output(wait=True)
            frame = self._get_frame_with_roi()
            if frame is not None:
                img = Image.fromarray(frame)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                display(HTML(f'<img src="data:image/png;base64,{img_str}"/>'))
                x1, x2 = self.roi_x.value
                y1, y2 = self.roi_y.value
                print(f"ROI: {x2-x1} x {y2-y1} px")

    def get_roi(self):
        """Return current ROI as (x1, y1, x2, y2)."""
        return (self.roi_x.value[0], self.roi_y.value[0],
                self.roi_x.value[1], self.roi_y.value[1])

    def get_widget(self):
        """Return widget for display."""
        return widgets.VBox([
            widgets.HTML(f'<b>Video {self.index + 1}: {os.path.basename(self.video.filename)}</b>'),
            widgets.HTML(f'<small>{self.video.width}x{self.video.height}, {self.video.total_frames} frames</small>'),
            self.preview_frame,
            self.roi_x,
            self.roi_y,
            self.preview_output
        ])


class SideBySideConverter:
    """Create side-by-side animated WebP from multiple videos."""

    def __init__(self, video_list):
        """
        Args:
            video_list: List of VideoInfo objects
        """
        self.videos = video_list
        self.selectors = [VideoROISelector(v, i) for i, v in enumerate(video_list)]
        self._syncing = False  # Flag to prevent recursive sync
        self._create_widgets()
        self._setup_roi_sync()

    def _create_widgets(self):
        style = {'description_width': '120px'}
        layout = widgets.Layout(width='400px')

        # Find common frame range
        min_frames = min(v.total_frames for v in self.videos)

        self.frame_range = widgets.IntRangeSlider(
            value=[0, min_frames - 1],
            min=0, max=min_frames - 1,
            step=1, description='Frame Range:',
            style=style, layout=layout, continuous_update=False
        )

        self.layout_select = widgets.RadioButtons(
            options=[('Horizontal (side by side)', 'horizontal'),
                     ('Vertical (stacked)', 'vertical')],
            value='horizontal',
            description='Layout:',
            style=style
        )

        self.quality = widgets.IntSlider(
            value=70, min=1, max=100,
            step=1, description='Quality (%):',
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

        self.output_name = widgets.Text(
            value='side_by_side.webp',
            description='Output File:',
            style=style, layout=layout
        )

        self.sync_roi = widgets.Checkbox(
            value=False, description='Sync ROI position', style=style
        )

        self.preview_btn = widgets.Button(description='Preview Combined', button_style='info')
        self.convert_btn = widgets.Button(description='Convert to WebP', button_style='success')
        self.preview_output = widgets.Output()
        self.status_output = widgets.Output()

        self.preview_btn.on_click(self._show_preview)
        self.convert_btn.on_click(self._convert)

    def _setup_roi_sync(self):
        """Setup ROI synchronization between videos."""
        def make_sync_handler(source_idx, axis):
            def handler(change):
                if not self.sync_roi.value or self._syncing:
                    return
                self._syncing = True
                try:
                    for i, sel in enumerate(self.selectors):
                        if i != source_idx:
                            slider = sel.roi_x if axis == 'x' else sel.roi_y
                            # Clamp values to target video dimensions
                            max_val = sel.video.width if axis == 'x' else sel.video.height
                            new_val = (min(change['new'][0], max_val),
                                       min(change['new'][1], max_val))
                            slider.value = new_val
                finally:
                    self._syncing = False
            return handler

        for i, sel in enumerate(self.selectors):
            sel.roi_x.observe(make_sync_handler(i, 'x'), names='value')
            sel.roi_y.observe(make_sync_handler(i, 'y'), names='value')

    def _extract_roi_frame(self, video, roi, frame_num):
        """Extract a cropped frame from video."""
        cap = cv2.VideoCapture(video.filename)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        x1, y1, x2, y2 = roi
        frame = frame[y1:y2, x1:x2]
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _combine_frames(self, frame_list):
        """Combine multiple frames into one."""
        if self.layout_select.value == 'horizontal':
            # Match heights
            max_h = max(f.shape[0] for f in frame_list)
            resized = []
            for f in frame_list:
                if f.shape[0] != max_h:
                    scale = max_h / f.shape[0]
                    new_w = int(f.shape[1] * scale)
                    f = cv2.resize(f, (new_w, max_h))
                resized.append(f)
            return np.hstack(resized)
        else:
            # Match widths
            max_w = max(f.shape[1] for f in frame_list)
            resized = []
            for f in frame_list:
                if f.shape[1] != max_w:
                    scale = max_w / f.shape[1]
                    new_h = int(f.shape[0] * scale)
                    f = cv2.resize(f, (max_w, new_h))
                resized.append(f)
            return np.vstack(resized)

    def _show_preview(self, _=None):
        with self.preview_output:
            clear_output(wait=True)
            frame_num = self.frame_range.value[0]
            frames = []
            for sel in self.selectors:
                roi = sel.get_roi()
                f = self._extract_roi_frame(sel.video, roi, frame_num)
                if f is not None:
                    frames.append(f)

            if len(frames) == len(self.videos):
                combined = self._combine_frames(frames)
                img = Image.fromarray(combined)

                # Scale for preview
                max_preview = 800
                if img.width > max_preview:
                    ratio = max_preview / img.width
                    img = img.resize((int(img.width * ratio), int(img.height * ratio)))

                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                display(HTML(f'<img src="data:image/png;base64,{img_str}"/>'))
                print(f"Combined size: {combined.shape[1]} x {combined.shape[0]} px")

    def _convert(self, _=None):
        with self.status_output:
            clear_output(wait=True)
            print("Converting to animated WebP...")

            start_frame, end_frame = self.frame_range.value
            rois = [sel.get_roi() for sel in self.selectors]
            combined_frames = []

            for i in range(start_frame, end_frame + 1):
                if (i - start_frame) % self.frame_skip.value != 0:
                    continue

                frames = []
                for j, sel in enumerate(self.selectors):
                    f = self._extract_roi_frame(sel.video, rois[j], i)
                    if f is not None:
                        frames.append(f)

                if len(frames) == len(self.videos):
                    combined = self._combine_frames(frames)
                    combined_frames.append(Image.fromarray(combined))

                if len(combined_frames) % 30 == 0:
                    print(f"Processed {len(combined_frames)} frames...")

            if not combined_frames:
                print("Error: No frames extracted!")
                return

            # Use FPS from first video
            effective_fps = self.videos[0].fps / self.frame_skip.value
            duration_ms = int(1000 / effective_fps)

            self.output_filename = self.output_name.value

            combined_frames[0].save(
                self.output_filename, 'WEBP',
                save_all=True, append_images=combined_frames[1:],
                duration=duration_ms,
                loop=0 if self.loop.value else 1,
                quality=self.quality.value
            )

            file_size = os.path.getsize(self.output_filename) / (1024 * 1024)
            print(f"\nDone! Saved: {self.output_filename}")
            print(f"Frames: {len(combined_frames)}, Size: {file_size:.2f} MB")

    def show(self):
        """Display the converter UI."""
        # ROI selectors side by side
        roi_widgets = [sel.get_widget() for sel in self.selectors]
        roi_box = widgets.HBox(roi_widgets)

        # Initialize previews
        for sel in self.selectors:
            sel._update_preview()

        display(widgets.VBox([
            widgets.HTML('<h3>1. Select ROI for each video</h3>'),
            self.sync_roi,
            roi_box,
            widgets.HTML('<h3>2. Output settings</h3>'),
            self.frame_range,
            self.layout_select,
            self.quality,
            self.frame_skip,
            self.loop,
            self.output_name,
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
