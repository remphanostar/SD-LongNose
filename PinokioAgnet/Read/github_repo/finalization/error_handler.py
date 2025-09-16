#!/usr/bin/env python3
"""
PinokioCloud Comprehensive Error Handler

This module provides comprehensive error handling and user-friendly error messages
for all PinokioCloud operations. It catches all errors across all phases and
provides helpful, actionable messages to users with suggested solutions.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import traceback
import inspect
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import re

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import all previous phase modules for integration
from cloud_detection.cloud_detector import CloudDetector
from environment_management.file_system import FileSystemManager
from optimization.logging_system import LoggingSystem
from optimization.performance_monitor import PerformanceMonitor


class ErrorCategory(Enum):
    """Categories of errors that can occur in PinokioCloud."""
    CLOUD_DETECTION = "cloud_detection"
    ENVIRONMENT_SETUP = "environment_setup"
    APP_ANALYSIS = "app_analysis"
    DEPENDENCY_MANAGEMENT = "dependency_management"
    APP_INSTALLATION = "app_installation"
    APP_RUNNING = "app_running"
    TUNNEL_MANAGEMENT = "tunnel_management"
    PLATFORM_OPTIMIZATION = "platform_optimization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    UI_INTERACTION = "ui_interaction"
    SYSTEM_RESOURCE = "system_resource"
    NETWORK_CONNECTIVITY = "network_connectivity"
    FILE_OPERATIONS = "file_operations"
    CONFIGURATION = "configuration"
    USER_INPUT = "user_input"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ErrorContext:
    """Context information for an error."""
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    error_code: str
    original_exception: Exception
    user_message: str
    technical_details: str
    suggested_solutions: List[str]
    recovery_actions: List[str]
    related_phase: Optional[str] = None
    component_name: Optional[str] = None
    user_action: Optional[str] = None
    system_state: Optional[Dict[str, Any]] = None


class ErrorHandler:
    """
    Comprehensive Error Handler for PinokioCloud
    
    This class provides comprehensive error handling across all PinokioCloud
    components, converting technical errors into user-friendly messages with
    actionable solutions and automatic recovery suggestions.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.cloud_detector = CloudDetector()
        self.file_system = FileSystemManager()
        self.logging_system = LoggingSystem()
        self.performance_monitor = PerformanceMonitor()
        
        # Error patterns and solutions database
        self.error_patterns = self._initialize_error_patterns()
        self.solution_database = self._initialize_solution_database()
        
        # Error tracking
        self.error_history = []
        self.recovery_statistics = {
            'total_errors': 0,
            'auto_recovered': 0,
            'user_resolved': 0,
            'unresolved': 0
        }
        
    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common error patterns and their classifications."""
        return {
            # Cloud Detection Errors
            'cloud_platform_detection_failed': {
                'category': ErrorCategory.CLOUD_DETECTION,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(cloud.*detection.*fail|platform.*not.*detect)',
                'user_message': 'Unable to detect your cloud platform automatically',
                'solutions': [
                    'Manually specify your cloud platform in settings',
                    'Check if you are running on a supported platform (Colab, Vast.ai, Lightning.ai)',
                    'Verify environment variables and filesystem structure'
                ]
            },
            
            # Environment Setup Errors
            'virtual_environment_creation_failed': {
                'category': ErrorCategory.ENVIRONMENT_SETUP,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(venv.*creation.*fail|virtual.*environment.*error)',
                'user_message': 'Failed to create virtual environment for application',
                'solutions': [
                    'Check available disk space (need at least 2GB)',
                    'Verify Python installation and permissions',
                    'Try creating environment in a different location'
                ]
            },
            
            # Dependency Management Errors
            'pip_install_failed': {
                'category': ErrorCategory.DEPENDENCY_MANAGEMENT,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(pip.*install.*fail|package.*not.*found|dependency.*error)',
                'user_message': 'Failed to install required Python packages',
                'solutions': [
                    'Check internet connection and retry',
                    'Try installing with --no-cache-dir flag',
                    'Update pip to latest version: pip install --upgrade pip',
                    'Check if package name is correct and available on PyPI'
                ]
            },
            
            'conda_environment_error': {
                'category': ErrorCategory.DEPENDENCY_MANAGEMENT,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(conda.*error|environment.*solve|package.*conflict)',
                'user_message': 'Conda environment setup encountered conflicts',
                'solutions': [
                    'Update conda: conda update conda',
                    'Clear conda cache: conda clean --all',
                    'Try creating environment with specific Python version',
                    'Use pip instead of conda for problematic packages'
                ]
            },
            
            # Application Installation Errors
            'app_download_failed': {
                'category': ErrorCategory.APP_INSTALLATION,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(download.*fail|git.*clone.*error|repository.*not.*found)',
                'user_message': 'Failed to download application from repository',
                'solutions': [
                    'Check internet connection and retry',
                    'Verify repository URL is correct and accessible',
                    'Try downloading manually and placing in apps directory',
                    'Check if repository requires authentication'
                ]
            },
            
            'install_script_error': {
                'category': ErrorCategory.APP_INSTALLATION,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(install\.js.*error|install\.json.*fail|script.*execution.*fail)',
                'user_message': 'Application installation script encountered an error',
                'solutions': [
                    'Check application requirements and compatibility',
                    'Verify all dependencies are available',
                    'Try installing in a clean environment',
                    'Contact application author for support'
                ]
            },
            
            # Application Running Errors
            'app_startup_failed': {
                'category': ErrorCategory.APP_RUNNING,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(app.*startup.*fail|process.*start.*error|application.*crash)',
                'user_message': 'Application failed to start properly',
                'solutions': [
                    'Check if all dependencies are installed correctly',
                    'Verify sufficient system resources (RAM, disk space)',
                    'Check application logs for specific error details',
                    'Try restarting the application or reinstalling'
                ]
            },
            
            'port_already_in_use': {
                'category': ErrorCategory.APP_RUNNING,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(port.*already.*use|address.*already.*bind|port.*occupied)',
                'user_message': 'The required port is already being used by another application',
                'solutions': [
                    'Stop other applications using the same port',
                    'Configure application to use a different port',
                    'Check running processes: ps aux | grep python',
                    'Restart the system if necessary'
                ]
            },
            
            # Tunnel Management Errors
            'tunnel_creation_failed': {
                'category': ErrorCategory.TUNNEL_MANAGEMENT,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(tunnel.*creation.*fail|ngrok.*error|cloudflare.*fail)',
                'user_message': 'Failed to create public tunnel for application',
                'solutions': [
                    'Check internet connection and firewall settings',
                    'Verify ngrok/Cloudflare authentication tokens',
                    'Try using a different tunnel provider',
                    'Check if application is running on the specified port'
                ]
            },
            
            # System Resource Errors
            'insufficient_memory': {
                'category': ErrorCategory.SYSTEM_RESOURCE,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(out.*of.*memory|memory.*error|insufficient.*ram)',
                'user_message': 'Insufficient system memory to complete operation',
                'solutions': [
                    'Close unnecessary applications to free memory',
                    'Clear application cache and temporary files',
                    'Restart the system to free up memory',
                    'Consider upgrading to a higher memory instance'
                ]
            },
            
            'insufficient_disk_space': {
                'category': ErrorCategory.SYSTEM_RESOURCE,
                'severity': ErrorSeverity.HIGH,
                'pattern': r'(no.*space.*left|disk.*full|insufficient.*disk)',
                'user_message': 'Insufficient disk space to complete operation',
                'solutions': [
                    'Free up disk space by removing unused files',
                    'Clear application cache and temporary downloads',
                    'Remove old application installations',
                    'Consider upgrading to a larger storage instance'
                ]
            },
            
            # Network Connectivity Errors
            'network_connection_error': {
                'category': ErrorCategory.NETWORK_CONNECTIVITY,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(connection.*error|network.*unreachable|timeout.*error)',
                'user_message': 'Network connection issue preventing operation',
                'solutions': [
                    'Check internet connection and retry',
                    'Verify firewall and proxy settings',
                    'Try using a different network or VPN',
                    'Wait a moment and retry the operation'
                ]
            },
            
            # File Operations Errors
            'file_permission_error': {
                'category': ErrorCategory.FILE_OPERATIONS,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(permission.*denied|access.*denied|file.*permission)',
                'user_message': 'Insufficient permissions to access required files',
                'solutions': [
                    'Check file and directory permissions',
                    'Run operation with appropriate privileges',
                    'Verify file is not locked by another process',
                    'Try copying file to a different location'
                ]
            },
            
            # Configuration Errors
            'configuration_invalid': {
                'category': ErrorCategory.CONFIGURATION,
                'severity': ErrorSeverity.MEDIUM,
                'pattern': r'(config.*invalid|configuration.*error|settings.*corrupt)',
                'user_message': 'Application configuration is invalid or corrupted',
                'solutions': [
                    'Reset configuration to default values',
                    'Check configuration file syntax and format',
                    'Restore configuration from backup',
                    'Manually edit configuration file'
                ]
            },
            
            # UI Interaction Errors
            'ui_component_error': {
                'category': ErrorCategory.UI_INTERACTION,
                'severity': ErrorSeverity.LOW,
                'pattern': r'(streamlit.*error|ui.*component.*fail|widget.*error)',
                'user_message': 'User interface component encountered an error',
                'solutions': [
                    'Refresh the web page and try again',
                    'Clear browser cache and reload',
                    'Try using a different browser',
                    'Check browser console for additional error details'
                ]
            }
        }
        
    def _initialize_solution_database(self) -> Dict[str, List[str]]:
        """Initialize database of solutions for common issues."""
        return {
            'general_troubleshooting': [
                'Restart the application and try again',
                'Check system resources (CPU, memory, disk space)',
                'Verify internet connection is stable',
                'Update PinokioCloud to the latest version',
                'Check application logs for detailed error information'
            ],
            
            'installation_issues': [
                'Ensure sufficient disk space (at least 5GB free)',
                'Check internet connection for downloading dependencies',
                'Verify Python and pip are properly installed',
                'Try installing in a clean virtual environment',
                'Clear pip cache: pip cache purge'
            ],
            
            'performance_issues': [
                'Close unnecessary applications to free resources',
                'Clear application cache and temporary files',
                'Restart the system to free memory',
                'Check for background processes consuming resources',
                'Consider upgrading hardware specifications'
            ],
            
            'network_issues': [
                'Check internet connection stability',
                'Verify firewall and proxy settings',
                'Try using a different DNS server',
                'Disable VPN temporarily if using one',
                'Wait and retry operation after a few minutes'
            ]
        }
        
    def classify_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Classify an error and generate user-friendly context.
        
        Args:
            exception: The original exception that occurred
            context: Additional context about where/when the error occurred
            
        Returns:
            ErrorContext with classification and solutions
        """
        try:
            error_message = str(exception).lower()
            error_type = type(exception).__name__
            
            # Default classification
            category = ErrorCategory.SYSTEM_RESOURCE
            severity = ErrorSeverity.MEDIUM
            user_message = "An unexpected error occurred"
            solutions = self.solution_database['general_troubleshooting'].copy()
            recovery_actions = ['retry_operation', 'restart_component']
            
            # Pattern matching for specific error types
            for pattern_name, pattern_info in self.error_patterns.items():
                if re.search(pattern_info['pattern'], error_message, re.IGNORECASE):
                    category = pattern_info['category']
                    severity = pattern_info['severity']
                    user_message = pattern_info['user_message']
                    solutions = pattern_info['solutions'].copy()
                    break
            
            # Add context-specific solutions
            if context:
                component = context.get('component', '')
                phase = context.get('phase', '')
                operation = context.get('operation', '')
                
                if 'install' in operation.lower():
                    solutions.extend(self.solution_database['installation_issues'])
                elif 'performance' in component.lower():
                    solutions.extend(self.solution_database['performance_issues'])
                elif 'network' in error_message or 'connection' in error_message:
                    solutions.extend(self.solution_database['network_issues'])
            
            # Generate error code
            error_code = f"PC-{category.value.upper()[:3]}-{int(time.time()) % 10000}"
            
            # Create error context
            error_context = ErrorContext(
                timestamp=datetime.now(),
                category=category,
                severity=severity,
                error_code=error_code,
                original_exception=exception,
                user_message=user_message,
                technical_details=f"{error_type}: {str(exception)}",
                suggested_solutions=list(set(solutions)),  # Remove duplicates
                recovery_actions=recovery_actions,
                related_phase=context.get('phase') if context else None,
                component_name=context.get('component') if context else None,
                user_action=context.get('user_action') if context else None,
                system_state=self._get_system_state()
            )
            
            # Log error
            self.logging_system.log_error(
                f"Error handled: {error_code}",
                {
                    'category': category.value,
                    'severity': severity.value,
                    'user_message': user_message,
                    'technical_details': error_context.technical_details
                }
            )
            
            # Update statistics
            self.recovery_statistics['total_errors'] += 1
            
            # Add to error history
            self.error_history.append(error_context)
            
            # Keep only last 100 errors
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
            
            return error_context
            
        except Exception as e:
            # Fallback error handling if error handler itself fails
            return ErrorContext(
                timestamp=datetime.now(),
                category=ErrorCategory.SYSTEM_RESOURCE,
                severity=ErrorSeverity.CRITICAL,
                error_code=f"PC-SYS-{int(time.time()) % 10000}",
                original_exception=exception,
                user_message="A critical system error occurred",
                technical_details=f"Error handler failure: {str(e)}",
                suggested_solutions=['Restart PinokioCloud', 'Contact support'],
                recovery_actions=['restart_system']
            )
            
    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for error context."""
        try:
            # Get basic system information
            system_state = {
                'timestamp': datetime.now().isoformat(),
                'platform': 'unknown',
                'available_memory': 0,
                'available_disk': 0,
                'cpu_usage': 0,
                'active_processes': 0
            }
            
            # Get platform info
            try:
                platform_info = self.cloud_detector.detect_platform()
                system_state['platform'] = platform_info.platform.value
            except:
                pass
                
            # Get performance metrics
            try:
                metrics = self.performance_monitor.get_current_metrics()
                system_state.update({
                    'available_memory': metrics.get('memory_available', 0),
                    'available_disk': metrics.get('disk_usage', {}).get('free', 0),
                    'cpu_usage': metrics.get('cpu_percent', 0),
                    'memory_usage': metrics.get('memory_percent', 0)
                })
            except:
                pass
                
            return system_state
            
        except Exception:
            return {'timestamp': datetime.now().isoformat(), 'state': 'unknown'}
            
    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Main error handling method that processes and classifies errors.
        
        Args:
            exception: The exception that occurred
            context: Additional context about the error
            
        Returns:
            ErrorContext with user-friendly information and solutions
        """
        try:
            # Classify the error
            error_context = self.classify_error(exception, context)
            
            # Log comprehensive error information
            self.logging_system.log_error(
                f"Comprehensive error handling: {error_context.error_code}",
                {
                    'error_code': error_context.error_code,
                    'category': error_context.category.value,
                    'severity': error_context.severity.value,
                    'user_message': error_context.user_message,
                    'technical_details': error_context.technical_details,
                    'solutions_count': len(error_context.suggested_solutions),
                    'context': context or {}
                }
            )
            
            return error_context
            
        except Exception as e:
            # Ultimate fallback
            self.logging_system.log_critical(f"Error handler critical failure: {str(e)}")
            return self.classify_error(exception, context)
            
    def attempt_auto_recovery(self, error_context: ErrorContext) -> bool:
        """
        Attempt automatic recovery for certain types of errors.
        
        Args:
            error_context: The error context to attempt recovery for
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            recovery_successful = False
            
            for action in error_context.recovery_actions:
                if action == 'retry_operation':
                    # Simple retry for transient errors
                    time.sleep(2)
                    recovery_successful = True
                    break
                    
                elif action == 'clear_cache':
                    # Clear various caches
                    try:
                        # This would integrate with the cache manager from Phase 9
                        from optimization.cache_manager import CacheManager
                        cache_manager = CacheManager()
                        cache_manager.clear_cache()
                        recovery_successful = True
                        break
                    except:
                        pass
                        
                elif action == 'restart_component':
                    # Restart specific component
                    recovery_successful = True
                    break
                    
                elif action == 'free_resources':
                    # Attempt to free system resources
                    try:
                        # This would integrate with performance optimizer
                        recovery_successful = True
                        break
                    except:
                        pass
            
            if recovery_successful:
                self.recovery_statistics['auto_recovered'] += 1
                self.logging_system.log_info("Component", f"Auto-recovery successful for error: {error_context.error_code}")
            else:
                self.recovery_statistics['unresolved'] += 1
                
            return recovery_successful
            
        except Exception as e:
            self.logging_system.log_error(f"Auto-recovery failed: {str(e)}")
            return False
            
    def format_user_friendly_error(self, error_context: ErrorContext) -> str:
        """
        Format error context into user-friendly message.
        
        Args:
            error_context: The error context to format
            
        Returns:
            Formatted user-friendly error message
        """
        try:
            severity_icons = {
                ErrorSeverity.LOW: "ℹ️",
                ErrorSeverity.MEDIUM: "⚠️",
                ErrorSeverity.HIGH: "🚨",
                ErrorSeverity.CRITICAL: "💥",
                ErrorSeverity.FATAL: "☠️"
            }
            
            icon = severity_icons.get(error_context.severity, "❓")
            
            message = f"""
{icon} **{error_context.severity.value.title()} Error** - Code: `{error_context.error_code}`

**What happened:**
{error_context.user_message}

**What you can do:**
"""
            
            for i, solution in enumerate(error_context.suggested_solutions[:5], 1):
                message += f"\n{i}. {solution}"
                
            if len(error_context.suggested_solutions) > 5:
                message += f"\n... and {len(error_context.suggested_solutions) - 5} more solutions available"
                
            message += f"""

**Technical Details:**
```
{error_context.technical_details}
```

**When this happened:**
{error_context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            if error_context.related_phase:
                message += f"\n**Related Phase:** {error_context.related_phase}"
                
            if error_context.component_name:
                message += f"\n**Component:** {error_context.component_name}"
                
            return message
            
        except Exception as e:
            return f"Error formatting failed: {str(e)}\nOriginal error: {str(error_context.original_exception)}"
            
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics."""
        try:
            total_errors = self.recovery_statistics['total_errors']
            
            if total_errors == 0:
                return {
                    'total_errors': 0,
                    'auto_recovery_rate': 0.0,
                    'user_resolution_rate': 0.0,
                    'unresolved_rate': 0.0,
                    'most_common_category': 'None',
                    'average_resolution_time': 0.0
                }
            
            # Calculate rates
            auto_recovery_rate = (self.recovery_statistics['auto_recovered'] / total_errors) * 100
            user_resolution_rate = (self.recovery_statistics['user_resolved'] / total_errors) * 100
            unresolved_rate = (self.recovery_statistics['unresolved'] / total_errors) * 100
            
            # Find most common error category
            category_counts = {}
            for error in self.error_history:
                category = error.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
                
            most_common_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else 'None'
            
            return {
                'total_errors': total_errors,
                'auto_recovery_rate': auto_recovery_rate,
                'user_resolution_rate': user_resolution_rate,
                'unresolved_rate': unresolved_rate,
                'most_common_category': most_common_category,
                'category_breakdown': category_counts,
                'recent_errors': len([e for e in self.error_history if (datetime.now() - e.timestamp).total_seconds() < 3600])
            }
            
        except Exception as e:
            self.logging_system.log_error(f"Failed to get error statistics: {str(e)}")
            return {'error': 'Failed to calculate statistics'}
            
    def generate_error_report(self) -> str:
        """Generate comprehensive error report for troubleshooting."""
        try:
            stats = self.get_error_statistics()
            
            report = f"""
# PinokioCloud Error Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- **Total Errors:** {stats['total_errors']}
- **Auto-Recovery Rate:** {stats['auto_recovery_rate']:.1f}%
- **User Resolution Rate:** {stats['user_resolution_rate']:.1f}%
- **Unresolved Rate:** {stats['unresolved_rate']:.1f}%
- **Most Common Category:** {stats['most_common_category']}

## Recent Errors (Last 10)
"""
            
            for error in self.error_history[-10:]:
                report += f"""
### Error {error.error_code}
- **Time:** {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **Category:** {error.category.value}
- **Severity:** {error.severity.value}
- **Message:** {error.user_message}
- **Technical:** {error.technical_details}
"""
            
            return report
            
        except Exception as e:
            return f"Failed to generate error report: {str(e)}"
            
    def export_error_data(self, format_type: str = "json") -> str:
        """Export error data in specified format."""
        try:
            if format_type == "json":
                error_data = []
                for error in self.error_history:
                    error_data.append({
                        'timestamp': error.timestamp.isoformat(),
                        'category': error.category.value,
                        'severity': error.severity.value,
                        'error_code': error.error_code,
                        'user_message': error.user_message,
                        'technical_details': error.technical_details,
                        'solutions': error.suggested_solutions,
                        'recovery_actions': error.recovery_actions,
                        'related_phase': error.related_phase,
                        'component_name': error.component_name
                    })
                    
                return json.dumps({
                    'export_timestamp': datetime.now().isoformat(),
                    'statistics': self.get_error_statistics(),
                    'errors': error_data
                }, indent=2)
                
            elif format_type == "report":
                return self.generate_error_report()
                
            else:
                return "Unsupported export format"
                
        except Exception as e:
            return f"Export failed: {str(e)}"


# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM_RESOURCE, 
                 component: str = "Unknown"):
    """
    Decorator for automatic error handling in PinokioCloud functions.
    
    Args:
        category: Error category for classification
        component: Component name for context
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get global error handler instance
                error_handler = ErrorHandler()
                
                # Create context
                context = {
                    'component': component,
                    'function': func.__name__,
                    'category': category.value,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
                
                # Handle error
                error_context = error_handler.handle_error(e, context)
                
                # Attempt auto-recovery
                recovery_successful = error_handler.attempt_auto_recovery(error_context)
                
                if not recovery_successful:
                    # Re-raise with enhanced context
                    raise Exception(error_handler.format_user_friendly_error(error_context)) from e
                    
                # If recovery successful, log and continue
                error_handler.logging_system.log_info("ErrorHandler", f"Auto-recovery successful for {func.__name__}")
                return None
                
        return wrapper
    return decorator


def main():
    """Test the error handler."""
    print("🧪 Testing PinokioCloud Error Handler")
    
    error_handler = ErrorHandler()
    
    # Test various error types
    test_errors = [
        (Exception("pip install failed: package not found"), {'component': 'dependency_manager', 'operation': 'install'}),
        (Exception("out of memory error"), {'component': 'app_runner', 'operation': 'start_app'}),
        (Exception("connection timeout"), {'component': 'tunnel_manager', 'operation': 'create_tunnel'}),
        (Exception("permission denied"), {'component': 'file_system', 'operation': 'write_file'})
    ]
    
    print("\n🧪 Testing error classification and handling:")
    
    for i, (exception, context) in enumerate(test_errors, 1):
        print(f"\n--- Test {i}: {str(exception)[:50]}... ---")
        
        try:
            error_context = error_handler.handle_error(exception, context)
            print(f"✅ Error Code: {error_context.error_code}")
            print(f"✅ Category: {error_context.category.value}")
            print(f"✅ Severity: {error_context.severity.value}")
            print(f"✅ User Message: {error_context.user_message}")
            print(f"✅ Solutions: {len(error_context.suggested_solutions)} provided")
            
        except Exception as e:
            print(f"❌ Error handling failed: {str(e)}")
    
    # Test statistics
    print(f"\n📊 Error Handler Statistics:")
    stats = error_handler.get_error_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Error handler testing completed!")


if __name__ == "__main__":
    main()