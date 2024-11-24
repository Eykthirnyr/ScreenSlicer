import sys
import subprocess
import webbrowser

# Check and install required modules
required_modules = {
    'PyQt5': 'PyQt5',
    'PIL': 'Pillow',
    'screeninfo': 'screeninfo'  # For getting display info from Windows
}

for module, pip_name in required_modules.items():
    try:
        __import__(module)
    except ImportError:
        print(f"Module {module} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QDialog, QComboBox, QWidget,
                             QFileDialog, QScrollArea, QToolTip)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QRegion, QFont
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PIL import Image
import math
import platform

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None  # In case screeninfo is not available

class ScreenConfigDialog(QDialog):
    def __init__(self, existing_screens=None):
        super().__init__()
        self.screen_entries = []
        self.initUI(existing_screens)

    def initUI(self, existing_screens):
        self.setWindowTitle('Screen Configuration')
        self.setFixedWidth(650)  # Set default width to 650px
        layout = QVBoxLayout()

        instruction_label = QLabel('Enter resolution, diagonal size (in cm), and select aspect ratio for each screen:')
        layout.addWidget(instruction_label)

        # Scroll area to accommodate multiple screens
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.screen_list_layout = QVBoxLayout()
        scroll_widget.setLayout(self.screen_list_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # If there are existing screens, populate them
        if existing_screens:
            for screen in existing_screens:
                self.addScreenEntry(screen)
        else:
            self.addScreenEntry()

        # Button to add screens
        buttons_layout = QHBoxLayout()
        self.add_screen_btn = QPushButton('Add Screen')
        self.add_screen_btn.clicked.connect(self.addScreenEntry)
        buttons_layout.addWidget(self.add_screen_btn)
        layout.addLayout(buttons_layout)

        # OK and Cancel buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def addScreenEntry(self, screen_data=None):
        group_box = QWidget()
        group_layout = QHBoxLayout()

        res_label = QLabel('Resolution (W x H):')
        res_width = QLineEdit()
        res_width.setPlaceholderText('Width in pixels')
        res_height = QLineEdit()
        res_height.setPlaceholderText('Height in pixels')

        diag_label = QLabel('Diagonal (cm):')
        diag_entry = QLineEdit()
        diag_entry.setPlaceholderText('Size in cm')

        ratio_label = QLabel('Aspect Ratio:')
        ratio_combo = QComboBox()
        ratio_combo.addItems(['16:9', '16:10', '4:3', '21:9', '5:4', '32:9', '1:1', '9:16', '3:2'])

        # Remove button for this screen
        remove_btn = QPushButton('Remove')
        remove_btn.clicked.connect(lambda: self.removeScreenEntry(group_box))

        group_layout.addWidget(res_label)
        group_layout.addWidget(res_width)
        group_layout.addWidget(res_height)
        group_layout.addWidget(diag_label)
        group_layout.addWidget(diag_entry)
        group_layout.addWidget(ratio_label)
        group_layout.addWidget(ratio_combo)
        group_layout.addWidget(remove_btn)

        group_box.setLayout(group_layout)
        self.screen_list_layout.addWidget(group_box)

        entry = {
            'group_box': group_box,
            'res_width': res_width,
            'res_height': res_height,
            'diag': diag_entry,
            'ratio_combo': ratio_combo
        }
        self.screen_entries.append(entry)

        if screen_data:
            res_width.setText(str(screen_data['res_width']))
            res_height.setText(str(screen_data['res_height']))
            diag_entry.setText(str(screen_data['diag']))
            ratio_str = f"{screen_data['ratio_w']}:{screen_data['ratio_h']}"
            index = ratio_combo.findText(ratio_str)
            if index != -1:
                ratio_combo.setCurrentIndex(index)
            else:
                ratio_combo.addItem(ratio_str)
                ratio_combo.setCurrentIndex(ratio_combo.count() -1)

    def removeScreenEntry(self, group_box):
        for entry in self.screen_entries:
            if entry['group_box'] == group_box:
                self.screen_entries.remove(entry)
                entry['group_box'].deleteLater()
                break

    def getValues(self):
        self.screen_resolutions = []
        self.screen_diagonals = []
        self.screen_aspect_ratios = []
        for entry in self.screen_entries:
            try:
                width = int(entry['res_width'].text())
                height = int(entry['res_height'].text())
                diag = float(entry['diag'].text())
                ratio_str = entry['ratio_combo'].currentText()
                ratio_parts = ratio_str.split(':')
                ratio_w = int(ratio_parts[0])
                ratio_h = int(ratio_parts[1])
                self.screen_resolutions.append((width, height))
                self.screen_diagonals.append(diag)
                self.screen_aspect_ratios.append((ratio_w, ratio_h))
            except ValueError:
                QMessageBox.warning(self, 'Input Error', 'Please enter valid numerical values.')
                return False
        if not self.screen_entries:
            QMessageBox.warning(self, 'No Screens', 'Please add at least one screen.')
            return False
        return True

class PreviewWidget(QWidget):
    def __init__(self, screen_arrangement, screen_resolutions, screen_physical_sizes):
        super().__init__()
        self.screen_arrangement = screen_arrangement  # List of screen positions and sizes
        self.screen_resolutions = screen_resolutions
        self.screen_physical_sizes = screen_physical_sizes
        self.image = None
        self.original_image = None
        self.image_position = QPoint(0, 0)
        self.dragging_image = False
        self.dragging_screen = False
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.screens_defined = False
        self.image_loaded = False
        self.image_scale = 1.0  # Added for image scaling
        self.initUI()

    def initUI(self):
        self.setMinimumSize(800, 600)
        self.setStyleSheet('background-color: #FFFFFF;')
        self.setMouseTracking(True)
        QToolTip.setFont(QFont('SansSerif', 10))

    def setImage(self, image_path):
        self.original_image = QPixmap(image_path)
        self.image = self.original_image.copy()
        self.image_loaded = True
        self.image_position = QPoint(0, 0)
        self.image_scale = 1.0  # Reset scale when a new image is loaded
        self.update()

    def scaleImage(self, factor):
        if self.image_loaded:
            self.image_scale *= factor
            width = int(self.original_image.width() * self.image_scale)
            height = int(self.original_image.height() * self.image_scale)
            self.image = self.original_image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.update()
        else:
            QMessageBox.warning(self, 'No Image', 'Please load an image before scaling.')

    def fitImageToScreens(self):
        if self.image_loaded and self.screens_defined:
            # Calculate the bounding rectangle of all screens
            screens_rect = self.calculateScreensBoundingRect()
            # Calculate the scaling factor needed to fit the image over the screens
            image_rect = QRect(0, 0, self.original_image.width(), self.original_image.height())

            # Calculate scale factors for width and height
            scale_w = screens_rect.width() / image_rect.width()
            scale_h = screens_rect.height() / image_rect.height()
            # Choose the maximum scale that fits the image inside the screens
            scale_factor = max(scale_w, scale_h)

            # Update image scale
            self.image_scale = scale_factor
            self.image = self.original_image.scaled(
                int(self.original_image.width() * self.image_scale),
                int(self.original_image.height() * self.image_scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Center the image over the screens
            self.image_position = QPoint(
                screens_rect.left() - (self.image.width() - screens_rect.width()) // 2,
                screens_rect.top() - (self.image.height() - screens_rect.height()) // 2
            )
            self.update()
        else:
            QMessageBox.warning(self, 'No Image or Screens', 'Please load an image and define screens before fitting.')

    def calculateScreensBoundingRect(self):
        # Calculate the bounding rectangle that contains all screens
        if not self.screen_arrangement:
            return QRect()
        rect = QRect(self.screen_arrangement[0]['pos'], self.screen_arrangement[0]['size'])
        for screen in self.screen_arrangement[1:]:
            screen_rect = QRect(screen['pos'], screen['size'])
            rect = rect.united(screen_rect)
        return rect

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale_factor, self.scale_factor)

        # Draw the background image (black and white, more opaque outside screens)
        if self.image:
            # Create a grayscale version of the image
            image_bw = self.image.toImage().convertToFormat(3)  # QImage.Format_Grayscale8
            image_bw_pixmap = QPixmap.fromImage(image_bw)
            painter.setOpacity(0.5)
            painter.drawPixmap(self.image_position, image_bw_pixmap)
            painter.setOpacity(1.0)

        # Create a clipping region for the screens
        screen_region = QRegion()
        for screen in self.screen_arrangement:
            rect = QRect(screen['pos'], screen['size'])
            screen_region = screen_region.united(QRegion(rect))

        # Clip to the screens and draw the image
        if self.image:
            painter.setClipRegion(screen_region)
            painter.drawPixmap(self.image_position, self.image)
            painter.setClipping(False)

        # Draw screens with red border if not fully covered
        for idx, screen in enumerate(self.screen_arrangement):
            rect = QRect(screen['pos'], screen['size'])
            # Check if the image fully covers the screen
            if self.image:
                image_rect = QRect(self.image_position, self.image.size())
                if image_rect.contains(rect):
                    pen_color = Qt.black
                else:
                    pen_color = Qt.red
            else:
                pen_color = Qt.black
            painter.setPen(QPen(pen_color, 2 / self.scale_factor))  # Adjust pen width
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignCenter, f"Screen {idx+1}")

        painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = (event.pos() - self.offset) / self.scale_factor
            if self.image_loaded:
                image_rect = QRect(self.image_position, self.image.size())
                if self.image and image_rect.contains(pos):
                    self.dragging_image = True
                    self.drag_start_pos = pos - self.image_position
            else:
                # Allow moving screens before image is loaded
                for screen in reversed(self.screen_arrangement):
                    rect = QRect(screen['pos'], screen['size'])
                    if rect.contains(pos):
                        self.dragging_screen = True
                        self.selected_screen = screen
                        self.drag_start_pos = pos - screen['pos']
                        break

    def mouseMoveEvent(self, event):
        pos = (event.pos() - self.offset) / self.scale_factor
        if self.dragging_image:
            self.image_position = pos - self.drag_start_pos
            self.update()
        elif self.dragging_screen:
            self.selected_screen['pos'] = pos - self.drag_start_pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_image = False
            self.dragging_screen = False

    def zoomIn(self):
        self.scale_factor *= 1.2
        self.update()

    def zoomOut(self):
        self.scale_factor /= 1.2
        self.update()

    def panLeft(self):
        self.offset += QPoint(20, 0)
        self.update()

    def panRight(self):
        self.offset -= QPoint(20, 0)
        self.update()

    def panUp(self):
        self.offset += QPoint(0, 20)
        self.update()

    def panDown(self):
        self.offset -= QPoint(0, 20)
        self.update()

    # Methods for fine adjustment
    def moveImage(self, dx, dy):
        if self.image_loaded:
            self.image_position += QPoint(dx, dy)
            self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_name = 'ScreenSlicer'  # Original and short name for the app
        self.setWindowTitle(self.app_name)
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Main title label, centered and bold
        title_label = QLabel('ScreenSlicer')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Updated subtitle with more precise description
        description_label = QLabel('Split images across multiple screens with precise control, custom configurations, and high-resolution exports.')
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(description_label)

        # Screen configuration
        config_layout = QHBoxLayout()

        self.configure_screens_btn = QPushButton('Configure Screens')
        self.configure_screens_btn.clicked.connect(self.configureScreens)
        self.configure_screens_btn.setToolTip('Manually configure your screens')
        config_layout.addWidget(self.configure_screens_btn)

        self.inherit_btn = QPushButton('Inherit from Windows')
        self.inherit_btn.clicked.connect(self.inheritFromWindows)
        self.inherit_btn.setToolTip('Automatically detect screens from Windows')
        config_layout.addWidget(self.inherit_btn)

        self.edit_screens_btn = QPushButton('Edit Screens')
        self.edit_screens_btn.clicked.connect(self.editScreens)
        self.edit_screens_btn.setEnabled(False)
        self.edit_screens_btn.setToolTip('Edit your screen configuration')
        config_layout.addWidget(self.edit_screens_btn)

        main_layout.addLayout(config_layout)

        # Zoom and Pan Controls
        controls_layout = QHBoxLayout()

        zoom_in_btn = QPushButton('Zoom In')
        zoom_in_btn.clicked.connect(self.zoomIn)
        zoom_in_btn.setToolTip('Zoom into the preview')
        controls_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton('Zoom Out')
        zoom_out_btn.clicked.connect(self.zoomOut)
        zoom_out_btn.setToolTip('Zoom out of the preview')
        controls_layout.addWidget(zoom_out_btn)

        pan_left_btn = QPushButton('Pan Left')
        pan_left_btn.clicked.connect(self.panLeft)
        pan_left_btn.setToolTip('Pan left in the preview')
        controls_layout.addWidget(pan_left_btn)

        pan_right_btn = QPushButton('Pan Right')
        pan_right_btn.clicked.connect(self.panRight)
        pan_right_btn.setToolTip('Pan right in the preview')
        controls_layout.addWidget(pan_right_btn)

        pan_up_btn = QPushButton('Pan Up')
        pan_up_btn.clicked.connect(self.panUp)
        pan_up_btn.setToolTip('Pan up in the preview')
        controls_layout.addWidget(pan_up_btn)

        pan_down_btn = QPushButton('Pan Down')
        pan_down_btn.clicked.connect(self.panDown)
        pan_down_btn.setToolTip('Pan down in the preview')
        controls_layout.addWidget(pan_down_btn)

        # Fine adjustment controls
        fine_adjust_layout = QHBoxLayout()
        fine_label = QLabel('Fine Adjust:')
        fine_adjust_layout.addWidget(fine_label)

        left_btn = QPushButton('←')
        left_btn.clicked.connect(lambda: self.preview_widget.moveImage(-1, 0))
        left_btn.setToolTip('Move image left by 1 pixel')
        fine_adjust_layout.addWidget(left_btn)

        right_btn = QPushButton('→')
        right_btn.clicked.connect(lambda: self.preview_widget.moveImage(1, 0))
        right_btn.setToolTip('Move image right by 1 pixel')
        fine_adjust_layout.addWidget(right_btn)

        up_btn = QPushButton('↑')
        up_btn.clicked.connect(lambda: self.preview_widget.moveImage(0, -1))
        up_btn.setToolTip('Move image up by 1 pixel')
        fine_adjust_layout.addWidget(up_btn)

        down_btn = QPushButton('↓')
        down_btn.clicked.connect(lambda: self.preview_widget.moveImage(0, 1))
        down_btn.setToolTip('Move image down by 1 pixel')
        fine_adjust_layout.addWidget(down_btn)

        # Image scaling controls
        scale_layout = QHBoxLayout()
        scale_up_btn = QPushButton('Scale Up')
        scale_up_btn.clicked.connect(self.scaleUp)
        scale_up_btn.setToolTip('Scale the image up')
        scale_layout.addWidget(scale_up_btn)

        scale_down_btn = QPushButton('Scale Down')
        scale_down_btn.clicked.connect(self.scaleDown)
        scale_down_btn.setToolTip('Scale the image down')
        scale_layout.addWidget(scale_down_btn)

        fit_btn = QPushButton('Try to Fit')
        fit_btn.clicked.connect(self.tryToFit)
        fit_btn.setToolTip('Automatically fit the image over the screens')
        scale_layout.addWidget(fit_btn)

        main_layout.addLayout(controls_layout)
        main_layout.addLayout(scale_layout)
        main_layout.addLayout(fine_adjust_layout)

        # Preview area
        self.preview_widget = PreviewWidget([], [], [])
        main_layout.addWidget(self.preview_widget)

        # Image input
        image_layout = QHBoxLayout()
        self.image_path = ''
        self.image_label = QLabel('No image selected.')
        image_layout.addWidget(self.image_label)
        self.load_image_btn = QPushButton('Load Image')
        self.load_image_btn.clicked.connect(self.loadImage)
        self.load_image_btn.setEnabled(False)  # Disable until screens are defined
        self.load_image_btn.setToolTip('Load an image to slice')
        image_layout.addWidget(self.load_image_btn)
        main_layout.addLayout(image_layout)

        # Export button
        self.export_btn = QPushButton('Export')
        self.export_btn.clicked.connect(self.exportImages)
        self.export_btn.setToolTip('Export sliced images for each screen')
        main_layout.addWidget(self.export_btn)

        # Footer with centered 'Made by' button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        made_by_btn = QPushButton('Made by Clément GHANEME')
        made_by_btn.clicked.connect(self.openWebsite)
        footer_layout.addWidget(made_by_btn)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def openWebsite(self):
        webbrowser.open('https://clement.business')

    def configureScreens(self):
        dialog = ScreenConfigDialog()
        if dialog.exec_() == QDialog.Accepted:
            if dialog.getValues():
                self.screen_resolutions = dialog.screen_resolutions
                self.screen_diagonals = dialog.screen_diagonals
                self.screen_aspect_ratios = dialog.screen_aspect_ratios
                self.calculatePhysicalSizes()
                self.arrangeScreens()
                QMessageBox.information(self, 'Configuration Saved', 'Screen configuration has been saved.')
                self.load_image_btn.setEnabled(True)
                self.preview_widget.screens_defined = True
                self.edit_screens_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, 'Configuration Error', 'Please correct the errors and try again.')
        else:
            pass  # User cancelled

    def inheritFromWindows(self):
        if platform.system() != 'Windows':
            QMessageBox.warning(self, 'Unsupported OS', 'Inherit from Windows is only supported on Windows.')
            return
        if get_monitors is None:
            QMessageBox.warning(self, 'Module Missing', 'The screeninfo module is required for this feature.')
            return
        monitors = get_monitors()
        self.screen_resolutions = []
        self.screen_diagonals = []
        self.screen_aspect_ratios = []
        for m in monitors:
            width = m.width
            height = m.height
            self.screen_resolutions.append((width, height))
            if m.width_mm == 0 or m.height_mm == 0:
                diag_cm = 54.6  # Assume a default size if dimensions are not available
            else:
                diag_cm = math.hypot(m.width_mm, m.height_mm) / 10  # Convert mm to cm
            self.screen_diagonals.append(diag_cm)
            gcd = math.gcd(width, height)
            ratio_w = width // gcd
            ratio_h = height // gcd
            self.screen_aspect_ratios.append((ratio_w, ratio_h))
        self.calculatePhysicalSizes()
        self.arrangeScreens()
        QMessageBox.information(self, 'Configuration Saved', 'Screen configuration has been inherited from Windows.')
        self.load_image_btn.setEnabled(True)
        self.preview_widget.screens_defined = True
        self.edit_screens_btn.setEnabled(True)

    def editScreens(self):
        existing_screens = []
        for i in range(len(self.screen_resolutions)):
            res_width, res_height = self.screen_resolutions[i]
            diag = self.screen_diagonals[i]
            ratio_w, ratio_h = self.screen_aspect_ratios[i]
            existing_screens.append({
                'res_width': res_width,
                'res_height': res_height,
                'diag': diag,
                'ratio_w': ratio_w,
                'ratio_h': ratio_h
            })
        dialog = ScreenConfigDialog(existing_screens)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.getValues():
                self.screen_resolutions = dialog.screen_resolutions
                self.screen_diagonals = dialog.screen_diagonals
                self.screen_aspect_ratios = dialog.screen_aspect_ratios
                self.calculatePhysicalSizes()
                self.arrangeScreens()
                QMessageBox.information(self, 'Configuration Saved', 'Screen configuration has been updated.')
            else:
                QMessageBox.warning(self, 'Configuration Error', 'Please correct the errors and try again.')
        else:
            pass  # User cancelled

    def calculatePhysicalSizes(self):
        self.screen_physical_sizes = []
        for diag_cm, aspect_ratio in zip(self.screen_diagonals, self.screen_aspect_ratios):
            ratio_w, ratio_h = aspect_ratio
            aspect = ratio_w / ratio_h
            h = diag_cm / math.sqrt(1 + aspect ** 2)
            w = aspect * h
            self.screen_physical_sizes.append((w, h))  # Physical width and height in cm

    def arrangeScreens(self):
        # Arrange screens in the preview area based on their physical sizes
        self.screen_arrangement = []

        # Calculate scaling factor to fit all screens into the preview area
        total_width_cm = sum(w for w, h in self.screen_physical_sizes)
        max_height_cm = max(h for w, h in self.screen_physical_sizes)

        # Calculate scaling factor
        preview_width = self.preview_widget.width() - 50  # Some padding
        preview_height = self.preview_widget.height() - 50
        scale_x = preview_width / total_width_cm
        scale_y = preview_height / max_height_cm
        scale = min(scale_x, scale_y)

        # Arrange screens
        x_offset = 25  # Initial padding
        y_offset = 25  # Center vertically
        for idx, (w_cm, h_cm) in enumerate(self.screen_physical_sizes):
            screen_w = w_cm * scale
            screen_h = h_cm * scale
            pos = QPoint(int(x_offset), int(y_offset + (max_height_cm - h_cm) * scale / 2))
            size = QSize(int(screen_w), int(screen_h))
            self.screen_arrangement.append({'pos': pos, 'size': size})
            x_offset += screen_w + 10  # 10 pixels spacing

        self.preview_widget.screen_arrangement = self.screen_arrangement
        self.preview_widget.screen_resolutions = self.screen_resolutions
        self.preview_widget.screen_physical_sizes = self.screen_physical_sizes
        self.preview_widget.image_loaded = False  # Reset image loaded flag
        self.preview_widget.image_position = QPoint(0, 0)
        self.preview_widget.update()

    def loadImage(self):
        if not self.preview_widget.screens_defined:
            QMessageBox.warning(self, 'No Configuration', 'Please configure screens before loading an image.')
            return
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        image_file, _ = QFileDialog.getOpenFileName(self, 'Select Image File', '', 'Images (*.png *.jpg *.jpeg)', options=options)
        if image_file:
            self.image_path = image_file
            self.image_label.setText(image_file)
            self.preview_widget.setImage(image_file)
        else:
            self.image_label.setText('No image selected.')

    def exportImages(self):
        if not self.image_path:
            QMessageBox.warning(self, 'No Image', 'Please load an image before exporting.')
            return
        if not hasattr(self, 'screen_arrangement'):
            QMessageBox.warning(self, 'No Configuration', 'Please configure screens before exporting.')
            return
        image = Image.open(self.image_path)
        image_width, image_height = image.size

        # Use the image position and scale from the preview to calculate crop boxes on the original image
        for idx, screen in enumerate(self.screen_arrangement):
            # Calculate the crop box in the original image
            left = (screen['pos'].x() - self.preview_widget.image_position.x()) / self.preview_widget.image_scale
            upper = (screen['pos'].y() - self.preview_widget.image_position.y()) / self.preview_widget.image_scale
            right = left + screen['size'].width() / self.preview_widget.image_scale
            lower = upper + screen['size'].height() / self.preview_widget.image_scale

            # Ensure the crop box is within the image bounds
            left = max(0, int(left))
            upper = max(0, int(upper))
            right = min(image_width, int(right))
            lower = min(image_height, int(lower))

            if left >= right or upper >= lower:
                QMessageBox.warning(self, 'Export Error', f'Screen {idx+1} is outside the image boundaries.')
                continue

            box = (left, upper, right, lower)
            cropped_image = image.crop(box)
            # Save the cropped image at the original resolution
            cropped_image.save(f'screen_{idx+1}.jpg')
        QMessageBox.information(self, 'Export Complete', 'Images have been exported successfully.')

    def zoomIn(self):
        self.preview_widget.zoomIn()

    def zoomOut(self):
        self.preview_widget.zoomOut()

    def panLeft(self):
        self.preview_widget.panLeft()

    def panRight(self):
        self.preview_widget.panRight()

    def panUp(self):
        self.preview_widget.panUp()

    def panDown(self):
        self.preview_widget.panDown()

    def scaleUp(self):
        # Calculate scaling factor based on grey area
        if self.preview_widget.image_loaded:
            grey_area_ratio = self.calculateGreyAreaRatio()
            factor = 1 + grey_area_ratio * 0.1  # Increase by up to 10% based on grey area
            self.preview_widget.scaleImage(factor)
        else:
            QMessageBox.warning(self, 'No Image', 'Please load an image before scaling.')

    def scaleDown(self):
        # Calculate scaling factor based on grey area
        if self.preview_widget.image_loaded:
            grey_area_ratio = self.calculateGreyAreaRatio()
            factor = 1 - grey_area_ratio * 0.1  # Decrease by up to 10% based on grey area
            if factor <= 0:
                QMessageBox.warning(self, 'Invalid Scale', 'Cannot scale down further.')
            else:
                self.preview_widget.scaleImage(factor)
        else:
            QMessageBox.warning(self, 'No Image', 'Please load an image before scaling.')

    def calculateGreyAreaRatio(self):
        # Calculate the ratio of grey area to the total image area
        if not self.preview_widget.image_loaded or not self.preview_widget.screens_defined:
            return 0
        image_rect = QRect(self.preview_widget.image_position, self.preview_widget.image.size())
        screens_rect = self.preview_widget.calculateScreensBoundingRect()
        intersection = image_rect.intersected(screens_rect)
        image_area = image_rect.width() * image_rect.height()
        intersection_area = intersection.width() * intersection.height()
        grey_area = image_area - intersection_area
        grey_area_ratio = grey_area / image_area if image_area > 0 else 0
        return grey_area_ratio

    def tryToFit(self):
        self.preview_widget.fitImageToScreens()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
