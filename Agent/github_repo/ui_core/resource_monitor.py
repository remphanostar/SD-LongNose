#!/usr/bin/env python3
"""
PinokioCloud Core Resource Monitor

This module provides core real-time system resource monitoring with modern
Streamlit features including st.metric, st.progress, st.plotly_chart, and
intelligent alerting for comprehensive system health monitoring.

Author: PinokioCloud Development Team
Version: 1.0.0 (Core)
"""

import os
import sys
import time
import threading
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import psutil
import json

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

from optimization.performance_monitor import PerformanceMonitor
from cloud_detection.cloud_detector import CloudDetector
from optimization.logging_system import LoggingSystem


class AlertLevel(Enum):
    """Resource alert levels."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    DANGER = "danger"


@dataclass
class ResourceAlert:
    """Represents a resource alert."""
    level: AlertLevel
    resource: str
    message: str
    timestamp: datetime
    threshold: float
    current_value: float


class ResourceMonitor:
    """
    Core Real-time Resource Monitor for PinokioCloud
    
    This class provides essential system resource monitoring with modern
    Streamlit features including real-time metrics, interactive charts,
    and intelligent alerting systems.
    """
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        """
        Initialize the resource monitor.
        
        Args:
            performance_monitor: Performance monitoring system
        """
        self.performance_monitor = performance_monitor
        self.cloud_detector = CloudDetector()
        self.logging_system = LoggingSystem()
        
        # Initialize session state
        if 'resource_history' not in st.session_state:
            st.session_state.resource_history = []
        if 'resource_alerts' not in st.session_state:
            st.session_state.resource_alerts = []
        if 'monitoring_enabled' not in st.session_state:
            st.session_state.monitoring_enabled = True
        if 'auto_refresh_interval' not in st.session_state:
            st.session_state.auto_refresh_interval = 5
        if 'alert_thresholds' not in st.session_state:
            st.session_state.alert_thresholds = {
                'cpu_warning': 80.0,
                'cpu_critical': 95.0,
                'memory_warning': 85.0,
                'memory_critical': 95.0,
                'disk_warning': 90.0,
                'disk_critical': 98.0,
                'gpu_warning': 85.0,
                'gpu_critical': 95.0
            }
            
        # Get platform info
        self.platform_info = self.cloud_detector.detect_platform()
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            return self.performance_monitor.get_current_metrics()
        except Exception as e:
            self.logging_system.log_error("Failed to get current metrics", {"error": str(e)})
            return {}
            
    def update_resource_history(self):
        """Update resource history with current metrics."""
        try:
            metrics = self.get_current_metrics()
            if metrics:
                # Add timestamp
                metrics['timestamp'] = datetime.now()
                
                # Add to history
                st.session_state.resource_history.append(metrics)
                
                # Keep only last 100 entries (for performance)
                if len(st.session_state.resource_history) > 100:
                    st.session_state.resource_history = st.session_state.resource_history[-100:]
                    
                # Check for alerts
                self.check_resource_alerts(metrics)
                
        except Exception as e:
            self.logging_system.log_error("Failed to update resource history", {"error": str(e)})
            
    def check_resource_alerts(self, metrics: Dict[str, Any]):
        """Check for resource alerts based on thresholds."""
        try:
            alerts = []
            thresholds = st.session_state.alert_thresholds
            
            # CPU alerts
            cpu_percent = metrics.get('cpu_percent', 0)
            if cpu_percent >= thresholds['cpu_critical']:
                alerts.append(ResourceAlert(
                    level=AlertLevel.CRITICAL,
                    resource="CPU",
                    message=f"CPU usage critically high: {cpu_percent:.1f}%",
                    timestamp=datetime.now(),
                    threshold=thresholds['cpu_critical'],
                    current_value=cpu_percent
                ))
            elif cpu_percent >= thresholds['cpu_warning']:
                alerts.append(ResourceAlert(
                    level=AlertLevel.WARNING,
                    resource="CPU",
                    message=f"CPU usage high: {cpu_percent:.1f}%",
                    timestamp=datetime.now(),
                    threshold=thresholds['cpu_warning'],
                    current_value=cpu_percent
                ))
                
            # Memory alerts
            memory_percent = metrics.get('memory_percent', 0)
            if memory_percent >= thresholds['memory_critical']:
                alerts.append(ResourceAlert(
                    level=AlertLevel.CRITICAL,
                    resource="Memory",
                    message=f"Memory usage critically high: {memory_percent:.1f}%",
                    timestamp=datetime.now(),
                    threshold=thresholds['memory_critical'],
                    current_value=memory_percent
                ))
            elif memory_percent >= thresholds['memory_warning']:
                alerts.append(ResourceAlert(
                    level=AlertLevel.WARNING,
                    resource="Memory",
                    message=f"Memory usage high: {memory_percent:.1f}%",
                    timestamp=datetime.now(),
                    threshold=thresholds['memory_warning'],
                    current_value=memory_percent
                ))
                
            # Add new alerts to session state
            st.session_state.resource_alerts.extend(alerts)
            
            # Keep only last 20 alerts
            if len(st.session_state.resource_alerts) > 20:
                st.session_state.resource_alerts = st.session_state.resource_alerts[-20:]
                
            # Show toast notifications for new alerts
            for alert in alerts:
                if alert.level == AlertLevel.CRITICAL:
                    st.toast(f"🚨 {alert.message}", icon="🚨")
                elif alert.level == AlertLevel.WARNING:
                    st.toast(f"⚠️ {alert.message}", icon="⚠️")
                
        except Exception as e:
            self.logging_system.log_error("Failed to check resource alerts", {"error": str(e)})
            
    def render_system_overview(self):
        """Render system overview with modern metrics."""
        st.markdown("### 🖥️ System Overview")
        
        # Get current metrics
        metrics = self.get_current_metrics()
        
        if not metrics:
            st.error("Unable to retrieve system metrics")
            return
            
        # Platform information with modern metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌐 Platform", self.platform_info.platform.value.title())
            
        with col2:
            cpu_count = metrics.get('cpu_count', 0)
            st.metric("🔧 CPU Cores", cpu_count)
            
        with col3:
            memory_total = metrics.get('memory_total', 0) / (1024**3)  # Convert to GB
            st.metric("💾 Total RAM", f"{memory_total:.1f} GB")
            
        with col4:
            disk_total = metrics.get('disk_usage', {}).get('total', 0) / (1024**3)  # Convert to GB
            st.metric("💿 Total Disk", f"{disk_total:.1f} GB")
            
    def render_real_time_metrics(self):
        """Render real-time resource metrics with modern Streamlit features."""
        st.markdown("### 📊 Real-time Metrics")
        
        # Get current metrics
        metrics = self.get_current_metrics()
        
        if not metrics:
            st.warning("No metrics available")
            return
            
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        # CPU Metrics
        with col1:
            cpu_percent = metrics.get('cpu_percent', 0)
            cpu_delta = None
            if len(st.session_state.resource_history) > 1:
                prev_cpu = st.session_state.resource_history[-2].get('cpu_percent', 0)
                cpu_delta = cpu_percent - prev_cpu
                
            st.metric(
                label="🔧 CPU Usage",
                value=f"{cpu_percent:.1f}%",
                delta=f"{cpu_delta:.1f}%" if cpu_delta is not None else None,
                help="Current CPU utilization percentage"
            )
            
            # CPU Progress bar with color coding
            if cpu_percent >= 90:
                st.error(f"🔥 Critical: {cpu_percent:.1f}%")
            elif cpu_percent >= 70:
                st.warning(f"⚠️ High: {cpu_percent:.1f}%")
            else:
                st.success(f"✅ Normal: {cpu_percent:.1f}%")
                
            st.progress(min(cpu_percent / 100, 1.0))
            
        # Memory Metrics
        with col2:
            memory_percent = metrics.get('memory_percent', 0)
            memory_used = metrics.get('memory_used', 0) / (1024**3)  # Convert to GB
            memory_delta = None
            if len(st.session_state.resource_history) > 1:
                prev_memory = st.session_state.resource_history[-2].get('memory_percent', 0)
                memory_delta = memory_percent - prev_memory
                
            st.metric(
                label="💾 Memory Usage",
                value=f"{memory_percent:.1f}%",
                delta=f"{memory_delta:.1f}%" if memory_delta is not None else None,
                help="Current memory utilization percentage"
            )
            
            # Memory status with color coding
            if memory_percent >= 90:
                st.error(f"🔥 Critical: {memory_used:.1f} GB")
            elif memory_percent >= 70:
                st.warning(f"⚠️ High: {memory_used:.1f} GB")
            else:
                st.success(f"✅ Normal: {memory_used:.1f} GB")
                
            st.progress(min(memory_percent / 100, 1.0))
            
        # Disk Metrics
        with col3:
            disk_usage = metrics.get('disk_usage', {})
            disk_percent = disk_usage.get('percent', 0)
            disk_used = disk_usage.get('used', 0) / (1024**3)  # Convert to GB
            disk_delta = None
            if len(st.session_state.resource_history) > 1:
                prev_disk = st.session_state.resource_history[-2].get('disk_usage', {}).get('percent', 0)
                disk_delta = disk_percent - prev_disk
                
            st.metric(
                label="💿 Disk Usage",
                value=f"{disk_percent:.1f}%",
                delta=f"{disk_delta:.1f}%" if disk_delta is not None else None,
                help="Current disk space utilization"
            )
            
            # Disk status
            if disk_percent >= 95:
                st.error(f"🔥 Critical: {disk_used:.1f} GB")
            elif disk_percent >= 80:
                st.warning(f"⚠️ High: {disk_used:.1f} GB")
            else:
                st.success(f"✅ Normal: {disk_used:.1f} GB")
                
            st.progress(min(disk_percent / 100, 1.0))
            
        # GPU Metrics (if available)
        with col4:
            gpu_info = metrics.get('gpu_info', {})
            if gpu_info and 'name' in gpu_info:
                gpu_utilization = gpu_info.get('utilization', 0)
                
                st.metric(
                    label="🎮 GPU Usage",
                    value=f"{gpu_utilization:.1f}%",
                    help="Current GPU utilization percentage"
                )
                
                # GPU status
                gpu_name = gpu_info.get('name', 'Unknown GPU')[:15] + "..."
                if gpu_utilization >= 90:
                    st.error(f"🔥 {gpu_name}")
                elif gpu_utilization >= 70:
                    st.warning(f"⚠️ {gpu_name}")
                else:
                    st.success(f"✅ {gpu_name}")
                    
                st.progress(min(gpu_utilization / 100, 1.0))
            else:
                st.metric(
                    label="🎮 GPU",
                    value="Not Available",
                    help="No GPU detected or monitoring not available"
                )
                st.info("No GPU detected")
                
    def render_resource_charts(self):
        """Render interactive resource usage charts with Plotly."""
        st.markdown("### 📈 Resource Usage History")
        
        if len(st.session_state.resource_history) < 2:
            st.info("📊 Collecting data... Please wait for more data points.")
            return
            
        try:
            # Prepare data for charts
            history_df = pd.DataFrame(st.session_state.resource_history)
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            
            # Create tabs for different chart types
            overview_tab, detailed_tab = st.tabs(["📊 Overview", "🔍 Detailed"])
            
            with overview_tab:
                # Combined overview chart with modern Plotly styling
                fig = go.Figure()
                
                # Add CPU trace
                fig.add_trace(go.Scatter(
                    x=history_df['timestamp'],
                    y=history_df['cpu_percent'],
                    mode='lines+markers',
                    name='CPU %',
                    line=dict(color='#ff6b6b', width=3),
                    marker=dict(size=6),
                    hovertemplate='<b>CPU:</b> %{y:.1f}%<br><b>Time:</b> %{x}<extra></extra>'
                ))
                
                # Add Memory trace
                fig.add_trace(go.Scatter(
                    x=history_df['timestamp'],
                    y=history_df['memory_percent'],
                    mode='lines+markers',
                    name='Memory %',
                    line=dict(color='#4ecdc4', width=3),
                    marker=dict(size=6),
                    hovertemplate='<b>Memory:</b> %{y:.1f}%<br><b>Time:</b> %{x}<extra></extra>'
                ))
                
                # Add Disk trace if available
                if 'disk_usage' in history_df.columns:
                    disk_percents = [d.get('percent', 0) if isinstance(d, dict) else 0 for d in history_df['disk_usage']]
                    fig.add_trace(go.Scatter(
                        x=history_df['timestamp'],
                        y=disk_percents,
                        mode='lines+markers',
                        name='Disk %',
                        line=dict(color='#45b7d1', width=3),
                        marker=dict(size=6),
                        hovertemplate='<b>Disk:</b> %{y:.1f}%<br><b>Time:</b> %{x}<extra></extra>'
                    ))
                
                fig.update_layout(
                    title={
                        'text': "System Resource Usage Overview",
                        'x': 0.5,
                        'font': {'size': 20, 'color': '#00ff9f'}
                    },
                    xaxis_title="Time",
                    yaxis_title="Usage Percentage",
                    hovermode='x unified',
                    height=400,
                    showlegend=True,
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ffffff'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            with detailed_tab:
                # Detailed charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # CPU Chart
                    fig_cpu = px.area(
                        history_df, 
                        x='timestamp', 
                        y='cpu_percent',
                        title='CPU Usage Over Time',
                        labels={'cpu_percent': 'CPU Usage (%)', 'timestamp': 'Time'}
                    )
                    fig_cpu.update_traces(fill='tonexty', fillcolor='rgba(255, 107, 107, 0.3)', line_color='#ff6b6b')
                    fig_cpu.update_layout(height=300, template='plotly_dark')
                    st.plotly_chart(fig_cpu, use_container_width=True)
                    
                with col2:
                    # Memory Chart
                    fig_memory = px.area(
                        history_df, 
                        x='timestamp', 
                        y='memory_percent',
                        title='Memory Usage Over Time',
                        labels={'memory_percent': 'Memory Usage (%)', 'timestamp': 'Time'}
                    )
                    fig_memory.update_traces(fill='tonexty', fillcolor='rgba(78, 205, 196, 0.3)', line_color='#4ecdc4')
                    fig_memory.update_layout(height=300, template='plotly_dark')
                    st.plotly_chart(fig_memory, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Failed to render charts: {str(e)}")
            self.logging_system.log_error("Chart rendering failed", {"error": str(e)})
            
    def render_alerts_panel(self):
        """Render resource alerts panel with modern styling."""
        st.markdown("### 🚨 Resource Alerts")
        
        if not st.session_state.resource_alerts:
            st.success("✅ No active alerts - all systems operating normally")
            return
            
        # Group alerts by level
        critical_alerts = [a for a in st.session_state.resource_alerts if a.level == AlertLevel.CRITICAL]
        warning_alerts = [a for a in st.session_state.resource_alerts if a.level == AlertLevel.WARNING]
        
        # Display critical alerts
        if critical_alerts:
            st.error(f"🚨 **{len(critical_alerts)} Critical Alert(s)**")
            for alert in critical_alerts[-3:]:  # Show last 3 critical alerts
                with st.expander(f"🚨 CRITICAL: {alert.resource} - {alert.timestamp.strftime('%H:%M:%S')}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Current Value", f"{alert.current_value:.1f}%")
                        st.metric("Threshold", f"{alert.threshold}%")
                    with col2:
                        st.markdown(f"**Message:** {alert.message}")
                        st.markdown(f"**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
        # Display warning alerts
        if warning_alerts:
            st.warning(f"⚠️ **{len(warning_alerts)} Warning(s)**")
            for alert in warning_alerts[-2:]:  # Show last 2 warnings
                with st.expander(f"⚠️ WARNING: {alert.resource} - {alert.timestamp.strftime('%H:%M:%S')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Current Value", f"{alert.current_value:.1f}%")
                        st.metric("Threshold", f"{alert.threshold}%")
                    with col2:
                        st.markdown(f"**Message:** {alert.message}")
                        st.markdown(f"**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
        # Clear alerts button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear All Alerts", type="secondary"):
                st.session_state.resource_alerts = []
                st.toast("✅ All alerts cleared!", icon="🧹")
                st.rerun()
        with col2:
            if st.button("🔄 Check Resources", type="primary"):
                self.update_resource_history()
                st.toast("🔄 Resources checked!", icon="🔄")
                st.rerun()
                
    def render_settings_panel(self):
        """Render monitoring settings panel with modern controls."""
        with st.expander("⚙️ Monitoring Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔄 Auto-Refresh")
                monitoring_enabled = st.toggle(
                    "Enable monitoring",
                    value=st.session_state.monitoring_enabled,
                    help="Enable automatic resource monitoring"
                )
                st.session_state.monitoring_enabled = monitoring_enabled
                
                if monitoring_enabled:
                    refresh_interval = st.slider(
                        "Refresh interval (seconds)",
                        min_value=1,
                        max_value=60,
                        value=st.session_state.auto_refresh_interval,
                        help="How often to refresh resource data"
                    )
                    st.session_state.auto_refresh_interval = refresh_interval
                    
            with col2:
                st.markdown("#### 🚨 Alert Thresholds")
                
                # CPU thresholds
                cpu_warning = st.slider(
                    "CPU Warning (%)",
                    min_value=50,
                    max_value=100,
                    value=int(st.session_state.alert_thresholds['cpu_warning']),
                    help="CPU usage threshold for warnings"
                )
                cpu_critical = st.slider(
                    "CPU Critical (%)",
                    min_value=cpu_warning,
                    max_value=100,
                    value=int(st.session_state.alert_thresholds['cpu_critical']),
                    help="CPU usage threshold for critical alerts"
                )
                
                # Memory thresholds
                memory_warning = st.slider(
                    "Memory Warning (%)",
                    min_value=50,
                    max_value=100,
                    value=int(st.session_state.alert_thresholds['memory_warning']),
                    help="Memory usage threshold for warnings"
                )
                memory_critical = st.slider(
                    "Memory Critical (%)",
                    min_value=memory_warning,
                    max_value=100,
                    value=int(st.session_state.alert_thresholds['memory_critical']),
                    help="Memory usage threshold for critical alerts"
                )
                
                # Update thresholds
                st.session_state.alert_thresholds.update({
                    'cpu_warning': float(cpu_warning),
                    'cpu_critical': float(cpu_critical),
                    'memory_warning': float(memory_warning),
                    'memory_critical': float(memory_critical)
                })
                
    def render_monitor(self):
        """Render the complete resource monitor interface."""
        try:
            # Update resource history if monitoring is enabled
            if st.session_state.monitoring_enabled:
                self.update_resource_history()
                
            # Render all components
            self.render_system_overview()
            
            st.markdown("---")
            
            self.render_real_time_metrics()
            
            st.markdown("---")
            
            self.render_resource_charts()
            
            st.markdown("---")
            
            self.render_alerts_panel()
            
            st.markdown("---")
            
            self.render_settings_panel()
            
            # Auto-refresh functionality with modern approach
            if st.session_state.monitoring_enabled:
                # Use rerun for auto-refresh
                time.sleep(st.session_state.auto_refresh_interval)
                st.rerun()
                
        except Exception as e:
            st.error(f"Resource monitor error: {str(e)}")
            st.toast(f"❌ Monitor error: {str(e)}", icon="❌")
            self.logging_system.log_error("Resource monitor error", {"error": str(e)})


def main():
    """Test the core resource monitor."""
    st.set_page_config(page_title="Core Resource Monitor Test", layout="wide")
    
    st.title("📊 Core Resource Monitor Test")
    
    # Mock performance monitor for testing
    class MockPerformanceMonitor:
        def get_current_metrics(self):
            import random
            return {
                'cpu_percent': random.uniform(10, 90),
                'cpu_count': 4,
                'memory_percent': random.uniform(20, 80),
                'memory_total': 16 * 1024**3,  # 16GB
                'memory_used': random.uniform(2, 12) * 1024**3,
                'disk_usage': {
                    'total': 100 * 1024**3,  # 100GB
                    'used': random.uniform(20, 80) * 1024**3,
                    'free': random.uniform(20, 80) * 1024**3,
                    'percent': random.uniform(20, 80)
                },
                'gpu_info': {
                    'name': 'NVIDIA Tesla T4',
                    'utilization': random.uniform(0, 100),
                    'memory_percent': random.uniform(10, 90)
                }
            }
    
    mock_perf_monitor = MockPerformanceMonitor()
    monitor = ResourceMonitor(mock_perf_monitor)
    monitor.render_monitor()


if __name__ == "__main__":
    main()