#!/usr/bin/env python3
"""
PinokioCloud Terminal Widget for Notebook
Interactive terminal using ipywidgets
"""

import subprocess
import ipywidgets as widgets
from IPython.display import display
import threading
from datetime import datetime

class TerminalWidget:
    """Interactive terminal widget for notebook."""
    
    def __init__(self):
        self.command_history = []
        self.terminal_output = []
        
    def create_terminal(self):
        """Create interactive terminal interface."""
        
        # Header
        header = widgets.HTML(value="""
        <div style='background: linear-gradient(45deg, #333, #555); 
                   padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px;'>
            <h3>💻 Interactive Terminal</h3>
            <p>Execute commands and monitor output</p>
        </div>
        """)
        
        # Command input
        self.command_input = widgets.Text(
            placeholder='Enter command (e.g., ls, pip list, python --version)...',
            layout=widgets.Layout(width='500px')
        )
        
        # Control buttons
        run_btn = widgets.Button(description='▶️ Run', button_style='primary')
        clear_btn = widgets.Button(description='🗑️ Clear', button_style='warning')
        
        # Terminal output display
        self.output_area = widgets.Output(
            layout=widgets.Layout(
                width='100%', 
                height='300px',
                border='1px solid #ddd',
                background_color='#1e1e1e'
            )
        )
        
        # Bind events
        run_btn.on_click(self.run_command)
        clear_btn.on_click(self.clear_terminal)
        self.command_input.on_submit(self.run_command)
        
        # Layout
        controls = widgets.HBox([self.command_input, run_btn, clear_btn])
        
        return widgets.VBox([header, controls, self.output_area])
    
    def run_command(self, button_or_sender):
        """Execute the entered command."""
        command = self.command_input.value.strip()
        if not command:
            return
        
        # Add to history
        self.command_history.append(command)
        
        # Display command being run
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        with self.output_area:
            print(f"\\n[{timestamp}] $ {command}")
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Display output
            with self.output_area:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"ERROR: {result.stderr}")
                print(f"Exit code: {result.returncode}")
        
        except subprocess.TimeoutExpired:
            with self.output_area:
                print("⏰ Command timed out (30s limit)")
        
        except Exception as e:
            with self.output_area:
                print(f"❌ Command failed: {e}")
        
        # Clear input
        self.command_input.value = ""
    
    def clear_terminal(self, button):
        """Clear terminal output."""
        self.output_area.clear_output()
        with self.output_area:
            print("PinokioCloud Terminal - Ready")

def create_terminal():
    """Create and return terminal widget."""
    terminal = TerminalWidget()
    return terminal.create_terminal()

# Usage: terminal_widget = create_terminal()