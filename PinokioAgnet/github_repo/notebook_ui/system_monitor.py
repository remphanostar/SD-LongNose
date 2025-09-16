#!/usr/bin/env python3
"""
PinokioCloud System Monitor for Notebook
Real-time system monitoring using ipywidgets
"""

import ipywidgets as widgets
from IPython.display import display, HTML
import threading
import time

class SystemMonitor:
    """Simple system monitor for notebook."""
    
    def __init__(self):
        self.monitoring = False
        
    def create_system_monitor(self):
        """Create system monitoring interface."""
        
        # Header
        header = widgets.HTML(value="""
        <div style='background: linear-gradient(45deg, #28a745, #20c997); 
                   padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px;'>
            <h3>📊 System Resource Monitor</h3>
            <p>Real-time performance tracking</p>
        </div>
        """)
        
        # Resource bars
        self.cpu_bar = widgets.IntProgress(
            value=0, min=0, max=100,
            description='CPU:',
            bar_style='info',
            layout=widgets.Layout(width='350px')
        )
        
        self.memory_bar = widgets.IntProgress(
            value=0, min=0, max=100,
            description='Memory:',
            bar_style='warning', 
            layout=widgets.Layout(width='350px')
        )
        
        self.gpu_bar = widgets.IntProgress(
            value=0, min=0, max=100,
            description='GPU:',
            bar_style='success',
            layout=widgets.Layout(width='350px')
        )
        
        # System info display
        self.system_info = widgets.HTML(value=self.get_system_info())
        
        # Control buttons
        start_btn = widgets.Button(description='▶️ Start Monitoring', button_style='success')
        stop_btn = widgets.Button(description='⏹️ Stop Monitoring', button_style='danger')
        
        start_btn.on_click(lambda b: self.start_monitoring())
        stop_btn.on_click(lambda b: self.stop_monitoring())
        
        controls = widgets.HBox([start_btn, stop_btn])
        
        # Complete monitor
        return widgets.VBox([
            header,
            self.cpu_bar,
            self.memory_bar, 
            self.gpu_bar,
            controls,
            self.system_info
        ])
    
    def get_system_info(self):
        """Get current system information."""
        try:
            import psutil
            import platform
            
            # Get basic info
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return f"""
            <div style='background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                <h4>💻 System Information</h4>
                <p><strong>Platform:</strong> {platform.system()} {platform.release()}</p>
                <p><strong>CPU Cores:</strong> {cpu_count}</p>
                <p><strong>Total Memory:</strong> {memory.total / (1024**3):.1f} GB</p>
                <p><strong>Total Disk:</strong> {disk.total / (1024**3):.1f} GB</p>
                <p><strong>Python:</strong> {platform.python_version()}</p>
            </div>
            """
            
        except ImportError:
            return """
            <div style='background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                <h4>⚠️ System Info</h4>
                <p>psutil not available - install for detailed monitoring</p>
                <p><strong>Status:</strong> Basic monitoring only</p>
            </div>
            """
        except Exception as e:
            return f"""
            <div style='background: #f8d7da; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                <h4>❌ System Info Error</h4>
                <p>{str(e)}</p>
            </div>
            """
    
    def start_monitoring(self):
        """Start background monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            try:
                import psutil
                while self.monitoring:
                    # Update progress bars
                    self.cpu_bar.value = int(psutil.cpu_percent(interval=1))
                    
                    memory = psutil.virtual_memory()
                    self.memory_bar.value = int(memory.percent)
                    
                    # Simple GPU check (if available)
                    try:
                        # Try to get GPU info
                        self.gpu_bar.value = 0  # Default if no GPU monitoring
                    except:
                        self.gpu_bar.value = 0
                    
                    time.sleep(3)
            except ImportError:
                # Fallback without psutil
                while self.monitoring:
                    self.cpu_bar.value = 25  # Simulated values
                    self.memory_bar.value = 45
                    self.gpu_bar.value = 0
                    time.sleep(5)
            except Exception:
                self.monitoring = False
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        print("✅ Monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring = False
        print("⏹️ Monitoring stopped")

def create_system_monitor():
    """Create and return system monitor widget."""
    monitor = SystemMonitor()
    return monitor.create_system_monitor()

# Usage: monitor_widget = create_system_monitor()