#!/usr/bin/env python3
"""
Email Preparation and Sending Script

This script prepares and sends emails using a template file and msmtp.
It replaces placeholders in the template with provided values and handles
the email sending process.

Template Format:
    The template should use @placeholder@ format, where placeholder can be:
    - hostname: The machine's hostname or description
    - topic: The email subject
    - body: The email content

Requirements:
    - Python 3.6+
    - msmtp installed and configured
    - Write access to log directory
    - Read access to template file
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from typing import Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    filename='/var/log/email_script.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class TemplateError(Exception):
    """Custom exception for template-related errors."""
    pass

class EmailTemplate:
    """
    Custom template class for handling email templates with @placeholder@ format.
    
    This class provides methods to safely replace placeholders in the format
    @placeholder@ with provided values.
    """
    
    def __init__(self, template_str: str):
        """
        Initialize template with the template string.
        
        Args:
            template_str: The template string containing @placeholder@ patterns
        """
        self.template = template_str
        self._validate_template()
    
    def _validate_template(self) -> None:
        """
        Validate template format and required placeholders.
        
        Raises:
            TemplateError: If template is invalid or missing required placeholders
        """
        required_placeholders = {'hostname', 'topic', 'body'}
        found_placeholders = set(re.findall(r'@(\w+)@', self.template))
        
        if not found_placeholders:
            raise TemplateError("Template contains no valid placeholders")
        
        missing = required_placeholders - found_placeholders
        if missing:
            raise TemplateError(f"Template missing required placeholders: {missing}")
    
    def safe_substitute(self, **kwargs: str) -> str:
        """
        Safely replace placeholders with provided values.
        
        Args:
            **kwargs: Keyword arguments where key is placeholder name and value is replacement
        
        Returns:
            str: Template with placeholders replaced by provided values
        
        Raises:
            TemplateError: If required placeholders are missing from kwargs
        """
        result = self.template
        
        # Validate all required values are provided
        required_values = set(re.findall(r'@(\w+)@', self.template))
        missing_values = required_values - set(kwargs.keys())
        if missing_values:
            raise TemplateError(f"Missing values for placeholders: {missing_values}")
        
        # Replace each placeholder
        for key, value in kwargs.items():
            pattern = f'@{key}@'
            if pattern in result:
                result = result.replace(pattern, str(value))
        
        return result

def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Prepare and send email based on a template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --topic "System Alert" --body "Disk space low" --hostname "webserver1"
    %(prog)s -t "Daily Report" -b "All systems normal"
        """
    )
    
    parser.add_argument(
        '-t', '--topic',
        required=True,
        help="Topic for email subject"
    )
    parser.add_argument(
        '-b', '--body',
        required=True,
        help="Body text for email"
    )
    parser.add_argument(
        '--hostname',
        default=None,
        help="Hostname or machine description (defaults to system hostname)"
    )
    
    return parser

def get_hostname() -> str:
    """
    Get system hostname with fallback options.
    
    Returns:
        str: System hostname or fallback value
    """
    try:
        return os.uname().nodename
    except AttributeError:
        return os.environ.get('COMPUTERNAME', 'unknown-host')

def read_template(template_path: str) -> EmailTemplate:
    """
    Read and validate the email template file.
    
    Args:
        template_path: Path to the template file
    
    Returns:
        EmailTemplate: Initialized template object
    
    Raises:
        FileNotFoundError: If template file doesn't exist
        TemplateError: If template is invalid
    """
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            return EmailTemplate(file.read())
    except (IOError, UnicodeDecodeError) as e:
        raise TemplateError(f"Error reading template file: {e}")

def send_email(content: str) -> Tuple[bool, Optional[str]]:
    """
    Send email using msmtp.
    
    Args:
        content: Prepared email content
    
    Returns:
        Tuple[bool, Optional[str]]: (Success status, Error message if any)
    """
    msmtp_config = os.path.expanduser('~/.msmtprc')
    if not os.path.isfile(msmtp_config):
        raise RuntimeError(f"msmtp config not found: {msmtp_config}")
    
    try:
        process = subprocess.Popen(
            [
                'msmtp',
                '--file', msmtp_config,
                '--read-envelope-from',
                '--read-recipients'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=content)
        
        if process.returncode != 0:
            return False, stderr.strip()
        
        return True, None
        
    except subprocess.SubprocessError as e:
        return False, str(e)

def main() -> int:
    """
    Main function to handle email preparation and sending.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Get hostname if not provided
        hostname = args.hostname or get_hostname()
        
        # Log input parameters
        logging.debug("Input parameters:")
        logging.debug(f"  Topic: {args.topic}")
        logging.debug(f"  Body: {args.body}")
        logging.debug(f"  Hostname: {hostname}")
        
        # Get template path relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, 'template.txt')
        
        # Read and process template
        template = read_template(template_path)
        email_content = template.safe_substitute(
            hostname=hostname,
            topic=args.topic,
            body=args.body
        )
        
        # Send email
        success, error = send_email(email_content)
        if not success:
            raise RuntimeError(f"Failed to send email: {error}")
        
        logging.info("Email sent successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
