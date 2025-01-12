
# OddPing

OddPing is a real-time graphical tool to monitor and visualize ping latency to multiple servers. It displays ping data as a line graph, with customizable colors, server configurations, and visual settings. The application is designed to be lightweight, transparent, and always on top, making it perfect for monitoring network performance while working.

---

## Features

- **Real-Time Ping Monitoring**: Visualize ping latency to multiple servers in real-time.
- **Customizable Servers**: Add, remove, or modify servers with custom colors and settings.
- **Transparent Window**: Optional transparent and borderless window for minimal distraction.
- **Always on Top**: Keep the application window always on top of other windows.
- **Customizable Visuals**: Adjust graph scales, guide lines, and text offsets.
- **Drag-and-Drop Window**: Move the window by dragging it with the mouse.
- **Configuration File**: Easily customize settings via a `config.json` file.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- Required Python packages: `pygame`, `ping3`, `pywin32`

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/XenOdd/OddPing.git
   cd OddPing
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python OddPing.py
   ```

---

## Usage

### Configuration

The application uses a `config.json` file to store settings. If the file doesn't exist, it will be created automatically with default values. You can customize the following:

- **Window Settings**: Width, height, transparency, borderless mode, etc.
- **Visual Settings**: FPS, font size, guide lines, colors, etc.
- **Servers**: Add or modify servers with custom addresses, colors, and line thickness.

Example `config.json`:
```json
{
  "window_config": {
    "width": 800,
    "height": 200,
    "transparent": true,
    "borderless": true,
    "always_on_top": true,
    "background_color": [0, 0, 0],
    "padding_left": 10,
    "padding_right": 10
  },
  "visual_config": {
    "max_points": 100,
    "fps": 60,
    "font_size": 14,
    "ping_text_offset": [10, -10],
    "scale_decay_rate": 0.95,
    "text_color": [255, 255, 255],
    "ping_interval": 1.0,
    "show_guides": true,
    "guide_lines_color": [128, 128, 128],
    "guide_lines_thickness": 1,
    "guide_lines_length": 10,
    "guide_levels": [50, 100, 150]
  },
  "servers": [
    {
      "address": "1.1.1.1",
      "color": [255, 255, 0],
      "line_thickness": 2,
      "enabled": true
    },
    {
      "address": "8.8.8.8",
      "color": [0, 255, 0],
      "line_thickness": 2,
      "enabled": true
    }
  ]
}
```

### Running the Application

1. **Start the Application**:
   ```bash
   python OddPing.py
   ```

2. **Interact with the Window**:
   - **Drag**: Click and drag the window to move it.


