# CheckMK Notification Plugin Development
## Creating Custom Alert Integrations

> **Prerequisites**: Read [01-quickstart.md](01-quickstart.md) for naming conventions and directory structure

## Overview

Notification plugins send alerts to external systems (Slack, Discord, PagerDuty, etc.) when CheckMK detects problems. Unlike check plugins which run continuously, notification plugins execute only when triggered by events.

### Key Concepts

**Execution Model**: Notification scripts are **executable files** that CheckMK runs directly
- CheckMK passes data via **environment variables** (not command-line arguments)
- Scripts write to stdout/stderr for logging
- Exit code indicates success (0) or failure (non-zero)

**Two Approaches**:
1. **Self-contained script** - All logic in one executable file (simple, recommended)
2. **Modular** - Python modules + wrapper script (for complex reusable code)

## Directory Structure

```
./local/
├── share/check_mk/notifications/
│   └── my_notification           # Executable notification script
└── lib/python3/cmk/notification_plugins/  # Optional: Python modules
    └── my_notification.py
```

**Installation Paths** (when MKP is installed):
- Scripts: `~SITE/local/share/check_mk/notifications/`
- Modules: `~SITE/local/lib/python3/cmk/notification_plugins/`

## Approach 1: Self-Contained Script (Recommended)

### Minimal Example

**File**: `./local/share/check_mk/notifications/my_webhook`

```python
#!/usr/bin/env python3
# My Custom Webhook Notification

import os
import sys
import json
import urllib.request
import urllib.error

def main():
    """Send notification to webhook"""
    # Get webhook URL from notification parameters
    webhook_url = os.environ.get("NOTIFY_PARAMETER_1")
    if not webhook_url:
        sys.stderr.write("ERROR: Missing webhook URL\n")
        return 1

    # Determine what type of notification this is
    what = os.environ.get("NOTIFY_WHAT", "SERVICE")  # SERVICE or HOST
    notification_type = os.environ.get("NOTIFY_NOTIFICATIONTYPE", "PROBLEM")

    # Build message based on type
    if what == "HOST":
        hostname = os.environ.get("NOTIFY_HOSTNAME", "unknown")
        state = os.environ.get("NOTIFY_HOSTSTATE", "UNKNOWN")
        output = os.environ.get("NOTIFY_HOSTOUTPUT", "")
        message = f"Host {hostname} is {state}: {output}"
    else:  # SERVICE
        hostname = os.environ.get("NOTIFY_HOSTNAME", "unknown")
        service = os.environ.get("NOTIFY_SERVICEDESC", "unknown")
        state = os.environ.get("NOTIFY_SERVICESTATE", "UNKNOWN")
        output = os.environ.get("NOTIFY_SERVICEOUTPUT", "")
        message = f"Service {service} on {hostname} is {state}: {output}"

    # Prepare webhook payload
    payload = {
        "type": notification_type,
        "what": what,
        "message": message,
        "timestamp": os.environ.get("NOTIFY_SHORTDATETIME", "")
    }

    # Send to webhook
    try:
        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                print(f"Notification sent successfully to {webhook_url}")
                return 0
            else:
                sys.stderr.write(f"ERROR: Webhook returned {response.status}\n")
                return 1

    except urllib.error.URLError as e:
        sys.stderr.write(f"ERROR: Failed to send notification: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"ERROR: Unexpected error: {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Make it executable**:
```bash
chmod +x ./local/share/check_mk/notifications/my_webhook
```

### Complete Discord Example

Based on real-world production code:

```python
#!/usr/bin/env python3
# Discord Notification Plugin

import os
import sys
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum

class Color(IntEnum):
    """Discord embed colors"""
    CRITICAL = 0xEE0000  # Red
    DOWN = 0xEE0000
    WARNING = 0xFFDD00   # Yellow
    OK = 0x00CC00        # Green
    UP = 0x00CC00
    UNKNOWN = 0xCCCCCC   # Gray

@dataclass
class Context:
    """CheckMK notification context from environment variables"""
    what: str
    notification_type: str
    hostname: str

    # Optional parameters (from notification rule)
    webhook_url: Optional[str] = None
    site_url: Optional[str] = None

    # Service fields
    service_desc: Optional[str] = None
    service_state: Optional[str] = None
    service_output: Optional[str] = None

    # Host fields
    host_state: Optional[str] = None
    host_output: Optional[str] = None

    @classmethod
    def from_environment(cls) -> 'Context':
        """Load context from environment variables"""
        return cls(
            what=os.environ.get("NOTIFY_WHAT", "SERVICE"),
            notification_type=os.environ.get("NOTIFY_NOTIFICATIONTYPE", "PROBLEM"),
            hostname=os.environ.get("NOTIFY_HOSTNAME", "unknown"),
            webhook_url=os.environ.get("NOTIFY_PARAMETER_1"),
            site_url=os.environ.get("NOTIFY_PARAMETER_2"),
            service_desc=os.environ.get("NOTIFY_SERVICEDESC"),
            service_state=os.environ.get("NOTIFY_SERVICESTATE"),
            service_output=os.environ.get("NOTIFY_SERVICEOUTPUT"),
            host_state=os.environ.get("NOTIFY_HOSTSTATE"),
            host_output=os.environ.get("NOTIFY_HOSTOUTPUT"),
        )

def build_discord_embed(ctx: Context) -> dict:
    """Build Discord embed message"""
    if ctx.what == "HOST":
        title = f"Host: {ctx.hostname}"
        state = ctx.host_state or "UNKNOWN"
        description = ctx.host_output or "No output"
    else:
        title = f"Service: {ctx.service_desc}"
        state = ctx.service_state or "UNKNOWN"
        description = ctx.service_output or "No output"

    # Get color based on state
    color = getattr(Color, state, Color.UNKNOWN)

    embed = {
        "title": f"{ctx.notification_type}: {title}",
        "description": description,
        "color": color,
        "fields": [
            {"name": "Host", "value": ctx.hostname, "inline": True},
            {"name": "State", "value": state, "inline": True},
        ],
        "footer": {"text": f"CheckMK - {os.environ.get('NOTIFY_SHORTDATETIME', '')}"}
    }

    # Add site URL if configured
    if ctx.site_url:
        if ctx.what == "SERVICE":
            url = f"{ctx.site_url}/check_mk/view.py?view_name=service"
        else:
            url = f"{ctx.site_url}/check_mk/view.py?view_name=host"
        embed["url"] = url

    return embed

def send_to_discord(webhook_url: str, embed: dict) -> bool:
    """Send embed to Discord webhook"""
    payload = {
        "username": "CheckMK",
        "embeds": [embed]
    }

    try:
        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status in (200, 204):
                return True
            else:
                sys.stderr.write(f"Discord returned status {response.status}\n")
                return False

    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP Error {e.code}: {e.reason}\n")
        return False
    except urllib.error.URLError as e:
        sys.stderr.write(f"Connection error: {e.reason}\n")
        return False
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {type(e).__name__}: {e}\n")
        return False

def main():
    """Main entry point"""
    # Load context from environment
    ctx = Context.from_environment()

    # Validate required parameters
    if not ctx.webhook_url:
        sys.stderr.write("ERROR: NOTIFY_PARAMETER_1 (webhook URL) is required\n")
        return 1

    # Build and send message
    embed = build_discord_embed(ctx)

    if send_to_discord(ctx.webhook_url, embed):
        print(f"Notification sent to Discord for {ctx.hostname}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Approach 2: Modular with Python Library

For complex notifications with shared utility code.

### Python Module

**File**: `./local/lib/python3/cmk/notification_plugins/my_service.py`

```python
#!/usr/bin/env python3
"""My Service notification plugin"""

import os
import sys
import json
import urllib.request
from typing import Dict, Any

def get_context() -> Dict[str, Any]:
    """Extract notification context from environment variables"""
    return {
        'what': os.environ.get('NOTIFY_WHAT', 'SERVICE'),
        'type': os.environ.get('NOTIFY_NOTIFICATIONTYPE', 'PROBLEM'),
        'hostname': os.environ.get('NOTIFY_HOSTNAME', 'unknown'),
        'service': os.environ.get('NOTIFY_SERVICEDESC'),
        'state': os.environ.get('NOTIFY_SERVICESTATE') or os.environ.get('NOTIFY_HOSTSTATE'),
        'output': os.environ.get('NOTIFY_SERVICEOUTPUT') or os.environ.get('NOTIFY_HOSTOUTPUT'),
        'api_key': os.environ.get('NOTIFY_PARAMETER_1'),
        'api_endpoint': os.environ.get('NOTIFY_PARAMETER_2'),
    }

def format_message(context: Dict[str, Any]) -> str:
    """Format notification message"""
    if context['what'] == 'HOST':
        return f"Host {context['hostname']} is {context['state']}: {context['output']}"
    else:
        return f"Service {context['service']} on {context['hostname']} is {context['state']}: {context['output']}"

def send_notification(context: Dict[str, Any]) -> int:
    """Send notification to external service"""
    if not context['api_key']:
        sys.stderr.write("ERROR: Missing API key (PARAMETER_1)\n")
        return 1

    message = format_message(context)
    payload = {
        'message': message,
        'severity': 'critical' if context['state'] in ('CRITICAL', 'DOWN') else 'warning',
        'source': 'checkmk',
    }

    try:
        request = urllib.request.Request(
            context['api_endpoint'],
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {context['api_key']}"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            return 0 if response.status == 200 else 1

    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 1

def main() -> int:
    """Main entry point"""
    context = get_context()
    return send_notification(context)
```

### Wrapper Script

**File**: `./local/share/check_mk/notifications/my_service`

```python
#!/usr/bin/env python3
# My Service Notification

import sys
from cmk.notification_plugins.my_service import main

if __name__ == "__main__":
    sys.exit(main())
```

```bash
chmod +x ./local/share/check_mk/notifications/my_service
```

## Available Environment Variables

CheckMK provides extensive context via environment variables:

### Common Variables

```python
# Always available
NOTIFY_WHAT                  # "HOST" or "SERVICE"
NOTIFY_NOTIFICATIONTYPE      # "PROBLEM", "RECOVERY", "ACKNOWLEDGEMENT", etc.
NOTIFY_HOSTNAME              # Host name
NOTIFY_HOSTADDRESS           # Host IP address
NOTIFY_HOSTALIAS             # Host alias
NOTIFY_SHORTDATETIME         # Timestamp (e.g., "2024-11-18 17:30:00")
NOTIFY_LONGDATETIME          # Full timestamp
NOTIFY_DATE                  # Date only
NOTIFY_CONTACTNAME           # Contact being notified
NOTIFY_CONTACTEMAIL          # Contact email
NOTIFY_OMD_SITE              # Site name
NOTIFY_OMD_ROOT              # Site root path

# Host-specific (when NOTIFY_WHAT == "HOST")
NOTIFY_HOSTSTATE             # "UP", "DOWN", "UNREACHABLE"
NOTIFY_LASTHOSTSTATE         # Previous state
NOTIFY_HOSTOUTPUT            # Check output
NOTIFY_LONGHOSTOUTPUT        # Detailed output
NOTIFY_HOSTPERFDATA          # Performance data

# Service-specific (when NOTIFY_WHAT == "SERVICE")
NOTIFY_SERVICEDESC           # Service description
NOTIFY_SERVICESTATE          # "OK", "WARNING", "CRITICAL", "UNKNOWN"
NOTIFY_LASTSERVICESTATE      # Previous state
NOTIFY_SERVICEOUTPUT         # Check output
NOTIFY_LONGSERVICEOUTPUT     # Detailed output
NOTIFY_SERVICEPERFDATA       # Performance data

# Parameters (from notification rule configuration)
NOTIFY_PARAMETER_1           # Custom parameter 1
NOTIFY_PARAMETER_2           # Custom parameter 2
# ... up to NOTIFY_PARAMETER_N

# URLs (if configured)
NOTIFY_HOSTURL               # Direct link to host
NOTIFY_SERVICEURL            # Direct link to service
```

### Reading Parameters

Parameters come from the notification rule configuration in the GUI:

```python
# Example: Slack notification
webhook_url = os.environ.get("NOTIFY_PARAMETER_1")  # Webhook URL
channel = os.environ.get("NOTIFY_PARAMETER_2", "#monitoring")  # Channel
username = os.environ.get("NOTIFY_PARAMETER_3", "CheckMK")  # Bot name

# Always validate required parameters
if not webhook_url:
    sys.stderr.write("ERROR: Webhook URL required (PARAMETER_1)\n")
    sys.exit(1)
```

## Error Handling Best Practices

### Exit Codes

```python
# Success
return 0

# Failure (CheckMK will retry)
return 1

# Permanent failure (CheckMK will not retry)
return 2
```

### Logging

```python
import sys

# Info (visible in notification log)
print("Notification sent successfully")

# Errors (visible in notification log)
sys.stderr.write("ERROR: Failed to connect to API\n")

# Debug (only if verbose logging enabled)
if os.environ.get("NOTIFY_LOGDIR"):
    with open(f"{os.environ['NOTIFY_LOGDIR']}/debug.log", "a") as f:
        f.write(f"Debug: payload = {payload}\n")
```

### Timeout Handling

```python
import urllib.request
import socket

try:
    # Always set a timeout to prevent hanging
    with urllib.request.urlopen(request, timeout=10) as response:
        data = response.read()
except socket.timeout:
    sys.stderr.write("ERROR: Request timed out after 10 seconds\n")
    return 1
except urllib.error.URLError as e:
    sys.stderr.write(f"ERROR: Network error: {e.reason}\n")
    return 1
```

### Retry Logic

```python
import time

def send_with_retry(url, payload, max_retries=3):
    """Send with exponential backoff"""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1, 2, 4 seconds
                time.sleep(wait)
                continue
            else:
                sys.stderr.write(f"ERROR after {max_retries} attempts: {e}\n")
                return False
    return False
```

## Testing Notification Plugins

### Manual Testing

```bash
# Set environment variables manually
export NOTIFY_WHAT="SERVICE"
export NOTIFY_NOTIFICATIONTYPE="PROBLEM"
export NOTIFY_HOSTNAME="test-host"
export NOTIFY_SERVICEDESC="CPU Load"
export NOTIFY_SERVICESTATE="CRITICAL"
export NOTIFY_SERVICEOUTPUT="Load average: 15.2"
export NOTIFY_PARAMETER_1="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Run the script
./local/share/check_mk/notifications/my_webhook

# Check exit code
echo $?  # Should be 0 for success
```

### Using CheckMK's Test Feature

```bash
# From CheckMK GUI: Setup > Events > Notifications
# 1. Create a test notification rule
# 2. Configure your plugin with parameters
# 3. Use "Test" button to trigger

# Or via command line:
cmk --notify test \
    --plugin my_webhook \
    --parameter "https://webhook.url" \
    --host myhost \
    --service "My Service"
```

### Unit Testing

```python
# tests/test_my_webhook.py
import os
import unittest
from unittest.mock import patch, MagicMock

# If using modular approach
from cmk.notification_plugins.my_webhook import main, get_context

class TestMyWebhook(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        self.env = {
            'NOTIFY_WHAT': 'SERVICE',
            'NOTIFY_HOSTNAME': 'test-host',
            'NOTIFY_SERVICEDESC': 'Test Service',
            'NOTIFY_SERVICESTATE': 'CRITICAL',
            'NOTIFY_PARAMETER_1': 'https://example.com/webhook',
        }

    @patch.dict(os.environ, env)
    def test_context_loading(self):
        """Test context extraction from environment"""
        ctx = get_context()
        self.assertEqual(ctx['hostname'], 'test-host')
        self.assertEqual(ctx['state'], 'CRITICAL')

    @patch('urllib.request.urlopen')
    @patch.dict(os.environ, env)
    def test_successful_notification(self, mock_urlopen):
        """Test successful notification sending"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = main()
        self.assertEqual(result, 0)

    @patch('urllib.request.urlopen')
    @patch.dict(os.environ, env)
    def test_network_error(self, mock_urlopen):
        """Test handling of network errors"""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")

        result = main()
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
```

## Common Patterns

### Secure Password Handling

```python
# Store passwords in CheckMK password store
# Reference them in notification rule as PARAMETER_N
password_id = os.environ.get("NOTIFY_PARAMETER_2")  # e.g., "password:webhook_secret"

# CheckMK automatically resolves password: references
if password_id and password_id.startswith("password:"):
    # Already resolved by CheckMK
    api_key = password_id
else:
    # Direct value
    api_key = password_id
```

### State-Based Formatting

```python
def get_emoji_for_state(state: str) -> str:
    """Get emoji based on state"""
    emojis = {
        'OK': '✅',
        'UP': '✅',
        'WARNING': '⚠️',
        'CRITICAL': '🚨',
        'DOWN': '🚨',
        'UNKNOWN': '❓',
        'UNREACHABLE': '🔌',
    }
    return emojis.get(state, '❓')

def get_priority(state: str) -> str:
    """Map CheckMK state to external system priority"""
    priority_map = {
        'CRITICAL': 'high',
        'DOWN': 'high',
        'WARNING': 'medium',
        'UNKNOWN': 'low',
        'OK': 'low',
        'UP': 'low',
    }
    return priority_map.get(state, 'medium')
```

### HTML Formatting

```python
def format_html_email(context):
    """Format notification as HTML email"""
    state_colors = {
        'CRITICAL': '#EE0000',
        'WARNING': '#FFDD00',
        'OK': '#00CC00',
        'UNKNOWN': '#CCCCCC',
    }

    color = state_colors.get(context['state'], '#CCCCCC')

    html = f"""
    <html>
      <body>
        <h2 style="color: {color};">{context['type']}: {context['hostname']}</h2>
        <p><strong>State:</strong> {context['state']}</p>
        <p><strong>Output:</strong> {context['output']}</p>
        <p><small>{context.get('NOTIFY_SHORTDATETIME', '')}</small></p>
      </body>
    </html>
    """
    return html
```

## Troubleshooting

### Script Not Executing

```bash
# Check if script is executable
ls -l ~/local/share/check_mk/notifications/
# Should show -rwxr-xr-x

# Make executable if needed
chmod +x ~/local/share/check_mk/notifications/my_webhook

# Check shebang
head -1 ~/local/share/check_mk/notifications/my_webhook
# Should be: #!/usr/bin/env python3
```

### Not Receiving Notifications

```bash
# Check notification log
tail -f ~/var/log/notify.log

# Check for errors
grep ERROR ~/var/log/notify.log

# Test manually
export NOTIFY_PARAMETER_1="test"
~/local/share/check_mk/notifications/my_webhook
```

### Import Errors (Modular Approach)

```bash
# Ensure Python can find your module
export PYTHONPATH=~/local/lib/python3:$PYTHONPATH

# Test import
python3 -c "from cmk.notification_plugins.my_webhook import main; print('OK')"
```

### Debugging Environment Variables

```python
#!/usr/bin/env python3
# Debug script - shows all NOTIFY_ variables

import os
import sys

print("=== CheckMK Notification Environment ===")
for key, value in sorted(os.environ.items()):
    if key.startswith("NOTIFY_"):
        print(f"{key} = {value}")
print("=" * 40)
sys.exit(0)
```

## Best Practices

1. **Always validate required parameters** - Return error if missing
2. **Use timeouts** - Don't let network calls hang indefinitely
3. **Handle all exception types** - Network errors, timeouts, JSON parsing, etc.
4. **Return correct exit codes** - 0 for success, 1 for retry, 2 for permanent failure
5. **Log to stderr** - Use stderr for errors, stdout for info
6. **Test thoroughly** - Use manual tests before deploying to production
7. **Keep dependencies minimal** - Use stdlib when possible (urllib vs requests)
8. **Document parameters** - Clear comments about what PARAMETER_1, etc. expect
9. **Implement retry logic** - For transient network failures
10. **Sanitize data** - Escape/validate before sending to external APIs

## Next Steps

- **Configuration UI**: Create notification rules in CheckMK GUI
- **Rulesets**: Define parameter forms for your notification plugin (advanced)
- **Testing**: Set up test notifications to verify functionality
- **Monitoring**: Watch notification logs for errors and performance

## References

- CheckMK Notification Documentation: https://docs.checkmk.com/latest/en/notifications.html
- Environment Variables Reference: Check CheckMK docs for complete list
- Example Plugins: See `notifications/` directory in CheckMK installation
