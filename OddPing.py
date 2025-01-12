import pygame
import win32gui
import win32con
from collections import deque
import time
from ping3 import ping
from dataclasses import dataclass, asdict
from typing import Dict, List
import json
import os
import sys

# Window Configuration
@dataclass
class WindowConfig:
    width: int = 800
    height: int = 200
    transparent: bool = True
    borderless: bool = True
    always_on_top: bool = True
    background_color: tuple = (0, 0, 0)
    padding_left: int = 10    # Separate padding for left and right
    padding_right: int = 10   # to control graph edges precisely

# Visual Configuration
@dataclass
class VisualConfig:
    max_points: int = 100
    fps: int = 60
    font_size: int = 14
    ping_text_offset: tuple = (10, -10)  # Offset from the newest point
    scale_decay_rate: float = 0.95
    text_color: tuple = (255, 255, 255)
    ping_interval: float = 1.0  # Time between pings in seconds
    
    # Guide lines configuration
    show_guides: bool = True
    guide_lines_color: tuple = (128, 128, 128)
    guide_lines_thickness: int = 1
    guide_lines_length: int = 10
    guide_levels: List[int] = None  # Will be set in __post_init__

    def __post_init__(self):
        if self.guide_levels is None:
            self.guide_levels = [50, 100, 150]  # Default guide levels

# Server Configuration
@dataclass
class ServerConfig:
    address: str
    color: tuple
    line_thickness: int = 2
    enabled: bool = True

    def __post_init__(self):
        # Ensure color is a tuple (Pygame requires tuples for colors)
        if isinstance(self.color, list):
            self.color = tuple(self.color)

# Default servers with their configurations
DEFAULT_SERVERS = [
    ServerConfig("1.1.1.1", (255, 255, 0), 2),  # Yellow
    ServerConfig("8.8.8.8", (0, 255, 0), 2),    # Green
    ServerConfig("8.8.4.4", (0, 255, 255), 2)   # Cyan
]

def get_config_path(config_file: str = "config.json"):
    """Get the absolute path to the config file."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as a script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, config_file)

def create_default_config(config_file: str = "config.json"):
    """Create a default config.json file if it doesn't exist."""
    if not os.path.exists(config_file):
        default_config = {
            "window_config": {
                "width": 200,
                "height": 100,
                "transparent": True,
                "borderless": True,
                "always_on_top": True,
                "background_color": [0, 0, 0],
                "padding_left": 10,
                "padding_right": 10
            },
            "visual_config": {
                "max_points": 60,
                "fps": 60,
                "font_size": 14,
                "ping_text_offset": [0, 0],
                "scale_decay_rate": 0.95,
                "text_color": [255, 255, 255],
                "ping_interval": 1.0,
                "show_guides": True,
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
                    "enabled": True
                },
                {
                    "address": "8.8.4.4",
                    "color": [0, 255, 255],
                    "line_thickness": 2,
                    "enabled": True
                }
            ]
        }
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
        print(f"Created default config file: {config_file}")

class PingVisualizer:
    def __init__(self, config_file: str = "config.json"):
        # Ensure config file exists
        config_path = get_config_path(config_file)
        create_default_config(config_path)
        
        # Load configuration
        self.load_config(config_path)
        
        # Initialize pygame
        pygame.init()
        
        # Window setup
        flags = 0
        if self.window_config.borderless:
            flags |= pygame.NOFRAME
        if self.window_config.transparent:
            flags |= pygame.SRCALPHA
            
        self.window = pygame.display.set_mode(
            (self.window_config.width, self.window_config.height), 
            flags
        )
        pygame.display.set_caption("Ping Visualizer")
        
        # Window properties
        if self.window_config.transparent or self.window_config.always_on_top:
            hwnd = pygame.display.get_wm_info()["window"]
            
            if self.window_config.transparent:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                                     win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
                win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
            
            if self.window_config.always_on_top:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        # Initialize font
        self.font = pygame.font.SysFont('arial', self.visual_config.font_size)
        
        # Initialize data storage for each server
        self.ping_data = {}
        self.current_max_ping = max(self.visual_config.guide_levels) * 1.5
        self.target_max_ping = self.current_max_ping
        self.last_ping_time = 0
        
        for server in self.servers:
            self.ping_data[server.address] = {
                'values': deque([0] * self.visual_config.max_points, maxlen=self.visual_config.max_points),
                'last_value': 0
            }
        
        self.running = True
        self.dragging = False
        self.drag_offset = (0, 0)
    
    def load_config(self, config_file: str):
        """Load configuration from a JSON file."""
        with open(config_file, "r") as f:
            config = json.load(f)
        
        # Convert JSON data back into dataclass objects
        self.window_config = WindowConfig(**config["window_config"])
        self.visual_config = VisualConfig(**config["visual_config"])
        self.servers = [ServerConfig(**server) for server in config["servers"]]
    
    def save_config(self, config_file: str = "config.json"):
        """Save the current configuration to a JSON file."""
        config = {
            "window_config": asdict(self.window_config),
            "visual_config": asdict(self.visual_config),
            "servers": [asdict(server) for server in self.servers]
        }
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        print(f"Saved configuration to: {config_file}")
    
    def get_ping(self, server: str) -> int:
        try:
            result = ping(server, timeout=1)
            if result is not None:
                return int(result * 1000)  # Convert to milliseconds
        except:
            pass
        return 0
    
    def update_scale(self):
        # Find highest ping across all servers
        highest_ping = 0
        for server_data in self.ping_data.values():
            highest_ping = max(highest_ping, max(server_data['values']))
        
        # Update target scale
        self.target_max_ping = max(
            highest_ping * 1.2,
            max(self.visual_config.guide_levels) * 1.2
        )
        
        # Smoothly adjust current scale
        if self.current_max_ping < self.target_max_ping:
            self.current_max_ping = self.target_max_ping
        else:
            self.current_max_ping = max(
                self.target_max_ping,
                self.current_max_ping * self.visual_config.scale_decay_rate
            )
    
    def update_values(self):
        current_time = time.time()
        if current_time - self.last_ping_time >= self.visual_config.ping_interval:
            for server in self.servers:
                if server.enabled:
                    ping_value = self.get_ping(server.address)
                    self.ping_data[server.address]['values'].append(ping_value)
                    self.ping_data[server.address]['last_value'] = ping_value
            self.last_ping_time = current_time
    
    def draw_guide_lines(self):
        if not self.visual_config.show_guides:
            return
            
        for level in self.visual_config.guide_levels:
            y = int(self.window_config.height - 
                   (level / self.current_max_ping) * 
                   (self.window_config.height - 20))
            
            # Draw three small lines
            x_positions = [
                self.window_config.padding_left,
                self.window_config.width // 2,
                self.window_config.width - self.window_config.padding_right
            ]
            
            for x in x_positions:
                pygame.draw.line(
                    self.window,
                    self.visual_config.guide_lines_color,
                    (x - self.visual_config.guide_lines_length // 2, y),
                    (x + self.visual_config.guide_lines_length // 2, y),
                    self.visual_config.guide_lines_thickness
                )
    
    def draw(self):
        self.window.fill(self.window_config.background_color)
        
        # Update scale
        self.update_scale()
        
        # Draw guide lines
        self.draw_guide_lines()
        
        # Draw each server's data
        for server in self.servers:
            if not server.enabled:
                continue
                
            server_data = self.ping_data[server.address]
            points = []
            
            # Calculate points with precise padding
            for i, value in enumerate(server_data['values']):
                x = self.window_config.width - self.window_config.padding_right - \
                    (len(server_data['values']) - i - 1) * \
                    ((self.window_config.width - self.window_config.padding_left - self.window_config.padding_right) / 
                     (self.visual_config.max_points - 1))
                y = self.window_config.height - \
                    (value / self.current_max_ping) * \
                    (self.window_config.height - 20)  # Fixed padding for bottom
                points.append((int(x), int(y)))
            
            # Draw lines
            if len(points) >= 2:
                pygame.draw.lines(
                    self.window,
                    server.color,  # Use server's color
                    False,
                    points,
                    server.line_thickness
                )
            
            # Draw ping value next to the newest point
            if points:
                text = f"{server_data['last_value']}ms"
                text_surface = self.font.render(text, True, server.color)  # Use server's color
                
                # Position text relative to the last point
                last_point = points[-1]
                text_pos = (
                    last_point[0] + self.visual_config.ping_text_offset[0],
                    last_point[1] + self.visual_config.ping_text_offset[1]
                )
                
                # Keep text within window bounds
                if text_pos[0] + text_surface.get_width() > self.window_config.width:
                    text_pos = (last_point[0] - text_surface.get_width() - 5, text_pos[1])
                
                self.window.blit(text_surface, text_pos)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.dragging = True
                    mouse_x, mouse_y = event.pos
                    hwnd = pygame.display.get_wm_info()["window"]
                    window_x, window_y = win32gui.GetWindowRect(hwnd)[:2]
                    self.drag_offset = (window_x - mouse_x, window_y - mouse_y)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mouse_x, mouse_y = event.pos
                    hwnd = pygame.display.get_wm_info()["window"]
                    x = mouse_x + self.drag_offset[0]
                    y = mouse_y + self.drag_offset[1]
                    win32gui.SetWindowPos(hwnd, 0, x, y, 0, 0, 
                                        win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)

    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.update_values()
            self.draw()
            clock.tick(self.visual_config.fps)
        
        pygame.quit()

if __name__ == "__main__":
    # Load configuration from config.json
    visualizer = PingVisualizer("config.json")
    visualizer.run()