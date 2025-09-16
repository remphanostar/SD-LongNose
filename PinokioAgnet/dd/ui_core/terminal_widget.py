#!/usr/bin/env python3
"""
PinokioCloud Core Terminal Widget

This module provides a core terminal widget with essential functionality including
real-time command execution, ANSI color support, and modern Streamlit features
like st.status and st.toast for better user experience.

Author: PinokioCloud Development Team
Version: 1.0.0 (Core)
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
    Core Terminal Widget for Streamlit
    
    This widget provides essential terminal functionality with modern Streamlit
    features including st.status for command execution, st.toast for notifications,
    and real-time output streaming with ANSI color support.
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
        st.toast("🧹 Terminal cleared", icon="🧹")
        
    def execute_command(self, command: str, working_dir: Optional[str] = None):
        """Execute a command and stream output to terminal using modern Streamlit features."""
        if self.is_running:
            st.toast("⚠️ Another command is already running", icon="⚠️")
            return
            
        self.is_running = True
        self.current_command = command
        
        self.add_message(LogLevel.INFO, "Terminal", f"Executing: {command}")
        
        # Use st.status for better command execution feedback
        with st.status(f"Running: {command}", expanded=True) as status:
            def run_command():
                try:
                    status.write("📋 Preparing command execution...")
                    
                    # Use shell runner to execute command with real-time output
                    result = self.shell_runner.run_command_with_output(
                        command,
                        working_directory=working_dir,
                        capture_output=True,
                        stream_output=True,
                        output_callback=self._command_output_callback
                    )
                    
                    if result.success:
                        status.update(label="✅ Command completed successfully", state="complete")
                        self.add_message(LogLevel.SUCCESS, "Terminal", f"Command completed successfully (exit code: {result.exit_code})")
                        st.toast(f"✅ Command completed: {command}", icon="✅")
                    else:
                        status.update(label="❌ Command failed", state="error")
                        self.add_message(LogLevel.ERROR, "Terminal", f"Command failed (exit code: {result.exit_code})")
                        if result.stderr:
                            self.add_message(LogLevel.ERROR, "STDERR", result.stderr, raw_output=True)
                        st.toast(f"❌ Command failed: {command}", icon="❌")
                        
                except Exception as e:
                    status.update(label="🚨 Command execution error", state="error")
                    self.add_message(LogLevel.ERROR, "Terminal", f"Command execution failed: {str(e)}")
                    st.toast(f"🚨 Execution error: {str(e)}", icon="🚨")
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
        st.markdown("### 🎛️ Terminal Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🧹 Clear Terminal", type="secondary"):
                self.clear_terminal()
                st.rerun()
                
        with col2:
            auto_scroll = st.toggle("Auto Scroll", value=st.session_state.terminal_auto_scroll)
            st.session_state.terminal_auto_scroll = auto_scroll
            
        with col3:
            show_timestamps = st.toggle("Timestamps", value=st.session_state.terminal_show_timestamps)
            st.session_state.terminal_show_timestamps = show_timestamps
            
        with col4:
            filter_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS", "SYSTEM"]
            filter_level = st.selectbox(
                "Filter Level", 
                filter_levels, 
                index=filter_levels.index(st.session_state.terminal_filter_level),
                label_visibility="collapsed"
            )
            st.session_state.terminal_filter_level = filter_level
            
    def render_command_input(self):
        """Render command input interface."""
        st.markdown("### 💻 Command Execution")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            command = st.text_input(
                "Enter command:",
                placeholder="pip install package_name",
                disabled=self.is_running,
                key="terminal_command_input",
                help="Enter a shell command to execute"
            )
            
        with col2:
            execute_button = st.button(
                "▶️ Execute", 
                disabled=self.is_running or not command,
                type="primary",
                use_container_width=True
            )
            
        if execute_button and command:
            self.execute_command(command)
            st.rerun()
            
        # Show current running command with modern status
        if self.is_running and self.current_command:
            st.info(f"🔄 Running: `{self.current_command}`")
            
        # Quick commands with modern pill-style buttons
        st.markdown("#### 🚀 Quick Commands")
        
        quick_commands = {
            "System Info": "uname -a && python3 --version && pip --version",
            "List Processes": "ps aux | head -10",
            "Disk Usage": "df -h",
            "Memory Usage": "free -h",
            "GPU Info": "nvidia-smi",
            "Python Packages": "pip list | head -20"
        }
        
        # Create columns for quick command buttons
        cols = st.columns(3)
        for i, (name, cmd) in enumerate(quick_commands.items()):
            with cols[i % 3]:
                if st.button(name, disabled=self.is_running, key=f"quick_cmd_{i}", use_container_width=True):
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
            st.info("📝 No terminal output yet. Execute a command to see output here.")
        else:
            # Build terminal content
            terminal_content = []
            for message in filtered_messages[-50:]:  # Show last 50 messages
                formatted_msg = self.format_message_for_display(message)
                terminal_content.append(formatted_msg)
                
            # Display in a scrollable container with modern styling
            terminal_html = f"""
            <div style="
                background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
                border: 2px solid #00ff9f;
                border-radius: 15px;
                padding: 1.5rem;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                color: #00ff9f;
                max-height: 400px;
                overflow-y: auto;
                font-size: 13px;
                line-height: 1.4;
                box-shadow: 0 8px 32px rgba(0, 255, 159, 0.2);
                backdrop-filter: blur(10px);
            ">
                {'<br>'.join(terminal_content)}
            </div>
            """
            
            st.markdown(terminal_html, unsafe_allow_html=True)
            
        # Show terminal statistics with modern metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Messages", len(st.session_state.terminal_messages))
        with col2:
            st.metric("🔍 Filtered", len(filtered_messages))
        with col3:
            status = "🔄 Running" if self.is_running else "⏹️ Ready"
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
                mime="text/plain",
                type="secondary"
            )
            
        except Exception as e:
            st.toast(f"❌ Failed to export logs: {str(e)}", icon="❌")
            
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
            
            # Export functionality
            st.markdown("### 📤 Export")
            col1, col2 = st.columns(2)
            with col1:
                self.export_terminal_logs()
            with col2:
                if st.button("📊 View Statistics", type="secondary"):
                    st.toast("📊 Terminal statistics displayed above", icon="📊")
            
            # Auto-refresh for running commands
            if self.is_running and st.session_state.terminal_auto_scroll:
                time.sleep(2)
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
    """Test the core terminal widget."""
    st.set_page_config(page_title="Core Terminal Widget Test", layout="wide")
    
    st.title("🖥️ Core Terminal Widget Test")
    
    terminal = TerminalWidget()
    
    # Add some test messages
    if st.button("Add Test Messages"):
        terminal.add_message(LogLevel.INFO, "Test", "This is an info message")
        terminal.add_message(LogLevel.WARNING, "Test", "This is a warning message")
        terminal.add_message(LogLevel.ERROR, "Test", "This is an error message")
        terminal.add_message(LogLevel.SUCCESS, "Test", "This is a success message")
        terminal.add_message(LogLevel.SYSTEM, "Test", "This is a system message")
        st.toast("✅ Test messages added!", icon="✅")
        
    terminal.render_terminal()


if __name__ == "__main__":
    main()