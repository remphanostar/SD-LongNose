#!/usr/bin/env python3
"""
PinokioCloud Terminal Widget

This module provides a real-time terminal display widget for the Streamlit interface.
It shows live output from app installations, running processes, and system commands
with full ANSI color support and real-time streaming capabilities.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import threading
import queue
import subprocess
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import html

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

from environment_management.shell_runner import ShellRunner
from optimization.logging_system import LoggingSystem


class LogLevel(Enum):
    """Terminal log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"


@dataclass
class TerminalMessage:
    """Represents a terminal message."""
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    raw_output: bool = False
    ansi_formatted: bool = False


class ANSIConverter:
    """Converts ANSI escape sequences to HTML for display."""
    
    # ANSI color codes to HTML
    ANSI_COLORS = {
        '30': '#000000',  # Black
        '31': '#ff4444',  # Red
        '32': '#00ff9f',  # Green
        '33': '#ffaa00',  # Yellow
        '34': '#00d4ff',  # Blue
        '35': '#ff44ff',  # Magenta
        '36': '#00ffff',  # Cyan
        '37': '#ffffff',  # White
        '90': '#666666',  # Bright Black
        '91': '#ff6666',  # Bright Red
        '92': '#66ff66',  # Bright Green
        '93': '#ffff66',  # Bright Yellow
        '94': '#6666ff',  # Bright Blue
        '95': '#ff66ff',  # Bright Magenta
        '96': '#66ffff',  # Bright Cyan
        '97': '#ffffff',  # Bright White
    }
    
    # Background colors
    ANSI_BG_COLORS = {
        '40': '#000000',  # Black background
        '41': '#ff4444',  # Red background
        '42': '#00ff9f',  # Green background
        '43': '#ffaa00',  # Yellow background
        '44': '#00d4ff',  # Blue background
        '45': '#ff44ff',  # Magenta background
        '46': '#00ffff',  # Cyan background
        '47': '#ffffff',  # White background
    }
    
    @classmethod
    def convert_ansi_to_html(cls, text: str) -> str:
        """Convert ANSI escape sequences to HTML."""
        if not text:
            return ""
            
        # Escape HTML first
        text = html.escape(text)
        
        # Convert ANSI color codes
        ansi_pattern = r'\x1b\[([0-9;]*)m'
        
        def replace_ansi(match):
            codes = match.group(1).split(';') if match.group(1) else ['0']
            styles = []
            
            for code in codes:
                if code == '0' or code == '':  # Reset
                    return '</span>'
                elif code == '1':  # Bold
                    styles.append('font-weight: bold')
                elif code == '3':  # Italic
                    styles.append('font-style: italic')
                elif code == '4':  # Underline
                    styles.append('text-decoration: underline')
                elif code in cls.ANSI_COLORS:  # Foreground colors
                    styles.append(f'color: {cls.ANSI_COLORS[code]}')
                elif code in cls.ANSI_BG_COLORS:  # Background colors
                    styles.append(f'background-color: {cls.ANSI_BG_COLORS[code]}')
                    
            if styles:
                return f'<span style="{"; ".join(styles)}">'
            else:
                return ''
                
        # Replace ANSI codes with HTML spans
        html_text = re.sub(ansi_pattern, replace_ansi, text)
        
        # Ensure all spans are properly closed
        open_spans = html_text.count('<span')
        close_spans = html_text.count('</span>')
        if open_spans > close_spans:
            html_text += '</span>' * (open_spans - close_spans)
            
        return html_text


class TerminalWidget:
    """
    Real-time Terminal Widget for Streamlit
    
    This widget provides a terminal interface within the Streamlit app that can
    display real-time output from installations, processes, and system commands
    with full ANSI color support and streaming capabilities.
    """
    
    def __init__(self, max_lines: int = 1000):
        """
        Initialize the terminal widget.
        
        Args:
            max_lines: Maximum number of lines to keep in terminal history
        """
        self.max_lines = max_lines
        self.messages: List[TerminalMessage] = []
        self.message_queue = queue.Queue()
        self.shell_runner = ShellRunner()
        self.logging_system = LoggingSystem()
        self.ansi_converter = ANSIConverter()
        
        # Terminal state
        self.is_running = False
        self.current_command = None
        self.command_thread = None
        
        # Initialize session state
        if 'terminal_messages' not in st.session_state:
            st.session_state.terminal_messages = []
        if 'terminal_auto_scroll' not in st.session_state:
            st.session_state.terminal_auto_scroll = True
        if 'terminal_show_timestamps' not in st.session_state:
            st.session_state.terminal_show_timestamps = True
        if 'terminal_filter_level' not in st.session_state:
            st.session_state.terminal_filter_level = "INFO"
            
    def add_message(self, level: LogLevel, source: str, message: str, raw_output: bool = False):
        """Add a message to the terminal."""
        terminal_message = TerminalMessage(
            timestamp=datetime.now(),
            level=level,
            source=source,
            message=message,
            raw_output=raw_output,
            ansi_formatted=raw_output  # Raw output might contain ANSI codes
        )
        
        # Add to session state
        st.session_state.terminal_messages.append(terminal_message)
        
        # Limit message history
        if len(st.session_state.terminal_messages) > self.max_lines:
            st.session_state.terminal_messages = st.session_state.terminal_messages[-self.max_lines:]
            
        # Log to system
        self.logging_system.log_info("Terminal", f"Terminal: [{source}] {message}")
        
    def clear_terminal(self):
        """Clear all terminal messages."""
        st.session_state.terminal_messages = []
        self.add_message(LogLevel.SYSTEM, "Terminal", "Terminal cleared")
        
    def execute_command(self, command: str, working_dir: Optional[str] = None):
        """Execute a command and stream output to terminal."""
        if self.is_running:
            self.add_message(LogLevel.WARNING, "Terminal", "Another command is already running")
            return
            
        self.is_running = True
        self.current_command = command
        
        self.add_message(LogLevel.INFO, "Terminal", f"Executing: {command}")
        
        def run_command():
            try:
                # Use shell runner to execute command with real-time output
                result = self.shell_runner.run_command_with_output(
                    command,
                    working_directory=working_dir,
                    capture_output=True,
                    stream_output=True,
                    output_callback=self._command_output_callback
                )
                
                if result.success:
                    self.add_message(LogLevel.SUCCESS, "Terminal", f"Command completed successfully (exit code: {result.exit_code})")
                else:
                    self.add_message(LogLevel.ERROR, "Terminal", f"Command failed (exit code: {result.exit_code})")
                    if result.stderr:
                        self.add_message(LogLevel.ERROR, "STDERR", result.stderr, raw_output=True)
                        
            except Exception as e:
                self.add_message(LogLevel.ERROR, "Terminal", f"Command execution failed: {str(e)}")
            finally:
                self.is_running = False
                self.current_command = None
                
        # Run command in background thread
        self.command_thread = threading.Thread(target=run_command, daemon=True)
        self.command_thread.start()
        
    def _command_output_callback(self, output: str, is_stderr: bool = False):
        """Callback for real-time command output."""
        source = "STDERR" if is_stderr else "STDOUT"
        level = LogLevel.ERROR if is_stderr else LogLevel.INFO
        
        # Split output into lines for better display
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip():  # Only add non-empty lines
                self.add_message(level, source, line, raw_output=True)
                
    def render_terminal_controls(self):
        """Render terminal control buttons and options."""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("🧹 Clear Terminal"):
                self.clear_terminal()
                st.rerun()
                
        with col2:
            auto_scroll = st.checkbox("Auto Scroll", value=st.session_state.terminal_auto_scroll)
            st.session_state.terminal_auto_scroll = auto_scroll
            
        with col3:
            show_timestamps = st.checkbox("Show Timestamps", value=st.session_state.terminal_show_timestamps)
            st.session_state.terminal_show_timestamps = show_timestamps
            
        with col4:
            filter_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS", "SYSTEM"]
            filter_level = st.selectbox("Filter Level", filter_levels, 
                                      index=filter_levels.index(st.session_state.terminal_filter_level))
            st.session_state.terminal_filter_level = filter_level
            
        with col5:
            if st.button("📥 Export Logs"):
                self.export_terminal_logs()
                
    def render_command_input(self):
        """Render command input interface."""
        st.markdown("### 💻 Command Execution")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            command = st.text_input(
                "Enter command:",
                placeholder="pip install package_name",
                disabled=self.is_running,
                key="terminal_command_input"
            )
            
        with col2:
            if st.button("▶️ Execute", disabled=self.is_running or not command):
                self.execute_command(command)
                st.rerun()
                
        # Show current running command
        if self.is_running and self.current_command:
            st.info(f"🔄 Running: {self.current_command}")
            
        # Predefined commands
        st.markdown("#### 🚀 Quick Commands")
        quick_commands = {
            "System Info": "uname -a && python --version && pip --version",
            "List Processes": "ps aux | head -10",
            "Disk Usage": "df -h",
            "Memory Usage": "free -h",
            "GPU Info": "nvidia-smi",
            "Python Packages": "pip list | head -20",
            "Network Test": "ping -c 4 google.com"
        }
        
        cols = st.columns(len(quick_commands))
        for i, (name, cmd) in enumerate(quick_commands.items()):
            with cols[i % len(cols)]:
                if st.button(name, disabled=self.is_running, key=f"quick_cmd_{i}"):
                    self.execute_command(cmd)
                    st.rerun()
                    
    def format_message_for_display(self, message: TerminalMessage) -> str:
        """Format a terminal message for display."""
        timestamp_str = ""
        if st.session_state.terminal_show_timestamps:
            timestamp_str = f"[{message.timestamp.strftime('%H:%M:%S')}] "
            
        level_color = {
            LogLevel.DEBUG: "#666666",
            LogLevel.INFO: "#00ff9f",
            LogLevel.WARNING: "#ffaa00",
            LogLevel.ERROR: "#ff4444",
            LogLevel.SUCCESS: "#00ff9f",
            LogLevel.SYSTEM: "#00d4ff"
        }.get(message.level, "#ffffff")
        
        source_str = f"[{message.source}]" if message.source != "Terminal" else ""
        
        # Process message content
        content = message.message
        if message.ansi_formatted:
            content = self.ansi_converter.convert_ansi_to_html(content)
        else:
            content = html.escape(content)
            
        return f'<span style="color: {level_color}">{timestamp_str}{source_str} {content}</span>'
        
    def render_terminal_output(self):
        """Render the terminal output area."""
        st.markdown("### 📺 Terminal Output")
        
        # Filter messages based on level
        level_hierarchy = {
            "DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "SUCCESS": 1, "SYSTEM": 1
        }
        min_level = level_hierarchy.get(st.session_state.terminal_filter_level, 1)
        
        filtered_messages = [
            msg for msg in st.session_state.terminal_messages
            if level_hierarchy.get(msg.level.value.upper(), 1) >= min_level
        ]
        
        # Create terminal output
        if not filtered_messages:
            st.info("No terminal output yet. Execute a command to see output here.")
        else:
            # Build terminal content
            terminal_content = []
            for message in filtered_messages[-100:]:  # Show last 100 messages
                formatted_msg = self.format_message_for_display(message)
                terminal_content.append(formatted_msg)
                
            # Display in a scrollable container
            terminal_html = f"""
            <div class="terminal-container" style="
                background: #000000;
                border: 1px solid #00ff9f;
                border-radius: 10px;
                padding: 1rem;
                font-family: 'Courier New', monospace;
                color: #00ff9f;
                max-height: 400px;
                overflow-y: auto;
                font-size: 12px;
                line-height: 1.4;
            ">
                {'<br>'.join(terminal_content)}
            </div>
            """
            
            st.markdown(terminal_html, unsafe_allow_html=True)
            
        # Show terminal statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", len(st.session_state.terminal_messages))
        with col2:
            st.metric("Filtered Messages", len(filtered_messages))
        with col3:
            status = "🔄 Running" if self.is_running else "⏹️ Idle"
            st.metric("Status", status)
            
    def export_terminal_logs(self):
        """Export terminal logs to file."""
        try:
            log_content = []
            for message in st.session_state.terminal_messages:
                timestamp = message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                log_line = f"[{timestamp}] [{message.level.value.upper()}] [{message.source}] {message.message}"
                log_content.append(log_line)
                
            log_text = '\n'.join(log_content)
            
            # Create download button
            st.download_button(
                label="📥 Download Terminal Logs",
                data=log_text,
                file_name=f"pinokiocloud_terminal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"Failed to export logs: {str(e)}")
            
    def render_terminal(self):
        """Render the complete terminal interface."""
        try:
            # Terminal controls
            self.render_terminal_controls()
            
            st.markdown("---")
            
            # Command input
            self.render_command_input()
            
            st.markdown("---")
            
            # Terminal output
            self.render_terminal_output()
            
            # Auto-refresh for running commands
            if self.is_running and st.session_state.terminal_auto_scroll:
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            st.error(f"Terminal widget error: {str(e)}")
            self.logging_system.log_error("Terminal widget error", {"error": str(e)})
            
    def add_installation_output(self, app_name: str, output: str, is_error: bool = False):
        """Add installation output to terminal."""
        level = LogLevel.ERROR if is_error else LogLevel.INFO
        source = f"INSTALL:{app_name}"
        
        # Split multi-line output
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip():
                self.add_message(level, source, line, raw_output=True)
                
    def add_system_message(self, message: str, level: LogLevel = LogLevel.SYSTEM):
        """Add a system message to terminal."""
        self.add_message(level, "System", message)
        
    def add_debug_message(self, message: str, source: str = "Debug"):
        """Add a debug message to terminal."""
        self.add_message(LogLevel.DEBUG, source, message)


def main():
    """Test the terminal widget."""
    st.set_page_config(page_title="Terminal Widget Test", layout="wide")
    
    st.title("🖥️ Terminal Widget Test")
    
    terminal = TerminalWidget()
    
    # Add some test messages
    if st.button("Add Test Messages"):
        terminal.add_message(LogLevel.INFO, "Test", "This is an info message")
        terminal.add_message(LogLevel.WARNING, "Test", "This is a warning message")
        terminal.add_message(LogLevel.ERROR, "Test", "This is an error message")
        terminal.add_message(LogLevel.SUCCESS, "Test", "This is a success message")
        terminal.add_message(LogLevel.SYSTEM, "Test", "This is a system message")
        
    terminal.render_terminal()


if __name__ == "__main__":
    main()