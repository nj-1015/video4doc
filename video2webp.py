"""MP4 to Animated WebP Converter Module"""

import cv2
import numpy as np
from PIL import Image
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import io
import base64
import os


class GDriveFolderPicker:
    """Interactive Google Drive folder browser with create folder capability."""

    def __init__(self, start_path='/content/drive/MyDrive'):
        self.base_path = '/content/drive/MyDrive'
        self.current_path = start_path
        self._mounted = False
        self._create_widgets()

    def _mount_drive(self):
        """Mount Google Drive if not already mounted."""
        if self._mounted:
            return True
        try:
            from google.colab import drive
            if not os.path.exists(self.base_path):
                drive.mount('/content/drive')
            self._mounted = True
            return True
        except Exception as e:
            print(f"Could not mount Google Drive: {e}")
            return False

    def _create_widgets(self):
        self.output = widgets.Output()

        self.path_label = widgets.HTML(
            value=f'<b>Current:</b> {self.current_path}'
        )

        self.folder_list = widgets.Select(
            options=[],
            rows=8,
            description='',
            layout=widgets.Layout(width='100%')
        )

        self.up_btn = widgets.Button(
            description='⬆ Up',
            button_style='info',
            layout=widgets.Layout(width='80px')
        )

        self.open_btn = widgets.Button(
            description='📂 Open',
            button_style='primary',
            layout=widgets.Layout(width='80px')
        )

        self.new_folder_name = widgets.Text(
            placeholder='New folder name',
            layout=widgets.Layout(width='200px')
        )

        self.create_btn = widgets.Button(
            description='➕ Create',
            button_style='success',
            layout=widgets.Layout(width='80px')
        )

        self.refresh_btn = widgets.Button(
            description='🔄',
            layout=widgets.Layout(width='50px')
        )

        self.up_btn.on_click(self._go_up)
        self.open_btn.on_click(self._open_folder)
        self.create_btn.on_click(self._create_folder)
        self.refresh_btn.on_click(self._refresh)
        self.folder_list.observe(self._on_select, names='value')

    def _list_folders(self, path):
        """List folders in the given path."""
        folders = []
        try:
            if os.path.exists(path):
                for item in sorted(os.listdir(path)):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        folders.append(item)
        except PermissionError:
            pass
        return folders

    def _update_list(self):
        """Update the folder list display."""
        folders = self._list_folders(self.current_path)
        self.folder_list.options = folders if folders else ['(no subfolders)']
        self.path_label.value = f'<b>📁 Current:</b> <code>{self.current_path}</code>'

    def _go_up(self, _=None):
        """Navigate to parent folder."""
        if self.current_path != self.base_path:
            self.current_path = os.path.dirname(self.current_path)
            self._update_list()

    def _open_folder(self, _=None):
        """Open selected folder."""
        selected = self.folder_list.value
        if selected and selected != '(no subfolders)':
            self.current_path = os.path.join(self.current_path, selected)
            self._update_list()

    def _on_select(self, change):
        """Handle double-click on folder."""
        pass  # Could add double-click support

    def _create_folder(self, _=None):
        """Create a new folder and navigate into it."""
        name = self.new_folder_name.value.strip()
        if name:
            new_path = os.path.join(self.current_path, name)
            try:
                os.makedirs(new_path, exist_ok=True)
                self.new_folder_name.value = ''
                # Auto-navigate into the new folder
                self.current_path = new_path
                self._update_list()
                with self.output:
                    clear_output(wait=True)
                    print(f"✓ Created and entered: {name}")
            except Exception as e:
                with self.output:
                    clear_output(wait=True)
                    print(f"Error: {e}")

    def _refresh(self, _=None):
        """Refresh folder list."""
        if not self._mounted:
            with self.output:
                clear_output(wait=True)
                print("Mounting Google Drive...")
            self._mount_drive()
        self._update_list()

    def get_path(self):
        """Return the currently selected path."""
        return self.current_path

    def get_widget(self):
        """Return the folder picker widget."""
        return widgets.VBox([
            self.path_label,
            self.folder_list,
            widgets.HBox([self.up_btn, self.open_btn, self.refresh_btn]),
            widgets.HBox([self.new_folder_name, self.create_btn]),
            self.output
        ], layout=widgets.Layout(width='400px', border='1px solid #ccc', padding='10px'))


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
            step=1, description='Every Nth:',
            style=style, layout=layout
        )

        self.loop = widgets.Checkbox(
            value=True, description='Loop Animation', style=style
        )

        self.save_to_gdrive = widgets.Checkbox(
            value=False, description='Save to Google Drive', style=style
        )

        self.gdrive_picker = GDriveFolderPicker()

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

            # Determine output path
            base_name = os.path.splitext(os.path.basename(self.video.filename))[0] + '.webp'
            if self.save_to_gdrive.value:
                gdrive_folder = self.gdrive_picker.get_path()
                self.output_filename = f"{gdrive_folder}/{base_name}"
                print(f"Saving to GDrive: {self.output_filename}")
            else:
                self.output_filename = base_name
                print(f"Saving locally: {self.output_filename}")
                print("(Check 'Save to Google Drive' to save to GDrive folder)")

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
            if self.save_to_gdrive.value:
                print("File saved to Google Drive!")

    def show(self):
        """Display the converter UI."""
        display(widgets.VBox([
            widgets.HTML('<h4>Trim Frames</h4>'),
            self.frame_range,
            widgets.HTML('<h4>Crop Region</h4>'),
            self.crop_x, self.crop_y,
            widgets.HTML('<h4>Output Settings</h4>'),
            self.quality, self.scale, self.frame_skip, self.loop,
            self.save_to_gdrive,
            self.gdrive_picker.get_widget(),
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

        self.caption = widgets.Text(
            value='', placeholder='Enter caption (optional)',
            description='Caption:',
            style=style, layout=layout
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
            self.caption,
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
                     ('Vertical (stacked)', 'vertical'),
                     ('Split Screen (2 videos only)', 'split')],
            value='horizontal',
            description='Layout:',
            style=style
        )

        self.split_position = widgets.IntSlider(
            value=50, min=10, max=90,
            step=5, description='Split %:',
            style=style, layout=layout
        )

        self.split_line = widgets.Checkbox(
            value=True, description='Show split line', style=style
        )

        self.quality = widgets.IntSlider(
            value=70, min=1, max=100,
            step=1, description='Quality (%):',
            style=style, layout=layout
        )

        self.frame_skip = widgets.IntSlider(
            value=1, min=1, max=10,
            step=1, description='Every Nth:',
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

        self.save_to_gdrive = widgets.Checkbox(
            value=False, description='Save to Google Drive', style=style
        )

        self.gdrive_picker = GDriveFolderPicker()

        self.sync_roi = widgets.Checkbox(
            value=False, description='Sync ROI position', style=style
        )

        self.caption_position = widgets.RadioButtons(
            options=[('Top', 'top'), ('Bottom', 'bottom'), ('None', 'none')],
            value='bottom',
            description='Caption:',
            style=style
        )

        self.caption_size = widgets.IntSlider(
            value=48, min=16, max=150,
            step=4, description='Caption Size:',
            style=style, layout=layout
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

    def _add_caption(self, frame, caption):
        """Add caption to a single frame using OpenCV."""
        if not caption or self.caption_position.value == 'none':
            return frame

        font_size = self.caption_size.value
        # OpenCV font scale (roughly: font_size / 30 gives good scaling)
        font_scale = font_size / 25.0
        thickness = max(2, int(font_size / 20))

        # Measure text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), baseline = cv2.getTextSize(caption, font, font_scale, thickness)

        padding = 20
        bar_height = text_h + baseline + padding * 2
        frame_h, frame_w = frame.shape[:2]

        # Create new frame with caption bar
        if self.caption_position.value == 'top':
            new_frame = np.zeros((frame_h + bar_height, frame_w, 3), dtype=np.uint8)
            new_frame[bar_height:, :] = frame
            text_y = padding + text_h
        else:  # bottom
            new_frame = np.zeros((frame_h + bar_height, frame_w, 3), dtype=np.uint8)
            new_frame[:frame_h, :] = frame
            text_y = frame_h + padding + text_h

        # Draw caption centered
        text_x = (frame_w - text_w) // 2
        cv2.putText(new_frame, caption, (text_x, text_y), font, font_scale,
                    (255, 255, 255), thickness, cv2.LINE_AA)

        return new_frame

    def _combine_frames(self, frame_list, captions=None):
        """Combine multiple frames into one."""
        # Add captions to individual frames first (except for split mode)
        if captions and self.layout_select.value != 'split':
            frame_list = [self._add_caption(f, c) for f, c in zip(frame_list, captions)]

        if self.layout_select.value == 'split':
            # Split screen mode (2 videos only)
            if len(frame_list) < 2:
                return frame_list[0] if frame_list else None

            f1, f2 = frame_list[0], frame_list[1]

            # Resize both to same dimensions (use larger of each dimension)
            target_h = max(f1.shape[0], f2.shape[0])
            target_w = max(f1.shape[1], f2.shape[1])

            f1 = cv2.resize(f1, (target_w, target_h))
            f2 = cv2.resize(f2, (target_w, target_h))

            # Calculate split position
            split_x = int(target_w * self.split_position.value / 100)

            # Create combined frame
            combined = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            combined[:, :split_x] = f1[:, :split_x]
            combined[:, split_x:] = f2[:, split_x:]

            # Draw split line
            if self.split_line.value:
                cv2.line(combined, (split_x, 0), (split_x, target_h), (255, 255, 255), 2)

            # Add captions for split mode (overlay on the image)
            if captions:
                font_size = self.caption_size.value
                font_scale = font_size / 25.0
                thickness = max(2, int(font_size / 20))
                font = cv2.FONT_HERSHEY_SIMPLEX

                # Caption 1 on left side
                if captions[0]:
                    (tw, th), _ = cv2.getTextSize(captions[0], font, font_scale, thickness)
                    tx = 10
                    ty = target_h - 20
                    # Draw background
                    cv2.rectangle(combined, (tx - 5, ty - th - 5), (tx + tw + 5, ty + 5), (0, 0, 0), -1)
                    cv2.putText(combined, captions[0], (tx, ty), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

                # Caption 2 on right side
                if len(captions) > 1 and captions[1]:
                    (tw, th), _ = cv2.getTextSize(captions[1], font, font_scale, thickness)
                    tx = target_w - tw - 10
                    ty = target_h - 20
                    cv2.rectangle(combined, (tx - 5, ty - th - 5), (tx + tw + 5, ty + 5), (0, 0, 0), -1)
                    cv2.putText(combined, captions[1], (tx, ty), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

            return combined

        elif self.layout_select.value == 'horizontal':
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
            captions = []
            for sel in self.selectors:
                roi = sel.get_roi()
                f = self._extract_roi_frame(sel.video, roi, frame_num)
                if f is not None:
                    frames.append(f)
                    captions.append(sel.caption.value)

            if len(frames) == len(self.videos):
                combined = self._combine_frames(frames, captions)
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
            captions = [sel.caption.value for sel in self.selectors]
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
                    combined = self._combine_frames(frames, captions)
                    combined_frames.append(Image.fromarray(combined))

                if len(combined_frames) % 30 == 0:
                    print(f"Processed {len(combined_frames)} frames...")

            if not combined_frames:
                print("Error: No frames extracted!")
                return

            # Use FPS from first video
            effective_fps = self.videos[0].fps / self.frame_skip.value
            duration_ms = int(1000 / effective_fps)

            # Determine output path
            if self.save_to_gdrive.value:
                gdrive_folder = self.gdrive_picker.get_path()
                self.output_filename = f"{gdrive_folder}/{self.output_name.value}"
                print(f"Saving to GDrive: {self.output_filename}")
            else:
                self.output_filename = self.output_name.value
                print(f"Saving locally: {self.output_filename}")
                print("(Check 'Save to Google Drive' to save to GDrive folder)")

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
            if self.save_to_gdrive.value:
                print("File saved to Google Drive!")

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
            widgets.HBox([self.split_position, self.split_line]),
            widgets.HBox([self.caption_position, self.caption_size]),
            self.quality,
            self.frame_skip,
            self.loop,
            self.output_name,
            self.save_to_gdrive,
            self.gdrive_picker.get_widget(),
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
