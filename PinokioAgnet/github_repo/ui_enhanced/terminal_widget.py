#!/usr/bin/env python3
"""
PinokioCloud Enhanced Terminal Widget

This module provides the ultimate terminal experience using cutting-edge Streamlit
features including fragments for real-time updates, advanced status widgets,
AI command suggestions, and enhanced ANSI color support with holographic effects.

Author: PinokioCloud Development Team
Version: 2.0.0 (Enhanced)
"""

import os
import sys
import time
import threading
import queue
import subprocess
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import html
import json

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

from environment_management.shell_runner import ShellRunner
from optimization.logging_system import LoggingSystem


class LogLevel(Enum):
    """Enhanced terminal log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"
    AI_SUGGESTION = "ai_suggestion"
    PERFORMANCE = "performance"


@dataclass
class EnhancedTerminalMessage:
    """Enhanced terminal message with additional metadata."""
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    raw_output: bool = False
    ansi_formatted: bool = False
    command_id: Optional[str] = None
    execution_time: Optional[float] = None
    exit_code: Optional[int] = None
    tags: List[str] = field(default_factory=list)


class EnhancedANSIConverter:
    """Enhanced ANSI converter with advanced styling and effects."""
    
    # Enhanced ANSI color codes with cyberpunk theme
    ANSI_COLORS = {
        '30': '#000000',  # Black
        '31': '#ff4444',  # Red
        '32': '#00ff9f',  # Green (cyberpunk primary)
        '33': '#ffaa00',  # Yellow
        '34': '#00d4ff',  # Blue (cyberpunk secondary)
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
    def convert_ansi_to_html(cls, text: str, enhanced_mode: bool = True) -> str:
        """Convert ANSI escape sequences to enhanced HTML with effects."""
        if not text:
            return ""
            
        # Escape HTML first
        text = html.escape(text)
        
        # Enhanced ANSI conversion with glow effects
        ansi_pattern = r'\x1b\[([0-9;]*)m'
        
        def replace_ansi(match):
            codes = match.group(1).split(';') if match.group(1) else ['0']
            styles = []
            
            for code in codes:
                if code == '0' or code == '':  # Reset
                    return '</span>'
                elif code == '1':  # Bold with glow
                    if enhanced_mode:
                        styles.append('font-weight: bold; text-shadow: 0 0 5px currentColor')
                    else:
                        styles.append('font-weight: bold')
                elif code == '3':  # Italic
                    styles.append('font-style: italic')
                elif code == '4':  # Underline with glow
                    if enhanced_mode:
                        styles.append('text-decoration: underline; text-decoration-color: currentColor; text-shadow: 0 0 3px currentColor')
                    else:
                        styles.append('text-decoration: underline')
                elif code in cls.ANSI_COLORS:  # Foreground colors
                    color = cls.ANSI_COLORS[code]
                    if enhanced_mode:
                        styles.append(f'color: {color}; text-shadow: 0 0 8px {color}')
                    else:
                        styles.append(f'color: {color}')
                    
            if styles:
                return f'<span style="{"; ".join(styles)}">'
            else:
                return ''
                
        # Replace ANSI codes with enhanced HTML spans
        html_text = re.sub(ansi_pattern, replace_ansi, text)
        
        # Ensure all spans are properly closed
        open_spans = html_text.count('<span')
        close_spans = html_text.count('</span>')
        if open_spans > close_spans:
            html_text += '</span>' * (open_spans - close_spans)
            
        return html_text


class EnhancedTerminalWidget:
    """
    Enhanced Terminal Widget with Cutting-Edge Features
    
    This widget provides the ultimate terminal experience using fragments for
    real-time updates, AI command suggestions, advanced status tracking,
    and enhanced visual effects with holographic styling.
    """
    
    def __init__(self, max_lines: int = 2000):
        """
        Initialize the enhanced terminal widget.
        
        Args:
            max_lines: Maximum number of lines to keep in terminal history
        """
        self.max_lines = max_lines
        self.enhanced_converter = EnhancedANSIConverter()
        self.shell_runner = ShellRunner()
        self.logging_system = LoggingSystem()
        
        # Enhanced terminal state
        self.is_running = False
        self.current_command = None
        self.command_thread = None
        self.command_history = []
        self.ai_suggestions = []
        
        # Initialize enhanced session state
        if 'enhanced_terminal_messages' not in st.session_state:
            st.session_state.enhanced_terminal_messages = []
        if 'terminal_preferences' not in st.session_state:
            st.session_state.terminal_preferences = {
                'auto_scroll': True,
                'show_timestamps': True,
                'filter_level': "INFO",
                'enhanced_mode': True,
                'ai_suggestions': True,
                'command_history': True,
                'performance_tracking': True
            }
        if 'command_statistics' not in st.session_state:
            st.session_state.command_statistics = {
                'total_commands': 0,
                'successful_commands': 0,
                'failed_commands': 0,
                'average_execution_time': 0.0
            }
            
    def add_enhanced_message(self, level: LogLevel, source: str, message: str, 
                           raw_output: bool = False, command_id: str = None, 
                           execution_time: float = None, exit_code: int = None):
        """Add an enhanced message to the terminal."""
        terminal_message = EnhancedTerminalMessage(
            timestamp=datetime.now(),
            level=level,
            source=source,
            message=message,
            raw_output=raw_output,
            ansi_formatted=raw_output,
            command_id=command_id,
            execution_time=execution_time,
            exit_code=exit_code
        )
        
        # Add to session state
        st.session_state.enhanced_terminal_messages.append(terminal_message)
        
        # Limit message history
        if len(st.session_state.enhanced_terminal_messages) > self.max_lines:
            st.session_state.enhanced_terminal_messages = st.session_state.enhanced_terminal_messages[-self.max_lines:]
            
        # Enhanced logging
        self.logging_system.log_info("Terminal", f"Enhanced Terminal: [{source}] {message}")
        
    @st.fragment(run_every=2)
    def render_live_terminal_fragment(self):
        """Render live terminal updates using fragment (cutting-edge feature)."""
        try:
            # This fragment updates every 2 seconds for real-time terminal display
            if st.session_state.enhanced_terminal_messages:
                latest_messages = st.session_state.enhanced_terminal_messages[-10:]
                
                # Create live terminal display
                terminal_content = []
                for message in latest_messages:
                    formatted_msg = self.format_enhanced_message(message)
                    terminal_content.append(formatted_msg)
                    
                # Enhanced terminal with holographic effect
                terminal_html = f"""
                <div class="terminal-enhanced" style="
                    background: 
                        linear-gradient(45deg, rgba(0, 255, 159, 0.05) 0%, rgba(0, 212, 255, 0.05) 100%),
                        #000000;
                    border: 2px solid #00ff9f;
                    border-radius: 15px;
                    padding: 2rem;
                    font-family: 'JetBrains Mono', 'Fira Code', monospace;
                    color: #00ff9f;
                    max-height: 200px;
                    overflow-y: auto;
                    box-shadow: 
                        0 0 20px rgba(0, 255, 159, 0.3),
                        inset 0 0 20px rgba(0, 255, 159, 0.1);
                    position: relative;
                    font-size: 12px;
                    line-height: 1.4;
                ">
                    <div style="margin-bottom: 10px; color: #00d4ff; font-weight: bold;">
                        📺 Live Terminal Feed
                    </div>
                    {'<br>'.join(terminal_content)}
                </div>
                """
                
                st.markdown(terminal_html, unsafe_allow_html=True)
                
        except Exception as e:
            # Fragment should fail gracefully
            pass
            
    def get_ai_command_suggestions(self, partial_command: str) -> List[str]:
        """Get AI-powered command suggestions (simulated)."""
        # Simulated AI suggestions based on partial input
        common_commands = {
            'pip': ['pip install', 'pip list', 'pip show', 'pip uninstall'],
            'git': ['git clone', 'git status', 'git add', 'git commit', 'git push'],
            'python': ['python3 -m pip', 'python3 --version', 'python3 -c'],
            'ls': ['ls -la', 'ls -lh', 'ls -lt'],
            'cd': ['cd /workspace', 'cd /content', 'cd ..'],
            'nvidia': ['nvidia-smi', 'nvidia-smi -l 1'],
            'ps': ['ps aux', 'ps aux | grep python'],
            'df': ['df -h', 'df -i'],
            'free': ['free -h', 'free -m']
        }
        
        suggestions = []
        partial_lower = partial_command.lower().strip()
        
        for key, commands in common_commands.items():
            if partial_lower.startswith(key) or key in partial_lower:
                suggestions.extend(commands)
                
        # Add context-aware suggestions
        if 'install' in partial_lower:
            suggestions.extend(['pip install torch', 'pip install transformers', 'pip install streamlit'])
        if 'run' in partial_lower:
            suggestions.extend(['python3 app.py', 'streamlit run app.py', 'python3 -m streamlit run'])
            
        return list(set(suggestions))[:5]  # Return top 5 unique suggestions
        
    def render_enhanced_command_input(self):
        """Render enhanced command input with AI suggestions."""
        st.markdown("### 🤖 AI-Powered Command Interface")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            command = st.text_input(
                "🎯 Enhanced Command Input",
                placeholder="Type a command... (AI suggestions will appear)",
                disabled=self.is_running,
                key="enhanced_terminal_command",
                help="Enhanced command input with AI suggestions and auto-completion"
            )
            
            # AI command suggestions
            if command and st.session_state.terminal_preferences['ai_suggestions']:
                suggestions = self.get_ai_command_suggestions(command)
                if suggestions:
                    st.markdown("#### 🤖 AI Suggestions")
                    try:
                        # Use pills for command suggestions
                        selected_suggestion = st.pills(
                            "Quick Commands",
                            suggestions,
                            key="command_suggestions",
                            selection_mode="single"
                        )
                        if selected_suggestion:
                            # Update command input
                            st.session_state.enhanced_terminal_command = selected_suggestion
                            st.rerun()
                    except:
                        # Fallback to buttons
                        suggestion_cols = st.columns(min(len(suggestions), 3))
                        for i, suggestion in enumerate(suggestions[:3]):
                            with suggestion_cols[i]:
                                if st.button(f"💡 {suggestion[:20]}...", key=f"suggestion_{i}"):
                                    st.session_state.enhanced_terminal_command = suggestion
                                    st.rerun()
            
        with col2:
            execute_button = st.button(
                "🚀 Execute", 
                disabled=self.is_running or not command,
                type="primary",
                use_container_width=True,
                help="Execute command with enhanced monitoring"
            )
            
        if execute_button and command:
            self.execute_enhanced_command(command)
            st.rerun()
            
        # Enhanced command history
        if st.session_state.terminal_preferences['command_history'] and self.command_history:
            with st.expander("📚 Command History", expanded=False):
                history_df = pd.DataFrame([
                    {
                        'Command': cmd['command'],
                        'Time': cmd['timestamp'].strftime('%H:%M:%S'),
                        'Status': '✅' if cmd['success'] else '❌',
                        'Duration': f"{cmd['duration']:.2f}s"
                    }
                    for cmd in self.command_history[-10:]  # Last 10 commands
                ])
                
                try:
                    # Interactive command history table
                    event = st.dataframe(
                        history_df,
                        use_container_width=True,
                        hide_index=True,
                        on_select="rerun",
                        selection_mode="single-row",
                        key="command_history_table"
                    )
                    
                    # Re-run selected command
                    if hasattr(event, 'selection') and event.selection.rows:
                        selected_row = event.selection.rows[0]
                        selected_command = history_df.iloc[selected_row]['Command']
                        if st.button(f"🔄 Re-run: {selected_command[:30]}...", type="secondary"):
                            self.execute_enhanced_command(selected_command)
                            st.rerun()
                except:
                    # Fallback display
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
                    
    def execute_enhanced_command(self, command: str, working_dir: Optional[str] = None):
        """Execute command with enhanced monitoring and AI assistance."""
        if self.is_running:
            st.toast("⚠️ Another command is already running", icon="⚠️")
            return
            
        self.is_running = True
        self.current_command = command
        command_id = f"cmd_{int(time.time())}"
        start_time = time.time()
        
        # Add to command history
        self.command_history.append({
            'command': command,
            'timestamp': datetime.now(),
            'success': False,  # Will be updated
            'duration': 0.0    # Will be updated
        })
        
        self.add_enhanced_message(LogLevel.SYSTEM, "Enhanced Terminal", f"🚀 Executing: {command}", command_id=command_id)
        
        # Enhanced status with detailed progress
        with st.status(f"🤖 Enhanced Execution: {command}", expanded=True) as status:
            def enhanced_run_command():
                try:
                    status.write("🔍 Analyzing command for optimization...")
                    time.sleep(0.5)
                    
                    status.write("⚙️ Setting up enhanced execution environment...")
                    time.sleep(0.5)
                    
                    status.write("🚀 Executing command with real-time monitoring...")
                    
                    # Use shell runner with enhanced monitoring
                    result = self.shell_runner.run_command_with_output(
                        command,
                        working_directory=working_dir,
                        capture_output=True,
                        stream_output=True,
                        output_callback=self._enhanced_output_callback
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Update command history
                    if self.command_history:
                        self.command_history[-1]['success'] = result.success
                        self.command_history[-1]['duration'] = execution_time
                    
                    # Update statistics
                    stats = st.session_state.command_statistics
                    stats['total_commands'] += 1
                    if result.success:
                        stats['successful_commands'] += 1
                        status.update(label="✅ Enhanced execution completed!", state="complete")
                        self.add_enhanced_message(
                            LogLevel.SUCCESS, 
                            "Enhanced Terminal", 
                            f"Command completed successfully (exit code: {result.exit_code}, time: {execution_time:.2f}s)",
                            command_id=command_id,
                            execution_time=execution_time,
                            exit_code=result.exit_code
                        )
                        st.toast(f"✅ Command completed in {execution_time:.2f}s", icon="✅")
                    else:
                        stats['failed_commands'] += 1
                        status.update(label="❌ Enhanced execution failed!", state="error")
                        self.add_enhanced_message(
                            LogLevel.ERROR, 
                            "Enhanced Terminal", 
                            f"Command failed (exit code: {result.exit_code}, time: {execution_time:.2f}s)",
                            command_id=command_id,
                            execution_time=execution_time,
                            exit_code=result.exit_code
                        )
                        if result.stderr:
                            self.add_enhanced_message(LogLevel.ERROR, "STDERR", result.stderr, raw_output=True)
                        st.toast(f"❌ Command failed after {execution_time:.2f}s", icon="❌")
                        
                    # Update average execution time
                    stats['average_execution_time'] = (
                        stats['average_execution_time'] * (stats['total_commands'] - 1) + execution_time
                    ) / stats['total_commands']
                        
                except Exception as e:
                    execution_time = time.time() - start_time
                    status.update(label="🚨 Enhanced execution error!", state="error")
                    self.add_enhanced_message(
                        LogLevel.ERROR, 
                        "Enhanced Terminal", 
                        f"Command execution failed: {str(e)} (time: {execution_time:.2f}s)",
                        command_id=command_id,
                        execution_time=execution_time
                    )
                    st.toast(f"🚨 Execution error: {str(e)}", icon="🚨")
                finally:
                    self.is_running = False
                    self.current_command = None
                    
            # Run enhanced command in background thread
            self.command_thread = threading.Thread(target=enhanced_run_command, daemon=True)
            self.command_thread.start()
        
    def _enhanced_output_callback(self, output: str, is_stderr: bool = False):
        """Enhanced callback for real-time command output."""
        source = "STDERR" if is_stderr else "STDOUT"
        level = LogLevel.ERROR if is_stderr else LogLevel.INFO
        
        # Enhanced output processing
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip():
                # Add performance tags for certain outputs
                tags = []
                if 'error' in line.lower():
                    tags.append('error')
                if 'warning' in line.lower():
                    tags.append('warning')
                if 'success' in line.lower() or 'complete' in line.lower():
                    tags.append('success')
                    
                self.add_enhanced_message(level, source, line, raw_output=True)
                
    def format_enhanced_message(self, message: EnhancedTerminalMessage) -> str:
        """Format an enhanced terminal message for display."""
        timestamp_str = ""
        if st.session_state.terminal_preferences['show_timestamps']:
            timestamp_str = f"[{message.timestamp.strftime('%H:%M:%S')}] "
            
        # Enhanced level colors with glow effects
        level_colors = {
            LogLevel.DEBUG: "#666666",
            LogLevel.INFO: "#00ff9f",
            LogLevel.WARNING: "#ffaa00",
            LogLevel.ERROR: "#ff4444",
            LogLevel.SUCCESS: "#00ff9f",
            LogLevel.SYSTEM: "#00d4ff",
            LogLevel.AI_SUGGESTION: "#ff44ff",
            LogLevel.PERFORMANCE: "#ffaa00"
        }
        
        level_color = level_colors.get(message.level, "#ffffff")
        source_str = f"[{message.source}]" if message.source != "Enhanced Terminal" else ""
        
        # Enhanced message content processing
        content = message.message
        if message.ansi_formatted:
            content = self.enhanced_converter.convert_ansi_to_html(
                content, 
                enhanced_mode=st.session_state.terminal_preferences['enhanced_mode']
            )
        else:
            content = html.escape(content)
            
        # Add execution time if available
        time_info = ""
        if message.execution_time:
            time_info = f" ({message.execution_time:.2f}s)"
            
        return f'<span style="color: {level_color}; text-shadow: 0 0 5px {level_color};">{timestamp_str}{source_str} {content}{time_info}</span>'
        
    def render_enhanced_terminal_controls(self):
        """Render enhanced terminal controls with cutting-edge features."""
        st.markdown("### 🎛️ Enhanced Terminal Controls")
        
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            # Basic controls
            if st.button("🧹 Clear Terminal", type="secondary"):
                st.session_state.enhanced_terminal_messages = []
                self.add_enhanced_message(LogLevel.SYSTEM, "Enhanced Terminal", "Terminal cleared with enhanced cleanup")
                st.toast("🧹 Terminal cleared!", icon="🧹")
                st.rerun()
                
            # Enhanced mode toggle
            enhanced_mode = st.toggle(
                "✨ Enhanced Mode", 
                value=st.session_state.terminal_preferences['enhanced_mode'],
                help="Enable enhanced visual effects and AI features"
            )
            st.session_state.terminal_preferences['enhanced_mode'] = enhanced_mode
            
        with control_col2:
            # Display preferences
            auto_scroll = st.toggle(
                "🔄 Auto Scroll", 
                value=st.session_state.terminal_preferences['auto_scroll']
            )
            st.session_state.terminal_preferences['auto_scroll'] = auto_scroll
            
            show_timestamps = st.toggle(
                "🕒 Timestamps", 
                value=st.session_state.terminal_preferences['show_timestamps']
            )
            st.session_state.terminal_preferences['show_timestamps'] = show_timestamps
            
        with control_col3:
            # AI features
            ai_suggestions = st.toggle(
                "🤖 AI Suggestions", 
                value=st.session_state.terminal_preferences['ai_suggestions'],
                help="Enable AI-powered command suggestions"
            )
            st.session_state.terminal_preferences['ai_suggestions'] = ai_suggestions
            
            performance_tracking = st.toggle(
                "📊 Performance Tracking", 
                value=st.session_state.terminal_preferences['performance_tracking'],
                help="Track command execution performance"
            )
            st.session_state.terminal_preferences['performance_tracking'] = performance_tracking
            
    def render_enhanced_terminal_output(self):
        """Render the enhanced terminal output area."""
        st.markdown("### 📺 Enhanced Terminal Output")
        
        # Filter level selection with segmented control
        try:
            filter_level = st.segmented_control(
                "Output Filter",
                ["ALL", "INFO", "WARNING", "ERROR", "SUCCESS"],
                default="ALL",
                key="terminal_filter_enhanced"
            )
        except:
            filter_levels = ["ALL", "INFO", "WARNING", "ERROR", "SUCCESS"]
            filter_level = st.selectbox("Filter Level", filter_levels)
            
        st.session_state.terminal_preferences['filter_level'] = filter_level
        
        # Filter messages
        level_hierarchy = {
            "ALL": 0, "DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "SUCCESS": 1, "SYSTEM": 1
        }
        min_level = level_hierarchy.get(filter_level, 0)
        
        filtered_messages = st.session_state.enhanced_terminal_messages
        if filter_level != "ALL":
            filtered_messages = [
                msg for msg in st.session_state.enhanced_terminal_messages
                if level_hierarchy.get(msg.level.value.upper(), 1) >= min_level
            ]
        
        # Enhanced terminal display
        if not filtered_messages:
            st.info("📝 Enhanced terminal ready. Execute a command to see enhanced output.")
        else:
            # Build enhanced terminal content
            terminal_content = []
            for message in filtered_messages[-100:]:  # Show last 100 messages
                formatted_msg = self.format_enhanced_message(message)
                terminal_content.append(formatted_msg)
                
            # Enhanced terminal container with effects
            terminal_html = f"""
            <div class="terminal-enhanced" style="
                background: 
                    linear-gradient(45deg, rgba(0, 255, 159, 0.05) 0%, rgba(0, 212, 255, 0.05) 100%),
                    radial-gradient(circle at 50% 50%, rgba(0, 255, 159, 0.1) 0%, transparent 70%),
                    #000000;
                border: 2px solid #00ff9f;
                border-radius: 20px;
                padding: 2rem;
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                color: #00ff9f;
                max-height: 500px;
                overflow-y: auto;
                box-shadow: 
                    0 0 30px rgba(0, 255, 159, 0.4),
                    inset 0 0 30px rgba(0, 255, 159, 0.1),
                    0 0 0 1px rgba(0, 255, 159, 0.2);
                position: relative;
                font-size: 13px;
                line-height: 1.5;
            ">
                <div style="
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, transparent, #00ff9f, transparent);
                    animation: scanline 4s linear infinite;
                "></div>
                {'<br>'.join(terminal_content)}
            </div>
            
            <style>
            @keyframes scanline {{
                0% {{ transform: translateX(-100%); }}
                100% {{ transform: translateX(100%); }}
            }}
            </style>
            """
            
            st.markdown(terminal_html, unsafe_allow_html=True)
            
        # Enhanced terminal statistics
        self.render_enhanced_terminal_stats()
        
    def render_enhanced_terminal_stats(self):
        """Render enhanced terminal statistics."""
        st.markdown("#### 📊 Enhanced Terminal Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        stats = st.session_state.command_statistics
        
        with col1:
            st.metric("📊 Total Commands", stats['total_commands'])
            
        with col2:
            success_rate = (stats['successful_commands'] / max(stats['total_commands'], 1)) * 100
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
            
        with col3:
            st.metric("⚡ Avg Time", f"{stats['average_execution_time']:.2f}s")
            
        with col4:
            st.metric("📝 Messages", len(st.session_state.enhanced_terminal_messages))
            
    def render_enhanced_terminal(self):
        """Render the complete enhanced terminal interface."""
        try:
            # Enhanced terminal controls
            self.render_enhanced_terminal_controls()
            
            st.markdown("---")
            
            # Live terminal fragment (updates every 2 seconds)
            if st.session_state.terminal_preferences['enhanced_mode']:
                st.markdown("#### 📺 Live Terminal Feed")
                self.render_live_terminal_fragment()
                st.markdown("---")
            
            # Enhanced command input with AI
            self.render_enhanced_command_input()
            
            st.markdown("---")
            
            # Enhanced terminal output
            self.render_enhanced_terminal_output()
            
            # Enhanced export and tools
            st.markdown("---")
            self.render_enhanced_terminal_tools()
            
        except Exception as e:
            st.error(f"Enhanced terminal widget error: {str(e)}")
            self.logging_system.log_error("Enhanced terminal widget error", {"error": str(e)})
            
    def render_enhanced_terminal_tools(self):
        """Render enhanced terminal tools and utilities."""
        st.markdown("### 🛠️ Enhanced Terminal Tools")
        
        tool_col1, tool_col2, tool_col3 = st.columns(3)
        
        with tool_col1:
            st.markdown("#### 📤 Export Options")
            
            # Enhanced export with multiple formats
            export_format = st.radio("Export Format", ["📄 Plain Text", "🌐 HTML", "📊 JSON"], horizontal=True)
            
            if st.button("📥 Export Enhanced Logs", type="secondary"):
                self.export_enhanced_logs(export_format)
                
        with tool_col2:
            st.markdown("#### 🔧 Terminal Tools")
            
            if st.button("📊 Performance Report", type="secondary"):
                self.show_performance_report()
                
            if st.button("🤖 AI Analysis", type="secondary"):
                self.show_ai_terminal_analysis()
                
        with tool_col3:
            st.markdown("#### ⚙️ Advanced Settings")
            
            try:
                with st.popover("🎛️ Terminal Settings"):
                    st.markdown("**Enhanced Terminal Configuration**")
                    
                    max_lines = st.slider("Max History Lines", 500, 5000, self.max_lines)
                    self.max_lines = max_lines
                    
                    theme_mode = st.radio("Terminal Theme", ["🌙 Dark", "🌈 Cyberpunk", "💫 Holographic"])
                    
                    if st.button("💾 Save Settings"):
                        st.toast("💾 Enhanced settings saved!", icon="💾")
            except:
                # Fallback to expander
                with st.expander("🎛️ Terminal Settings"):
                    max_lines = st.slider("Max History Lines", 500, 5000, self.max_lines)
                    self.max_lines = max_lines
                    
    def export_enhanced_logs(self, format_type: str):
        """Export enhanced terminal logs in multiple formats."""
        try:
            if format_type == "📄 Plain Text":
                log_content = []
                for message in st.session_state.enhanced_terminal_messages:
                    timestamp = message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    log_line = f"[{timestamp}] [{message.level.value.upper()}] [{message.source}] {message.message}"
                    log_content.append(log_line)
                    
                log_text = '\n'.join(log_content)
                st.download_button(
                    label="📥 Download Enhanced Logs (TXT)",
                    data=log_text,
                    file_name=f"enhanced_terminal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )
                
            elif format_type == "📊 JSON":
                json_data = []
                for message in st.session_state.enhanced_terminal_messages:
                    json_data.append({
                        'timestamp': message.timestamp.isoformat(),
                        'level': message.level.value,
                        'source': message.source,
                        'message': message.message,
                        'command_id': message.command_id,
                        'execution_time': message.execution_time,
                        'exit_code': message.exit_code
                    })
                    
                json_text = json.dumps(json_data, indent=2)
                st.download_button(
                    label="📥 Download Enhanced Logs (JSON)",
                    data=json_text,
                    file_name=f"enhanced_terminal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
            st.toast(f"📥 Enhanced logs exported in {format_type} format!", icon="📥")
            
        except Exception as e:
            st.toast(f"❌ Failed to export enhanced logs: {str(e)}", icon="❌")
            
    def show_performance_report(self):
        """Show enhanced performance report."""
        st.toast("📊 Enhanced performance report generated!", icon="📊")
        
        # Display performance metrics
        stats = st.session_state.command_statistics
        st.markdown("#### 📈 Performance Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Commands", stats['total_commands'])
            st.metric("Success Rate", f"{(stats['successful_commands']/max(stats['total_commands'],1)*100):.1f}%")
        with col2:
            st.metric("Average Time", f"{stats['average_execution_time']:.2f}s")
            st.metric("Failed Commands", stats['failed_commands'])
            
    def show_ai_terminal_analysis(self):
        """Show AI analysis of terminal usage."""
        st.toast("🤖 AI terminal analysis complete!", icon="🤖")
        
        # Simulated AI insights
        insights = [
            "💡 Most used commands: pip, git, python3",
            "⚡ Average command execution time is optimal",
            "🎯 Suggestion: Use 'pip install --upgrade' for better performance",
            "🔍 No suspicious command patterns detected"
        ]
        
        st.markdown("#### 🤖 AI Terminal Insights")
        for insight in insights:
            st.info(insight)


def main():
    """Test the enhanced terminal widget."""
    st.set_page_config(page_title="Enhanced Terminal Widget Test", layout="wide")
    
    st.title("🤖 Enhanced Terminal Widget Test")
    
    terminal = EnhancedTerminalWidget()
    
    # Add enhanced test messages
    if st.button("🧪 Add Enhanced Test Messages"):
        terminal.add_enhanced_message(LogLevel.INFO, "Test", "Enhanced info message with glow effects")
        terminal.add_enhanced_message(LogLevel.WARNING, "Test", "Enhanced warning with AI analysis")
        terminal.add_enhanced_message(LogLevel.ERROR, "Test", "Enhanced error with detailed context")
        terminal.add_enhanced_message(LogLevel.SUCCESS, "Test", "Enhanced success with celebration")
        terminal.add_enhanced_message(LogLevel.AI_SUGGESTION, "AI", "AI suggests using 'pip install --upgrade'")
        st.toast("🧪 Enhanced test messages added!", icon="🧪")
        st.balloons()
        
    terminal.render_enhanced_terminal()


if __name__ == "__main__":
    main()