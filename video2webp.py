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

        self.pingpong = widgets.Checkbox(
            value=False, description='Ping-pong (boomerang)', style=style
        )

        self.speed = widgets.FloatSlider(
            value=1.0, min=0.25, max=4.0,
            step=0.25, description='Speed:',
            style=style, layout=layout
        )

        self.max_size = widgets.IntSlider(
            value=0, min=0, max=1920,
            step=100, description='Max Size:',
            style=style, layout=layout
        )  # 0 means no limit

        self.resize_method = widgets.Dropdown(
            options=[('Bilinear (smooth)', cv2.INTER_LINEAR),
                     ('Nearest Neighbor (sharp pixels)', cv2.INTER_NEAREST),
                     ('Bicubic (smoother)', cv2.INTER_CUBIC),
                     ('Area (best for downscale)', cv2.INTER_AREA)],
            value=cv2.INTER_LINEAR,
            description='Resize:',
            style=style, layout=layout
        )

        self.output_format = widgets.RadioButtons(
            options=[('WebP', 'webp'), ('GIF', 'gif')],
            value='webp', description='Format:',
            style=style
        )

        self.border_size = widgets.IntSlider(
            value=0, min=0, max=50,
            step=2, description='Border:',
            style=style, layout=layout
        )

        self.border_color = widgets.ColorPicker(
            value='#000000', description='Border Color:',
            style=style
        )

        self.brightness = widgets.FloatSlider(
            value=1.0, min=0.5, max=2.0,
            step=0.1, description='Brightness:',
            style=style, layout=layout
        )

        self.contrast = widgets.FloatSlider(
            value=1.0, min=0.5, max=2.0,
            step=0.1, description='Contrast:',
            style=style, layout=layout
        )

        self.save_to_gdrive = widgets.Checkbox(
            value=False, description='Save to Google Drive', style=style
        )

        self.gdrive_picker = GDriveFolderPicker()

        self.preview_output = widgets.Output()
        self.preview_btn = widgets.Button(description='Preview Frame', button_style='info')
        self.convert_btn = widgets.Button(description='Convert', button_style='success')
        self.thumbnail_btn = widgets.Button(description='Save Thumbnail', button_style='warning')
        self.status_output = widgets.Output()

    def _setup_preview(self):
        self.preview_btn.on_click(self._show_preview)
        self.convert_btn.on_click(self._convert)
        self.thumbnail_btn.on_click(self._save_thumbnail)

    def _apply_adjustments(self, frame):
        """Apply brightness, contrast, border, and size limit."""
        # Brightness and contrast
        if self.brightness.value != 1.0 or self.contrast.value != 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast.value, beta=(self.brightness.value - 1) * 127)

        # Max size limit
        if self.max_size.value > 0:
            h, w = frame.shape[:2]
            if w > self.max_size.value or h > self.max_size.value:
                ratio = self.max_size.value / max(w, h)
                frame = cv2.resize(frame, (int(w * ratio), int(h * ratio)), interpolation=self.resize_method.value)

        # Border
        if self.border_size.value > 0:
            color_hex = self.border_color.value.lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            frame = cv2.copyMakeBorder(frame,
                self.border_size.value, self.border_size.value,
                self.border_size.value, self.border_size.value,
                cv2.BORDER_CONSTANT, value=color_rgb)

        return frame

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
            frame = cv2.resize(frame, (new_w, new_h), interpolation=self.resize_method.value)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = self._apply_adjustments(frame)
        return frame

    def _save_thumbnail(self, _=None):
        """Save current frame as PNG thumbnail."""
        with self.status_output:
            clear_output(wait=True)
            frame = self._get_frame(self.frame_range.value[0])
            if frame is not None:
                img = Image.fromarray(frame)
                base_name = os.path.splitext(os.path.basename(self.video.filename))[0] + '_thumb.png'
                if self.save_to_gdrive.value:
                    thumb_path = f"{self.gdrive_picker.get_path()}/{base_name}"
                else:
                    thumb_path = base_name
                img.save(thumb_path, 'PNG')
                print(f"Thumbnail saved: {thumb_path}")

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
            fmt = self.output_format.value.upper()
            print(f"Converting to animated {fmt}...")

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

            # Ping-pong: append reversed frames (excluding first and last to avoid stutter)
            if self.pingpong.value and len(frames) > 2:
                frames = frames + frames[-2:0:-1]

            # Calculate duration with speed adjustment
            effective_fps = (self.video.fps / self.frame_skip.value) * self.speed.value
            duration_ms = int(1000 / effective_fps)

            # Determine output path
            ext = self.output_format.value
            base_name = os.path.splitext(os.path.basename(self.video.filename))[0] + f'.{ext}'
            if self.save_to_gdrive.value:
                gdrive_folder = self.gdrive_picker.get_path()
                self.output_filename = f"{gdrive_folder}/{base_name}"
                print(f"Saving to GDrive: {self.output_filename}")
            else:
                self.output_filename = base_name
                print(f"Saving locally: {self.output_filename}")

            # Save animation
            if self.output_format.value == 'gif':
                frames[0].save(
                    self.output_filename, 'GIF',
                    save_all=True, append_images=frames[1:],
                    duration=duration_ms,
                    loop=0 if self.loop.value else 1
                )
            else:
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
            widgets.HTML('<h4>Adjustments</h4>'),
            widgets.HBox([self.brightness, self.contrast]),
            widgets.HBox([self.border_size, self.border_color]),
            widgets.HTML('<h4>Output Settings</h4>'),
            widgets.HBox([self.output_format, self.quality]),
            widgets.HBox([self.scale, self.max_size]),
            self.resize_method,
            self.frame_skip,
            widgets.HBox([self.speed, self.loop, self.pingpong]),
            self.save_to_gdrive,
            self.gdrive_picker.get_widget(),
            widgets.HBox([self.preview_btn, self.convert_btn, self.thumbnail_btn]),
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

    def __init__(self, video_info, index=0, reference_size=None, on_roi_change=None):
        """
        Args:
            video_info: VideoInfo object
            index: Video index for display
            reference_size: Optional (width, height) tuple for normalized coordinates.
                           If provided, ROI selection works in reference coordinates
                           and is scaled to actual video coordinates when extracting frames.
            on_roi_change: Optional callback(index, roi_x, roi_y) called when ROI changes via drag.
        """
        self.video = video_info
        self.index = index
        self.preview_scale = 1.0  # Track scale for coordinate conversion
        self.on_roi_change = on_roi_change  # Callback for ROI sync

        # Reference size for normalized ROI coordinates
        if reference_size:
            self.ref_width, self.ref_height = reference_size
            self.scale_x = self.video.width / self.ref_width
            self.scale_y = self.video.height / self.ref_height
            self.is_scaled = (self.video.width != self.ref_width or
                             self.video.height != self.ref_height)
        else:
            self.ref_width, self.ref_height = self.video.width, self.video.height
            self.scale_x = self.scale_y = 1.0
            self.is_scaled = False

        self._create_widgets()

    def _create_widgets(self):
        style = {'description_width': '80px'}
        layout = widgets.Layout(width='400px')

        # Use reference dimensions for sliders (enables sync across different resolutions)
        self.roi_x = widgets.IntRangeSlider(
            value=[0, self.ref_width],
            min=0, max=self.ref_width,
            step=1, description='ROI X:',
            style=style, layout=layout, continuous_update=False
        )

        self.roi_y = widgets.IntRangeSlider(
            value=[0, self.ref_height],
            min=0, max=self.ref_height,
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

        # Hidden widget for receiving coordinates from JavaScript
        self._roi_coords = widgets.Text(value='', layout=widgets.Layout(display='none'))
        self._roi_coords.observe(self._on_roi_drag, names='value')

        self.preview_output = widgets.Output()

        # Link preview updates
        self.roi_x.observe(self._update_preview, names='value')
        self.roi_y.observe(self._update_preview, names='value')
        self.preview_frame.observe(self._update_preview, names='value')

    def _on_roi_drag(self, change):
        """Handle ROI coordinates from JavaScript drag selection."""
        if not change['new']:
            return
        try:
            coords = change['new'].split(',')
            if len(coords) == 4:
                x1, y1, x2, y2 = [int(float(c)) for c in coords]
                # Convert from preview coordinates to reference coordinates
                scale = self.preview_scale
                if scale > 0:
                    x1 = int(x1 / scale)
                    y1 = int(y1 / scale)
                    x2 = int(x2 / scale)
                    y2 = int(y2 / scale)
                # Clamp to reference dimensions (sliders use reference coords)
                x1 = max(0, min(x1, self.ref_width))
                x2 = max(0, min(x2, self.ref_width))
                y1 = max(0, min(y1, self.ref_height))
                y2 = max(0, min(y2, self.ref_height))
                # Ensure x1 < x2 and y1 < y2
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                # Update sliders (this will trigger preview update)
                self.roi_x.value = (x1, x2)
                self.roi_y.value = (y1, y2)
                # Notify callback for ROI sync with other videos
                if self.on_roi_change:
                    self.on_roi_change(self.index, (x1, x2), (y1, y2))
        except (ValueError, IndexError):
            pass

    def _handle_roi_from_js(self, coord_str):
        """Handle ROI coordinates from JavaScript via Colab callback."""
        try:
            coords = coord_str.split(',')
            if len(coords) == 4:
                x1, y1, x2, y2 = [int(float(c)) for c in coords]
                # Convert from preview coordinates to reference coordinates
                scale = self.preview_scale
                if scale > 0:
                    x1 = int(x1 / scale)
                    y1 = int(y1 / scale)
                    x2 = int(x2 / scale)
                    y2 = int(y2 / scale)
                # Clamp to reference dimensions
                x1 = max(0, min(x1, self.ref_width))
                x2 = max(0, min(x2, self.ref_width))
                y1 = max(0, min(y1, self.ref_height))
                y2 = max(0, min(y2, self.ref_height))
                # Ensure x1 < x2 and y1 < y2
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                # Update sliders
                self.roi_x.value = (x1, x2)
                self.roi_y.value = (y1, y2)
                # Notify callback for ROI sync with other videos
                if self.on_roi_change:
                    self.on_roi_change(self.index, (x1, x2), (y1, y2))
        except (ValueError, IndexError):
            pass

    def _get_frame_for_preview(self):
        """Get frame for preview scaled to reference size."""
        cap = cv2.VideoCapture(self.video.filename)
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_frame.value)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None, 1.0

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # First, scale to reference size if needed (for resolution alignment)
        h, w = frame_rgb.shape[:2]
        if w != self.ref_width or h != self.ref_height:
            frame_rgb = cv2.resize(frame_rgb, (self.ref_width, self.ref_height),
                                   interpolation=cv2.INTER_NEAREST)

        # Then scale down for preview display if too large
        max_preview = 400
        h, w = frame_rgb.shape[:2]  # Now in reference dimensions
        if w > max_preview or h > max_preview:
            scale = max_preview / max(w, h)
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)))
        else:
            scale = 1.0

        return frame_rgb, scale

    def _update_preview(self, _=None):
        with self.preview_output:
            clear_output(wait=True)
            frame, scale = self._get_frame_for_preview()
            if frame is not None:
                self.preview_scale = scale
                h, w = frame.shape[:2]

                # Convert current ROI to preview coordinates
                x1, x2 = self.roi_x.value
                y1, y2 = self.roi_y.value
                px1, py1 = int(x1 * scale), int(y1 * scale)
                px2, py2 = int(x2 * scale), int(y2 * scale)

                img = Image.fromarray(frame)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()

                # Unique ID for this selector
                uid = f"roi_canvas_{self.index}"

                # Register Colab callback for receiving ROI coordinates from JavaScript
                callback_name = f"roi_callback_{self.index}"
                try:
                    from google.colab import output
                    output.register_callback(callback_name, self._handle_roi_from_js)
                except ImportError:
                    pass  # Not in Colab

                html_content = f'''
                <div style="position:relative;display:inline-block;cursor:crosshair;" id="{uid}_container">
                    <img id="{uid}_img" src="data:image/png;base64,{img_str}" style="display:block;"/>
                    <canvas id="{uid}" width="{w}" height="{h}" style="position:absolute;top:0;left:0;"></canvas>
                </div>
                <div id="{uid}_info" style="font-family:monospace;margin-top:4px;">ROI: {x2-x1} x {y2-y1} px (drag to select)</div>
                <script>
                (function() {{
                    var canvas = document.getElementById("{uid}");
                    var ctx = canvas.getContext("2d");
                    var container = document.getElementById("{uid}_container");
                    var info = document.getElementById("{uid}_info");
                    var drawing = false;
                    var startX, startY, endX, endY;

                    // Current ROI
                    var roiX1 = {px1}, roiY1 = {py1}, roiX2 = {px2}, roiY2 = {py2};

                    function sendToPython(coordStr) {{
                        // Use Colab's callback mechanism
                        if (typeof google !== 'undefined' && google.colab) {{
                            google.colab.kernel.invokeFunction('{callback_name}', [coordStr], {{}});
                        }}
                    }}

                    function drawROI() {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        // Dim area outside ROI
                        ctx.fillStyle = "rgba(0,0,0,0.4)";
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        // Clear the ROI area (make it visible)
                        ctx.clearRect(roiX1, roiY1, roiX2 - roiX1, roiY2 - roiY1);
                        // Draw ROI border
                        ctx.strokeStyle = "#00ff00";
                        ctx.lineWidth = 3;
                        ctx.setLineDash([]);
                        ctx.strokeRect(roiX1, roiY1, roiX2 - roiX1, roiY2 - roiY1);
                    }}

                    function drawSelection(x1, y1, x2, y2) {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        // Dim area outside selection
                        ctx.fillStyle = "rgba(0,0,0,0.4)";
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        // Clear the selection area
                        ctx.clearRect(x1, y1, x2 - x1, y2 - y1);
                        // Draw selection border
                        ctx.strokeStyle = "#ff0000";
                        ctx.lineWidth = 3;
                        ctx.setLineDash([5, 5]);
                        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                        ctx.setLineDash([]);
                    }}

                    function getPos(e) {{
                        var rect = canvas.getBoundingClientRect();
                        var x, y;
                        if (e.touches) {{
                            x = e.touches[0].clientX - rect.left;
                            y = e.touches[0].clientY - rect.top;
                        }} else {{
                            x = e.clientX - rect.left;
                            y = e.clientY - rect.top;
                        }}
                        return {{x: Math.max(0, Math.min(x, canvas.width)), y: Math.max(0, Math.min(y, canvas.height))}};
                    }}

                    function onStart(e) {{
                        e.preventDefault();
                        drawing = true;
                        var pos = getPos(e);
                        startX = pos.x;
                        startY = pos.y;
                    }}

                    function onMove(e) {{
                        if (!drawing) return;
                        e.preventDefault();
                        var pos = getPos(e);
                        endX = pos.x;
                        endY = pos.y;
                        var x1 = Math.min(startX, endX), y1 = Math.min(startY, endY);
                        var x2 = Math.max(startX, endX), y2 = Math.max(startY, endY);
                        drawSelection(x1, y1, x2, y2);
                        var w = Math.abs(x2 - x1) / {scale};
                        var h = Math.abs(y2 - y1) / {scale};
                        info.textContent = "Selecting: " + Math.round(w) + " x " + Math.round(h) + " px";
                    }}

                    function onEnd(e) {{
                        if (!drawing) return;
                        drawing = false;
                        var x1 = Math.min(startX, endX), y1 = Math.min(startY, endY);
                        var x2 = Math.max(startX, endX), y2 = Math.max(startY, endY);
                        if (Math.abs(x2 - x1) > 5 && Math.abs(y2 - y1) > 5) {{
                            roiX1 = x1; roiY1 = y1; roiX2 = x2; roiY2 = y2;
                            // Send coordinates to Python via Colab callback
                            var coordStr = x1 + "," + y1 + "," + x2 + "," + y2;
                            sendToPython(coordStr);
                            info.textContent = "ROI updated: " + Math.round((x2-x1)/{scale}) + " x " + Math.round((y2-y1)/{scale}) + " px";
                        }}
                        drawROI();
                    }}

                    canvas.addEventListener("mousedown", onStart);
                    canvas.addEventListener("mousemove", onMove);
                    canvas.addEventListener("mouseup", onEnd);
                    canvas.addEventListener("mouseleave", onEnd);
                    canvas.addEventListener("touchstart", onStart);
                    canvas.addEventListener("touchmove", onMove);
                    canvas.addEventListener("touchend", onEnd);

                    drawROI();
                }})();
                </script>
                '''
                display(HTML(html_content))

    def get_roi(self):
        """Return current ROI as (x1, y1, x2, y2) in actual video coordinates."""
        # Convert from reference coordinates to actual video coordinates
        x1 = int(self.roi_x.value[0] * self.scale_x)
        y1 = int(self.roi_y.value[0] * self.scale_y)
        x2 = int(self.roi_x.value[1] * self.scale_x)
        y2 = int(self.roi_y.value[1] * self.scale_y)
        # Clamp to actual video dimensions
        x1 = max(0, min(x1, self.video.width))
        x2 = max(0, min(x2, self.video.width))
        y1 = max(0, min(y1, self.video.height))
        y2 = max(0, min(y2, self.video.height))
        return (x1, y1, x2, y2)

    def get_widget(self):
        """Return widget for display."""
        # Show scale info if video was rescaled for alignment
        if self.is_scaled:
            scale_info = f'<br><span style="color:#ff9800;">⚠ Scaled to {self.ref_width}x{self.ref_height} for ROI sync</span>'
        else:
            scale_info = ''

        return widgets.VBox([
            widgets.HTML(f'<b>Video {self.index + 1}: {os.path.basename(self.video.filename)}</b>'),
            widgets.HTML(f'<small>{self.video.width}x{self.video.height}, {self.video.total_frames} frames{scale_info}</small>'),
            self.caption,
            self.preview_frame,
            self.roi_x,
            self.roi_y,
            self._roi_coords,  # Hidden widget for JS communication
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
        self._syncing = False  # Flag to prevent recursive sync

        # Calculate reference size (max dimensions) for ROI alignment
        ref_width = max(v.width for v in video_list)
        ref_height = max(v.height for v in video_list)
        self.reference_size = (ref_width, ref_height)

        # Create selectors with reference size and sync callback
        self.selectors = [VideoROISelector(v, i,
                                           reference_size=self.reference_size,
                                           on_roi_change=self._on_selector_roi_change)
                         for i, v in enumerate(video_list)]
        self._create_widgets()
        self._setup_roi_sync()

    def _on_selector_roi_change(self, source_idx, roi_x, roi_y):
        """Handle ROI change from drag selection - sync to other selectors."""
        if not self.sync_roi.value or self._syncing:
            return
        self._syncing = True
        try:
            for i, sel in enumerate(self.selectors):
                if i != source_idx:
                    sel.roi_x.value = roi_x
                    sel.roi_y.value = roi_y
                    # Update the canvas ROI via JavaScript (more reliable in Colab)
                    scale = sel.preview_scale
                    px1, py1 = int(roi_x[0] * scale), int(roi_y[0] * scale)
                    px2, py2 = int(roi_x[1] * scale), int(roi_y[1] * scale)
                    uid = f"roi_canvas_{i}"
                    js_code = f'''
                    (function() {{
                        var canvas = document.getElementById("{uid}");
                        if (canvas) {{
                            var ctx = canvas.getContext("2d");
                            var w = canvas.width, h = canvas.height;
                            var x1 = {px1}, y1 = {py1}, x2 = {px2}, y2 = {py2};
                            // Clear and dim outside ROI
                            ctx.clearRect(0, 0, w, h);
                            ctx.fillStyle = "rgba(0,0,0,0.4)";
                            ctx.fillRect(0, 0, w, h);
                            ctx.clearRect(x1, y1, x2 - x1, y2 - y1);
                            // Draw ROI border
                            ctx.strokeStyle = "#00ff00";
                            ctx.lineWidth = 3;
                            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                        }}
                        var info = document.getElementById("{uid}_info");
                        if (info) {{
                            info.textContent = "ROI: {roi_x[1] - roi_x[0]} x {roi_y[1] - roi_y[0]} px (drag to select)";
                        }}
                    }})();
                    '''
                    try:
                        from google.colab import output
                        output.eval_js(js_code)
                    except ImportError:
                        from IPython.display import display, Javascript
                        display(Javascript(js_code))
        finally:
            self._syncing = False

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

        self.pingpong = widgets.Checkbox(
            value=False, description='Ping-pong', style=style
        )

        self.speed = widgets.FloatSlider(
            value=1.0, min=0.25, max=4.0,
            step=0.25, description='Speed:',
            style=style, layout=layout
        )

        self.max_size = widgets.IntSlider(
            value=0, min=0, max=1920,
            step=100, description='Max Size:',
            style=style, layout=layout
        )

        self.resize_method = widgets.Dropdown(
            options=[('Bilinear (smooth)', cv2.INTER_LINEAR),
                     ('Nearest Neighbor (sharp pixels)', cv2.INTER_NEAREST),
                     ('Bicubic (smoother)', cv2.INTER_CUBIC),
                     ('Area (best for downscale)', cv2.INTER_AREA)],
            value=cv2.INTER_LINEAR,
            description='Resize:',
            style=style, layout=layout
        )

        self.output_format = widgets.RadioButtons(
            options=[('WebP', 'webp'), ('GIF', 'gif')],
            value='webp', description='Format:',
            style=style
        )

        self.border_size = widgets.IntSlider(
            value=0, min=0, max=50,
            step=2, description='Border:',
            style=style, layout=layout
        )

        self.border_color = widgets.ColorPicker(
            value='#000000', description='Border Color:',
            style=style
        )

        self.brightness = widgets.FloatSlider(
            value=1.0, min=0.5, max=2.0,
            step=0.1, description='Brightness:',
            style=style, layout=layout
        )

        self.contrast = widgets.FloatSlider(
            value=1.0, min=0.5, max=2.0,
            step=0.1, description='Contrast:',
            style=style, layout=layout
        )

        self.transition = widgets.Dropdown(
            options=[('None', 'none'), ('Fade', 'fade'), ('Wipe Left', 'wipe_left'), ('Wipe Right', 'wipe_right')],
            value='none', description='Transition:',
            style=style, layout=layout
        )

        self.output_name = widgets.Text(
            value='output',
            description='Output Name:',
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

        self.preview_btn = widgets.Button(description='Preview', button_style='info')
        self.convert_btn = widgets.Button(description='Convert', button_style='success')
        self.thumbnail_btn = widgets.Button(description='Thumbnail', button_style='warning')
        self.comparison_btn = widgets.Button(description='Interactive HTML', button_style='')
        self.preview_output = widgets.Output()
        self.status_output = widgets.Output()

        self.preview_btn.on_click(self._show_preview)
        self.convert_btn.on_click(self._convert)
        self.thumbnail_btn.on_click(self._save_thumbnail)
        self.comparison_btn.on_click(self._create_interactive_html)

    def _apply_adjustments(self, frame):
        """Apply brightness, contrast, border, and size limit."""
        if self.brightness.value != 1.0 or self.contrast.value != 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast.value, beta=(self.brightness.value - 1) * 127)

        if self.max_size.value > 0:
            h, w = frame.shape[:2]
            if w > self.max_size.value or h > self.max_size.value:
                ratio = self.max_size.value / max(w, h)
                frame = cv2.resize(frame, (int(w * ratio), int(h * ratio)), interpolation=self.resize_method.value)

        if self.border_size.value > 0:
            color_hex = self.border_color.value.lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            frame = cv2.copyMakeBorder(frame,
                self.border_size.value, self.border_size.value,
                self.border_size.value, self.border_size.value,
                cv2.BORDER_CONSTANT, value=color_rgb)
        return frame

    def _save_thumbnail(self, _=None):
        """Save first combined frame as PNG thumbnail."""
        with self.status_output:
            clear_output(wait=True)
            frame_num = self.frame_range.value[0]
            frames = []
            captions = [sel.caption.value for sel in self.selectors]
            for sel in self.selectors:
                roi = sel.get_roi()
                f = self._extract_roi_frame(sel.video, roi, frame_num)
                if f is not None:
                    frames.append(f)
            if len(frames) == len(self.videos):
                combined = self._combine_frames(frames, captions)
                combined = self._apply_adjustments(combined)
                img = Image.fromarray(combined)
                thumb_name = f"{self.output_name.value}_thumb.png"
                if self.save_to_gdrive.value:
                    thumb_path = f"{self.gdrive_picker.get_path()}/{thumb_name}"
                else:
                    thumb_path = thumb_name
                img.save(thumb_path, 'PNG')
                print(f"Thumbnail saved: {thumb_path}")

    def _create_interactive_html(self, _=None):
        """Create interactive HTML comparison slider with animated WebP (for 2 videos)."""
        with self.status_output:
            clear_output(wait=True)
            if len(self.videos) != 2:
                print("Interactive HTML requires exactly 2 videos")
                return

            print("Generating animated comparison...")

            start_frame, end_frame = self.frame_range.value
            rois = [sel.get_roi() for sel in self.selectors]

            # Collect frames for both videos
            frames_1, frames_2 = [], []

            for i in range(start_frame, end_frame + 1):
                if (i - start_frame) % self.frame_skip.value != 0:
                    continue

                f1 = self._extract_roi_frame(self.selectors[0].video, rois[0], i)
                f2 = self._extract_roi_frame(self.selectors[1].video, rois[1], i)

                if f1 is not None and f2 is not None:
                    frames_1.append(f1)
                    frames_2.append(f2)

                if len(frames_1) % 20 == 0:
                    print(f"Processed {len(frames_1)} frames...")

            if not frames_1 or not frames_2:
                print("Could not extract frames")
                return

            # Resize all frames to same dimensions
            h = max(max(f.shape[0] for f in frames_1), max(f.shape[0] for f in frames_2))
            w = max(max(f.shape[1] for f in frames_1), max(f.shape[1] for f in frames_2))

            interp = self.resize_method.value
            frames_1 = [cv2.resize(f, (w, h), interpolation=interp) for f in frames_1]
            frames_2 = [cv2.resize(f, (w, h), interpolation=interp) for f in frames_2]

            # Apply adjustments
            frames_1 = [self._apply_adjustments(f) for f in frames_1]
            frames_2 = [self._apply_adjustments(f) for f in frames_2]

            # Ping-pong
            if self.pingpong.value and len(frames_1) > 2:
                frames_1 = frames_1 + frames_1[-2:0:-1]
                frames_2 = frames_2 + frames_2[-2:0:-1]

            # Calculate duration
            effective_fps = (self.videos[0].fps / self.frame_skip.value) * self.speed.value
            duration_ms = int(1000 / effective_fps)

            # Convert to PIL and save as WebP
            pil_1 = [Image.fromarray(f) for f in frames_1]
            pil_2 = [Image.fromarray(f) for f in frames_2]

            buf1, buf2 = io.BytesIO(), io.BytesIO()
            pil_1[0].save(buf1, 'WEBP', save_all=True, append_images=pil_1[1:],
                         duration=duration_ms, loop=0, quality=self.quality.value)
            pil_2[0].save(buf2, 'WEBP', save_all=True, append_images=pil_2[1:],
                         duration=duration_ms, loop=0, quality=self.quality.value)

            b64_1 = base64.b64encode(buf1.getvalue()).decode()
            b64_2 = base64.b64encode(buf2.getvalue()).decode()

            captions = [sel.caption.value for sel in self.selectors]
            cap1 = captions[0] if captions[0] else 'Before'
            cap2 = captions[1] if len(captions) > 1 and captions[1] else 'After'

            html_content = f'''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparison: {cap1} vs {cap2}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
.comparison-container {{ position: relative; width: {w}px; max-width: 100%; overflow: hidden; cursor: ew-resize; }}
.comparison-container img {{ display: block; width: {w}px; height: {h}px; pointer-events: none; }}
.img-background {{ position: relative; }}
.img-overlay {{ position: absolute; top: 0; left: 0; width: 50%; height: 100%; overflow: hidden; }}
.img-overlay img {{ position: absolute; top: 0; left: 0; }}
.slider {{ position: absolute; top: 0; left: 50%; width: 4px; height: 100%; background: #fff; transform: translateX(-50%); pointer-events: none; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
.slider::before, .slider::after {{ content: ""; position: absolute; left: 50%; width: 0; height: 0; border: 8px solid transparent; transform: translateX(-50%); }}
.slider::before {{ top: 50%; margin-top: -20px; border-bottom: 12px solid #fff; border-top: none; }}
.slider::after {{ top: 50%; margin-top: 8px; border-top: 12px solid #fff; border-bottom: none; }}
.label {{ position: absolute; bottom: 15px; padding: 8px 16px; background: rgba(0,0,0,0.8); color: #fff; font-size: 14px; font-weight: 500; border-radius: 4px; }}
.label-left {{ left: 15px; }}
.label-right {{ right: 15px; }}
.instructions {{ position: absolute; top: 15px; left: 50%; transform: translateX(-50%); padding: 8px 16px; background: rgba(0,0,0,0.8); color: #fff; font-size: 12px; border-radius: 4px; opacity: 0.8; }}
</style>
</head>
<body>
<div class="comparison-container" id="container">
  <div class="img-background">
    <img src="data:image/webp;base64,{b64_2}" alt="{cap2}">
  </div>
  <div class="img-overlay" id="overlay">
    <img src="data:image/webp;base64,{b64_1}" alt="{cap1}">
  </div>
  <div class="slider" id="slider"></div>
  <span class="label label-left">{cap1}</span>
  <span class="label label-right">{cap2}</span>
  <span class="instructions">Drag to compare</span>
</div>
<script>
const container = document.getElementById("container");
const overlay = document.getElementById("overlay");
const slider = document.getElementById("slider");
let isDragging = false;

function updatePosition(x) {{
  const rect = container.getBoundingClientRect();
  let pos = (x - rect.left) / rect.width;
  pos = Math.max(0, Math.min(1, pos));
  const pct = pos * 100;
  overlay.style.width = pct + "%";
  slider.style.left = pct + "%";
}}

container.addEventListener("mousedown", (e) => {{
  isDragging = true;
  updatePosition(e.clientX);
}});

document.addEventListener("mouseup", () => isDragging = false);

document.addEventListener("mousemove", (e) => {{
  if (isDragging) updatePosition(e.clientX);
}});

// Touch support
container.addEventListener("touchstart", (e) => {{
  isDragging = true;
  updatePosition(e.touches[0].clientX);
}});

document.addEventListener("touchend", () => isDragging = false);

document.addEventListener("touchmove", (e) => {{
  if (isDragging) {{
    e.preventDefault();
    updatePosition(e.touches[0].clientX);
  }}
}});
</script>
</body></html>'''

            html_name = f"{self.output_name.value}_comparison.html"
            if self.save_to_gdrive.value:
                html_path = f"{self.gdrive_picker.get_path()}/{html_name}"
            else:
                html_path = html_name

            with open(html_path, 'w') as f:
                f.write(html_content)
            print(f"Interactive HTML saved: {html_path}")
            print("Open in browser to use the draggable comparison slider")

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
                            # All sliders use reference dimensions, so direct copy works
                            slider.value = change['new']
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

            f1 = cv2.resize(f1, (target_w, target_h), interpolation=self.resize_method.value)
            f2 = cv2.resize(f2, (target_w, target_h), interpolation=self.resize_method.value)

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
                    f = cv2.resize(f, (new_w, max_h), interpolation=self.resize_method.value)
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
                    f = cv2.resize(f, (max_w, new_h), interpolation=self.resize_method.value)
                resized.append(f)
            return np.vstack(resized)

    def _show_preview(self, _=None):
        with self.preview_output:
            clear_output(wait=True)
            print("Generating animated preview...")

            start_frame, end_frame = self.frame_range.value
            rois = [sel.get_roi() for sel in self.selectors]
            captions = [sel.caption.value for sel in self.selectors]

            # Limit preview to ~3 seconds or 60 frames max
            fps = self.videos[0].fps
            max_preview_frames = min(60, int(fps * 3))
            preview_skip = max(1, (end_frame - start_frame) // max_preview_frames)

            preview_frames = []
            frame_count = 0

            for i in range(start_frame, end_frame + 1):
                if (i - start_frame) % (self.frame_skip.value * preview_skip) != 0:
                    continue

                frames = []
                for j, sel in enumerate(self.selectors):
                    f = self._extract_roi_frame(sel.video, rois[j], i)
                    if f is not None:
                        frames.append(f)

                if len(frames) == len(self.videos):
                    combined = self._combine_frames(frames, captions)
                    img = Image.fromarray(combined)

                    # Scale for preview
                    max_preview_size = 600
                    if img.width > max_preview_size or img.height > max_preview_size:
                        ratio = max_preview_size / max(img.width, img.height)
                        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

                    preview_frames.append(img)
                    frame_count += 1

                    if frame_count >= max_preview_frames:
                        break

            if preview_frames:
                # Create animated preview
                effective_fps = fps / self.frame_skip.value
                duration_ms = int(1000 / effective_fps * preview_skip)

                buffer = io.BytesIO()
                preview_frames[0].save(
                    buffer, format='GIF',
                    save_all=True,
                    append_images=preview_frames[1:],
                    duration=duration_ms,
                    loop=0
                )
                img_str = base64.b64encode(buffer.getvalue()).decode()
                display(HTML(f'<img src="data:image/gif;base64,{img_str}"/>'))
                print(f"Preview: {len(preview_frames)} frames, Size: {preview_frames[0].width}x{preview_frames[0].height} px")
            else:
                print("No frames to preview")

    def _convert(self, _=None):
        with self.status_output:
            clear_output(wait=True)
            fmt = self.output_format.value.upper()
            print(f"Converting to animated {fmt}...")

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
                    combined = self._apply_adjustments(combined)
                    combined_frames.append(Image.fromarray(combined))

                if len(combined_frames) % 30 == 0:
                    print(f"Processed {len(combined_frames)} frames...")

            if not combined_frames:
                print("Error: No frames extracted!")
                return

            # Ping-pong: append reversed frames
            if self.pingpong.value and len(combined_frames) > 2:
                combined_frames = combined_frames + combined_frames[-2:0:-1]

            # Use FPS from first video with speed adjustment
            effective_fps = (self.videos[0].fps / self.frame_skip.value) * self.speed.value
            duration_ms = int(1000 / effective_fps)

            # Determine output path
            ext = self.output_format.value
            output_name = f"{self.output_name.value}.{ext}"
            if self.save_to_gdrive.value:
                gdrive_folder = self.gdrive_picker.get_path()
                self.output_filename = f"{gdrive_folder}/{output_name}"
                print(f"Saving to GDrive: {self.output_filename}")
            else:
                self.output_filename = output_name
                print(f"Saving locally: {self.output_filename}")

            # Save animation
            if self.output_format.value == 'gif':
                combined_frames[0].save(
                    self.output_filename, 'GIF',
                    save_all=True, append_images=combined_frames[1:],
                    duration=duration_ms,
                    loop=0 if self.loop.value else 1
                )
            else:
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
            widgets.HTML('<h3>2. Layout</h3>'),
            self.frame_range,
            self.layout_select,
            widgets.HBox([self.split_position, self.split_line]),
            widgets.HBox([self.caption_position, self.caption_size]),
            widgets.HTML('<h3>3. Adjustments</h3>'),
            widgets.HBox([self.brightness, self.contrast]),
            widgets.HBox([self.border_size, self.border_color]),
            self.resize_method,
            widgets.HTML('<h3>4. Output</h3>'),
            widgets.HBox([self.output_format, self.quality]),
            widgets.HBox([self.max_size, self.speed]),
            self.frame_skip,
            widgets.HBox([self.loop, self.pingpong]),
            self.output_name,
            self.save_to_gdrive,
            self.gdrive_picker.get_widget(),
            widgets.HBox([self.preview_btn, self.convert_btn, self.thumbnail_btn, self.comparison_btn]),
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
