
# ScreenSlicer

**ScreenSlicer** is a Python application that allows you to split images across multiple screens with precise control, custom configurations, and high-resolution exports. It's designed to help you create stunning multi-monitor wallpapers or display images seamlessly across several displays.

## Features

- **Custom Screen Configuration**: Manually configure your screens by entering resolution, diagonal size, and aspect ratio.
- **Inherit from Windows**: Automatically detect and inherit screen settings from Windows (only on Windows OS).
- **High-Resolution Export**: Export sliced images at the original resolution without any loss of quality.
- **Visual Feedback**: Screens not fully covered by the image are highlighted with red borders in the preview.
- **Fine Adjustment Controls**: Precisely position the image with one-pixel adjustments.
- **Image Scaling and Fitting**: Scale images up or down and automatically fit images over the configured screens.
- **User-Friendly Interface**: Tooltips and placeholder texts guide you through the application.
- **Developer Attribution**: A link to the developer's website is provided for more information.

## Getting Started

### Prerequisites

- **Python 3.x**
- **Required Python Modules**:
  - PyQt5
  - Pillow
  - screeninfo (optional, required for inheriting screen settings from Windows)

### Running the Application

Run the script using Python 3:

```bash
python screenslicer.py
```

## Usage

1. **Configure Screens**:

   - Click **"Configure Screens"** to manually set up your screens.
   - Enter the resolution (width and height in pixels), diagonal size (in cm), and select the aspect ratio for each screen.
   - Add or remove screens as needed.

   *Alternatively*, if you're on a Windows system, click **"Inherit from Windows"** to automatically detect and import your screen settings.

2. **Load an Image**:

   - After configuring screens, click **"Load Image"** to select the image you want to split.

3. **Adjust the Image**:

   - Use the **Scaling** and **Panning** controls to adjust the image position and size.
   - Use the **Fine Adjust** buttons to move the image one pixel at a time for precise positioning.
   - Screens not fully covered by the image will display a red border in the preview.

4. **Fit Image Over Screens**:

   - Click **"Try to Fit"** to automatically scale and position the image over the configured screens.

5. **Export Images**:

   - Click **"Export"** to save the sliced images for each screen.
   - The images will be saved in the same directory as the script with filenames like `screen_1.jpg`, `screen_2.jpg`, etc.

6. **Visit the Developer's Website**:

   - Click **"Made by Clément GHANEME"** at the bottom of the application to open the developer's website: [https://clement.business](https://clement.business).

## GUI

https://github.com/user-attachments/assets/31ec6d64-5b05-40ff-bb7a-dc9192bb0a04

## Troubleshooting

- **Modules Not Found**:

  If you encounter errors related to missing modules, ensure all dependencies are installed. Run:

  ```bash
  pip install PyQt5 Pillow screeninfo
  ```

- **Inherit from Windows Not Working**:

  - Ensure you are running the application on a Windows system.
  - Make sure the `screeninfo` module is installed.

- **Export Issues**:

  - Ensure that you have loaded an image and configured your screens before exporting.
  - If a screen is highlighted in red, it means the image does not fully cover that screen.

- **Application Crashes When Moving Screens**:

  - Make sure you are using the latest version of the code with the `toPoint()` method issue fixed.
  - If the problem persists, please report the issue on the GitHub repository.

##Infos

- **Developer**: Clément GHANEME
- **Website**: [https://clement.business](https://clement.business)
- **Initial Release** : 24/11/2024

---

*Enjoy using ScreenSlicer to create amazing multi-monitor setups!*
