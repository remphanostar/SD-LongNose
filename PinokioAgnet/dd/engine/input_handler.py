#!/usr/bin/env python3
"""
PinokioCloud Input Handler

This module handles user input and forms during application installation.
It provides comprehensive input collection, validation, and form management.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import previous phase modules
sys.path.append('/workspace/github_repo')
from environment_management.variable_system import VariableSystem
from environment_management.json_handler import JSONHandler


class InputType(Enum):
    """Enumeration of input types."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    FILE = "file"
    DIRECTORY = "directory"
    URL = "url"
    EMAIL = "email"
    PASSWORD = "password"
    TEXTAREA = "textarea"
    RANGE = "range"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    COLOR = "color"


class ValidationRule(Enum):
    """Enumeration of validation rules."""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL = "email"
    URL = "url"
    FILE_EXISTS = "file_exists"
    DIRECTORY_EXISTS = "directory_exists"
    CUSTOM = "custom"


class FormStatus(Enum):
    """Enumeration of form statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InputField:
    """Input field definition."""
    field_id: str
    field_type: InputType
    label: str
    description: str = ""
    placeholder: str = ""
    default_value: Any = None
    required: bool = False
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    options: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormSection:
    """Form section definition."""
    section_id: str
    title: str
    description: str = ""
    fields: List[InputField] = field(default_factory=list)
    order: int = 0
    visible: bool = True
    dependencies: List[str] = field(default_factory=list)


@dataclass
class FormDefinition:
    """Complete form definition."""
    form_id: str
    title: str
    description: str = ""
    sections: List[FormSection] = field(default_factory=list)
    submit_button_text: str = "Submit"
    cancel_button_text: str = "Cancel"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Input validation result."""
    is_valid: bool
    field_id: str
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class FormResult:
    """Form submission result."""
    success: bool
    form_id: str
    submitted_data: Dict[str, Any] = field(default_factory=dict)
    validation_results: List[ValidationResult] = field(default_factory=list)
    submission_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class InputHandler:
    """
    Handles user input and forms during application installation.
    
    Provides comprehensive input collection including:
    - Dynamic form generation and management
    - Input validation and error handling
    - User input collection and processing
    - Form state management and persistence
    - Conditional field display and dependencies
    - Input sanitization and security
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the input handler.
        
        Args:
            base_path: Base path for input operations
        """
        self.base_path = base_path
        
        # Initialize components
        self.variable_system = VariableSystem(base_path)
        self.json_handler = JSONHandler(base_path)
        
        # Form management
        self.active_forms: Dict[str, FormDefinition] = {}
        self.form_responses: Dict[str, FormResult] = {}
        self.form_templates: Dict[str, FormDefinition] = {}
        
        # Input validation
        self.validation_functions: Dict[str, callable] = {}
        self._setup_default_validation()
        
        # Progress callback
        self.progress_callback = None
        
        # Ensure forms directory exists
        os.makedirs(os.path.join(base_path, "forms"), exist_ok=True)
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def create_form(self, form_definition: FormDefinition) -> bool:
        """
        Create a new form.
        
        Args:
            form_definition: Form definition
            
        Returns:
            bool: True if form created successfully
        """
        try:
            self.active_forms[form_definition.form_id] = form_definition
            self._update_progress(f"Created form: {form_definition.form_id}")
            return True
        
        except Exception as e:
            return False
    
    def create_form_from_template(self, template_id: str, form_id: str, 
                                 customizations: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create form from template.
        
        Args:
            template_id: Template ID
            form_id: New form ID
            customizations: Customizations to apply
            
        Returns:
            bool: True if form created successfully
        """
        try:
            if template_id not in self.form_templates:
                return False
            
            template = self.form_templates[template_id]
            
            # Create new form based on template
            new_form = FormDefinition(
                form_id=form_id,
                title=template.title,
                description=template.description,
                sections=template.sections.copy(),
                submit_button_text=template.submit_button_text,
                cancel_button_text=template.cancel_button_text,
                metadata=template.metadata.copy()
            )
            
            # Apply customizations
            if customizations:
                if 'title' in customizations:
                    new_form.title = customizations['title']
                if 'description' in customizations:
                    new_form.description = customizations['description']
                if 'sections' in customizations:
                    new_form.sections = customizations['sections']
            
            self.active_forms[form_id] = new_form
            self._update_progress(f"Created form from template: {form_id}")
            return True
        
        except Exception as e:
            return False
    
    def create_installation_form(self, app_name: str, app_profile: Dict[str, Any]) -> str:
        """
        Create installation form for an application.
        
        Args:
            app_name: Name of the application
            app_profile: Application profile
            
        Returns:
            str: Form ID
        """
        try:
            form_id = f"install_{app_name}"
            
            # Create form sections
            sections = []
            
            # Basic Configuration Section
            basic_section = FormSection(
                section_id="basic_config",
                title="Basic Configuration",
                description="Configure basic application settings",
                order=1
            )
            
            # Add fields based on app profile
            if app_profile.get('category') in ['LLM', 'TEXT']:
                basic_section.fields.extend([
                    InputField(
                        field_id="model_name",
                        field_type=InputType.SELECT,
                        label="Model Name",
                        description="Select the model to use",
                        required=True,
                        options=[
                            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
                            {"value": "gpt-4", "label": "GPT-4"},
                            {"value": "claude-3", "label": "Claude 3"},
                            {"value": "llama-2", "label": "Llama 2"}
                        ]
                    ),
                    InputField(
                        field_id="max_tokens",
                        field_type=InputType.NUMBER,
                        label="Max Tokens",
                        description="Maximum number of tokens to generate",
                        default_value=1000,
                        required=True,
                        validation_rules=[
                            {"rule": ValidationRule.MIN_VALUE, "value": 1},
                            {"rule": ValidationRule.MAX_VALUE, "value": 4000}
                        ]
                    )
                ])
            
            if app_profile.get('category') in ['IMAGE', 'VIDEO']:
                basic_section.fields.extend([
                    InputField(
                        field_id="gpu_type",
                        field_type=InputType.SELECT,
                        label="GPU Type",
                        description="Select the GPU to use",
                        required=True,
                        options=[
                            {"value": "T4", "label": "T4 (16GB)"},
                            {"value": "V100", "label": "V100 (32GB)"},
                            {"value": "A100", "label": "A100 (40GB)"},
                            {"value": "RTX4090", "label": "RTX 4090 (24GB)"}
                        ]
                    ),
                    InputField(
                        field_id="image_size",
                        field_type=InputType.SELECT,
                        label="Image Size",
                        description="Default image size",
                        default_value="512x512",
                        options=[
                            {"value": "256x256", "label": "256x256"},
                            {"value": "512x512", "label": "512x512"},
                            {"value": "1024x1024", "label": "1024x1024"}
                        ]
                    )
                ])
            
            if app_profile.get('category') in ['AUDIO']:
                basic_section.fields.extend([
                    InputField(
                        field_id="audio_quality",
                        field_type=InputType.SELECT,
                        label="Audio Quality",
                        description="Audio output quality",
                        default_value="high",
                        options=[
                            {"value": "low", "label": "Low (16kHz)"},
                            {"value": "medium", "label": "Medium (22kHz)"},
                            {"value": "high", "label": "High (44kHz)"}
                        ]
                    )
                ])
            
            # Web UI Configuration Section
            if app_profile.get('webui_type'):
                webui_section = FormSection(
                    section_id="webui_config",
                    title="Web UI Configuration",
                    description="Configure web interface settings",
                    order=2
                )
                
                webui_section.fields.extend([
                    InputField(
                        field_id="port",
                        field_type=InputType.NUMBER,
                        label="Port",
                        description="Port for web interface",
                        default_value=7860,
                        required=True,
                        validation_rules=[
                            {"rule": ValidationRule.MIN_VALUE, "value": 1024},
                            {"rule": ValidationRule.MAX_VALUE, "value": 65535}
                        ]
                    ),
                    InputField(
                        field_id="share",
                        field_type=InputType.BOOLEAN,
                        label="Public Share",
                        description="Create public share link",
                        default_value=False
                    ),
                    InputField(
                        field_id="tunnel_type",
                        field_type=InputType.SELECT,
                        label="Tunnel Type",
                        description="Tunnel service for public access",
                        default_value="ngrok",
                        options=[
                            {"value": "ngrok", "label": "Ngrok"},
                            {"value": "cloudflare", "label": "Cloudflare Tunnel"},
                            {"value": "localtunnel", "label": "LocalTunnel"}
                        ],
                        dependencies=["share"]
                    )
                ])
                
                sections.append(webui_section)
            
            # Advanced Configuration Section
            advanced_section = FormSection(
                section_id="advanced_config",
                title="Advanced Configuration",
                description="Advanced application settings",
                order=3
            )
            
            advanced_section.fields.extend([
                InputField(
                    field_id="environment_variables",
                    field_type=InputType.TEXTAREA,
                    label="Environment Variables",
                    description="Additional environment variables (one per line, format: KEY=VALUE)",
                    placeholder="API_KEY=your_key_here\nMODEL_PATH=/path/to/model"
                ),
                InputField(
                    field_id="custom_args",
                    field_type=InputType.TEXTAREA,
                    label="Custom Arguments",
                    description="Additional command line arguments",
                    placeholder="--verbose --debug"
                ),
                InputField(
                    field_id="auto_start",
                    field_type=InputType.BOOLEAN,
                    label="Auto Start",
                    description="Automatically start the application after installation",
                    default_value=True
                )
            ])
            
            sections.append(advanced_section)
            
            # Create form
            form = FormDefinition(
                form_id=form_id,
                title=f"Install {app_name}",
                description=f"Configure and install {app_name}",
                sections=sections,
                submit_button_text="Install Application",
                cancel_button_text="Cancel Installation"
            )
            
            self.active_forms[form_id] = form
            self._update_progress(f"Created installation form for {app_name}")
            
            return form_id
        
        except Exception as e:
            return ""
    
    def collect_input(self, form_id: str, input_data: Dict[str, Any]) -> FormResult:
        """
        Collect and validate user input.
        
        Args:
            form_id: Form ID
            input_data: User input data
            
        Returns:
            FormResult: Form submission result
        """
        start_time = time.time()
        
        result = FormResult(
            success=False,
            form_id=form_id,
            submission_time=0.0
        )
        
        try:
            if form_id not in self.active_forms:
                result.error_messages.append("Form not found")
                return result
            
            form = self.active_forms[form_id]
            self._update_progress(f"Processing form submission: {form_id}")
            
            # Validate all fields
            validation_results = []
            for section in form.sections:
                for field in section.fields:
                    if field.field_id in input_data:
                        validation_result = self._validate_field(field, input_data[field.field_id])
                        validation_results.append(validation_result)
                        
                        if not validation_result.is_valid:
                            result.error_messages.append(f"{field.label}: {validation_result.error_message}")
            
            # Check if all validations passed
            all_valid = all(vr.is_valid for vr in validation_results)
            
            if all_valid:
                # Process and store input data
                processed_data = self._process_input_data(input_data, form)
                result.submitted_data = processed_data
                result.success = True
                
                # Store form response
                self.form_responses[form_id] = result
                
                # Set variables in variable system
                for key, value in processed_data.items():
                    self.variable_system.set_variable(key, value)
                
                self._update_progress(f"Form submission successful: {form_id}")
            else:
                result.validation_results = validation_results
                self._update_progress(f"Form validation failed: {form_id}")
            
            result.submission_time = time.time() - start_time
            return result
        
        except Exception as e:
            result.error_messages.append(f"Form processing error: {str(e)}")
            result.submission_time = time.time() - start_time
            return result
    
    def get_form_definition(self, form_id: str) -> Optional[FormDefinition]:
        """
        Get form definition.
        
        Args:
            form_id: Form ID
            
        Returns:
            FormDefinition or None if not found
        """
        return self.active_forms.get(form_id)
    
    def get_form_response(self, form_id: str) -> Optional[FormResult]:
        """
        Get form response.
        
        Args:
            form_id: Form ID
            
        Returns:
            FormResult or None if not found
        """
        return self.form_responses.get(form_id)
    
    def save_form_template(self, template_id: str, form_definition: FormDefinition):
        """
        Save form as template.
        
        Args:
            template_id: Template ID
            form_definition: Form definition
        """
        try:
            self.form_templates[template_id] = form_definition
            
            # Save to file
            template_path = os.path.join(self.base_path, "forms", f"{template_id}.json")
            template_data = self._serialize_form_definition(form_definition)
            self.json_handler.write_json(template_path, template_data)
            
            self._update_progress(f"Saved form template: {template_id}")
        
        except Exception as e:
            pass
    
    def load_form_template(self, template_id: str) -> bool:
        """
        Load form template from file.
        
        Args:
            template_id: Template ID
            
        Returns:
            bool: True if template loaded successfully
        """
        try:
            template_path = os.path.join(self.base_path, "forms", f"{template_id}.json")
            
            if os.path.exists(template_path):
                template_data = self.json_handler.read_json(template_path)
                form_definition = self._deserialize_form_definition(template_data)
                self.form_templates[template_id] = form_definition
                
                self._update_progress(f"Loaded form template: {template_id}")
                return True
            
            return False
        
        except Exception as e:
            return False
    
    def _validate_field(self, field: InputField, value: Any) -> ValidationResult:
        """Validate a single field."""
        result = ValidationResult(
            is_valid=True,
            field_id=field.field_id
        )
        
        try:
            # Check required
            if field.required and (value is None or value == ""):
                result.is_valid = False
                result.error_message = f"{field.label} is required"
                return result
            
            # Skip validation if value is empty and not required
            if value is None or value == "":
                return result
            
            # Apply validation rules
            for rule_config in field.validation_rules:
                rule = rule_config.get('rule')
                rule_value = rule_config.get('value')
                
                if rule == ValidationRule.MIN_LENGTH:
                    if len(str(value)) < rule_value:
                        result.is_valid = False
                        result.error_message = f"{field.label} must be at least {rule_value} characters"
                        break
                
                elif rule == ValidationRule.MAX_LENGTH:
                    if len(str(value)) > rule_value:
                        result.is_valid = False
                        result.error_message = f"{field.label} must be no more than {rule_value} characters"
                        break
                
                elif rule == ValidationRule.MIN_VALUE:
                    if isinstance(value, (int, float)) and value < rule_value:
                        result.is_valid = False
                        result.error_message = f"{field.label} must be at least {rule_value}"
                        break
                
                elif rule == ValidationRule.MAX_VALUE:
                    if isinstance(value, (int, float)) and value > rule_value:
                        result.is_valid = False
                        result.error_message = f"{field.label} must be no more than {rule_value}"
                        break
                
                elif rule == ValidationRule.PATTERN:
                    if not re.match(rule_value, str(value)):
                        result.is_valid = False
                        result.error_message = f"{field.label} format is invalid"
                        break
                
                elif rule == ValidationRule.EMAIL:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, str(value)):
                        result.is_valid = False
                        result.error_message = f"{field.label} must be a valid email address"
                        break
                
                elif rule == ValidationRule.URL:
                    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                    if not re.match(url_pattern, str(value)):
                        result.is_valid = False
                        result.error_message = f"{field.label} must be a valid URL"
                        break
                
                elif rule == ValidationRule.FILE_EXISTS:
                    if not os.path.exists(str(value)):
                        result.is_valid = False
                        result.error_message = f"{field.label} file does not exist"
                        break
                
                elif rule == ValidationRule.DIRECTORY_EXISTS:
                    if not os.path.isdir(str(value)):
                        result.is_valid = False
                        result.error_message = f"{field.label} directory does not exist"
                        break
                
                elif rule == ValidationRule.CUSTOM:
                    custom_function = rule_config.get('function')
                    if custom_function and custom_function in self.validation_functions:
                        if not self.validation_functions[custom_function](value):
                            result.is_valid = False
                            result.error_message = f"{field.label} validation failed"
                            break
        
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Validation error: {str(e)}"
        
        return result
    
    def _process_input_data(self, input_data: Dict[str, Any], form: FormDefinition) -> Dict[str, Any]:
        """Process and sanitize input data."""
        processed_data = {}
        
        try:
            for section in form.sections:
                for field in section.fields:
                    if field.field_id in input_data:
                        value = input_data[field.field_id]
                        
                        # Sanitize value based on field type
                        if field.field_type == InputType.TEXT:
                            value = str(value).strip()
                        elif field.field_type == InputType.NUMBER:
                            try:
                                value = float(value) if '.' in str(value) else int(value)
                            except ValueError:
                                value = 0
                        elif field.field_type == InputType.BOOLEAN:
                            value = bool(value)
                        elif field.field_type == InputType.TEXTAREA:
                            value = str(value).strip()
                        
                        processed_data[field.field_id] = value
            
            # Add metadata
            processed_data['_form_id'] = form.form_id
            processed_data['_submission_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        except Exception as e:
            pass
        
        return processed_data
    
    def _serialize_form_definition(self, form_definition: FormDefinition) -> Dict[str, Any]:
        """Serialize form definition to dictionary."""
        try:
            return {
                'form_id': form_definition.form_id,
                'title': form_definition.title,
                'description': form_definition.description,
                'sections': [
                    {
                        'section_id': section.section_id,
                        'title': section.title,
                        'description': section.description,
                        'order': section.order,
                        'visible': section.visible,
                        'dependencies': section.dependencies,
                        'fields': [
                            {
                                'field_id': field.field_id,
                                'field_type': field.field_type.value,
                                'label': field.label,
                                'description': field.description,
                                'placeholder': field.placeholder,
                                'default_value': field.default_value,
                                'required': field.required,
                                'validation_rules': [
                                    {
                                        'rule': rule['rule'].value if isinstance(rule['rule'], ValidationRule) else rule['rule'],
                                        'value': rule['value']
                                    } for rule in field.validation_rules
                                ],
                                'options': field.options,
                                'dependencies': field.dependencies,
                                'metadata': field.metadata
                            } for field in section.fields
                        ]
                    } for section in form_definition.sections
                ],
                'submit_button_text': form_definition.submit_button_text,
                'cancel_button_text': form_definition.cancel_button_text,
                'metadata': form_definition.metadata
            }
        
        except Exception as e:
            return {}
    
    def _deserialize_form_definition(self, data: Dict[str, Any]) -> FormDefinition:
        """Deserialize form definition from dictionary."""
        try:
            sections = []
            for section_data in data.get('sections', []):
                fields = []
                for field_data in section_data.get('fields', []):
                    validation_rules = []
                    for rule_data in field_data.get('validation_rules', []):
                        rule_type = ValidationRule(rule_data['rule']) if isinstance(rule_data['rule'], str) else rule_data['rule']
                        validation_rules.append({
                            'rule': rule_type,
                            'value': rule_data['value']
                        })
                    
                    field = InputField(
                        field_id=field_data['field_id'],
                        field_type=InputType(field_data['field_type']),
                        label=field_data['label'],
                        description=field_data.get('description', ''),
                        placeholder=field_data.get('placeholder', ''),
                        default_value=field_data.get('default_value'),
                        required=field_data.get('required', False),
                        validation_rules=validation_rules,
                        options=field_data.get('options', []),
                        dependencies=field_data.get('dependencies', []),
                        metadata=field_data.get('metadata', {})
                    )
                    fields.append(field)
                
                section = FormSection(
                    section_id=section_data['section_id'],
                    title=section_data['title'],
                    description=section_data.get('description', ''),
                    fields=fields,
                    order=section_data.get('order', 0),
                    visible=section_data.get('visible', True),
                    dependencies=section_data.get('dependencies', [])
                )
                sections.append(section)
            
            return FormDefinition(
                form_id=data['form_id'],
                title=data['title'],
                description=data.get('description', ''),
                sections=sections,
                submit_button_text=data.get('submit_button_text', 'Submit'),
                cancel_button_text=data.get('cancel_button_text', 'Cancel'),
                metadata=data.get('metadata', {})
            )
        
        except Exception as e:
            return FormDefinition(form_id="", title="")
    
    def _setup_default_validation(self):
        """Setup default validation functions."""
        try:
            # Add custom validation functions
            self.validation_functions['positive_number'] = lambda x: isinstance(x, (int, float)) and x > 0
            self.validation_functions['valid_port'] = lambda x: isinstance(x, int) and 1024 <= x <= 65535
            self.validation_functions['valid_path'] = lambda x: os.path.exists(str(x))
        
        except Exception as e:
            pass
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing input handler."""
    print("🧪 Testing Input Handler")
    print("=" * 50)
    
    # Initialize handler
    handler = InputHandler()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    handler.set_progress_callback(progress_callback)
    
    # Test form creation
    print("\n📝 Testing form creation...")
    
    # Create a test form
    test_form = FormDefinition(
        form_id="test_form",
        title="Test Form",
        description="A test form for validation",
        sections=[
            FormSection(
                section_id="basic",
                title="Basic Information",
                fields=[
                    InputField(
                        field_id="name",
                        field_type=InputType.TEXT,
                        label="Name",
                        description="Your full name",
                        required=True,
                        validation_rules=[
                            {"rule": ValidationRule.MIN_LENGTH, "value": 2},
                            {"rule": ValidationRule.MAX_LENGTH, "value": 50}
                        ]
                    ),
                    InputField(
                        field_id="email",
                        field_type=InputType.EMAIL,
                        label="Email",
                        description="Your email address",
                        required=True,
                        validation_rules=[
                            {"rule": ValidationRule.EMAIL, "value": ""}
                        ]
                    ),
                    InputField(
                        field_id="age",
                        field_type=InputType.NUMBER,
                        label="Age",
                        description="Your age",
                        required=True,
                        validation_rules=[
                            {"rule": ValidationRule.MIN_VALUE, "value": 18},
                            {"rule": ValidationRule.MAX_VALUE, "value": 100}
                        ]
                    )
                ]
            )
        ]
    )
    
    success = handler.create_form(test_form)
    print(f"✅ Form creation success: {success}")
    
    # Test form retrieval
    print("\n📋 Testing form retrieval...")
    retrieved_form = handler.get_form_definition("test_form")
    print(f"✅ Form retrieval success: {retrieved_form is not None}")
    if retrieved_form:
        print(f"   - Form ID: {retrieved_form.form_id}")
        print(f"   - Title: {retrieved_form.title}")
        print(f"   - Sections: {len(retrieved_form.sections)}")
        print(f"   - Fields: {sum(len(section.fields) for section in retrieved_form.sections)}")
    
    # Test input collection and validation
    print("\n✅ Testing input collection and validation...")
    
    # Valid input
    valid_input = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 25
    }
    
    result = handler.collect_input("test_form", valid_input)
    print(f"✅ Valid input success: {result.success}")
    print(f"   - Validation results: {len(result.validation_results)}")
    print(f"   - Submitted data: {len(result.submitted_data)} fields")
    
    # Invalid input
    invalid_input = {
        "name": "A",  # Too short
        "email": "invalid-email",  # Invalid email
        "age": 15  # Too young
    }
    
    result = handler.collect_input("test_form", invalid_input)
    print(f"✅ Invalid input handling: {not result.success}")
    print(f"   - Error messages: {len(result.error_messages)}")
    for error in result.error_messages:
        print(f"     - {error}")
    
    # Test installation form creation
    print("\n🔧 Testing installation form creation...")
    
    app_profile = {
        'category': 'LLM',
        'webui_type': 'gradio',
        'name': 'test_llm_app'
    }
    
    form_id = handler.create_installation_form("test_llm_app", app_profile)
    print(f"✅ Installation form creation: {form_id != ''}")
    if form_id:
        install_form = handler.get_form_definition(form_id)
        print(f"   - Form ID: {install_form.form_id}")
        print(f"   - Sections: {len(install_form.sections)}")
        print(f"   - Fields: {sum(len(section.fields) for section in install_form.sections)}")
    
    # Test form template saving and loading
    print("\n💾 Testing form template operations...")
    
    handler.save_form_template("test_template", test_form)
    load_success = handler.load_form_template("test_template")
    print(f"✅ Template save/load success: {load_success}")
    
    return True


if __name__ == "__main__":
    main()