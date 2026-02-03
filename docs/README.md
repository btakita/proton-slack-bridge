# ProtonMail Bridge → Slack Setup

## Quick Start

### 1. Install Dependencies
```bash
pip install requests
# OR create venv
python3 -m venv venv
source venv/bin/activate
pip install requests
```

### 2. Get Proton Mail Bridge Credentials
Open Proton Mail Bridge app → Your account → Mailbox configuration
- **IMAP Host**: 127.0.0.1
- **IMAP Port**: 1143 (default)
- **Username**: your@protonmail.com
- **Password**: Generated bridge password (NOT your Proton password)

### 3. Create Slack Webhook
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Incoming Webhooks → Activate → Add New Webhook to Workspace
4. Copy the webhook URL

### 4. Set Environment Variables
```bash
export PROTON_EMAIL="your@protonmail.com"
export PROTON_BRIDGE_PASSWORD="bridge-generated-password"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 5. Test Run
```bash
chmod +x protonslack.py
./protonslack.py
```

Send yourself a test email - it should appear in Slack within 30 seconds.

---

## macOS Service Setup (launchd)

### Create Service File
```bash
# Create the plist
nano ~/Library/LaunchAgents/com.protonslack.plist
```

### OSX Service Configuration
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.protonslack</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/.local/bin/protonslack</string>
    </array>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PROTON_EMAIL</key>
        <string>your@protonmail.com</string>
        <key>PROTON_BRIDGE_PASSWORD</key>
        <string>your-bridge-password</string>
        <key>SLACK_WEBHOOK_URL</key>
        <string>https://hooks.slack.com/services/YOUR/WEBHOOK</string>
    </dict>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/protonslack.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/protonslack.error.log</string>
</dict>
</plist>
```

### Install Service
```bash
# Make script executable and move to permanent location
chmod +x protonslack.py
mkdir -p ~/.local/bin
cp protonslack.py ~/.local/bin/protonslack

# Load the service
launchctl load ~/Library/LaunchAgents/com.protonslack.plist

# Check if running
launchctl list | grep protonslack

# View logs
tail -f ~/Library/Logs/protonslack.log
```

### Manage Service
```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.protonslack.plist

# Start
launchctl load ~/Library/LaunchAgents/com.protonslack.plist

# Restart (after code changes)
launchctl unload ~/Library/LaunchAgents/com.protonslack.plist
cp protonslack.py ~/.local/bin/protonslack
launchctl load ~/Library/LaunchAgents/com.protonslack.plist
```

---

## Customization

### Filter by Sender
```python
# In check_new_messages(), add filtering:
def check_new_messages(self) -> list[EmailMessage]:
    # ... existing code ...
    
    for msg_id in message_ids:
        # ... existing code ...
        raw_email = email.message_from_bytes(msg_data[0][1])
        msg = EmailMessage(raw_email)
        
        # Only forward from specific senders
        allowed_senders = ["important@example.com", "alerts@"]
        if any(sender in msg.from_addr for sender in allowed_senders):
            new_messages.append(msg)
```

### Route to Different Channels
```python
# Use multiple webhooks based on sender/subject
WEBHOOKS = {
    "alerts": os.getenv("SLACK_WEBHOOK_ALERTS"),
    "default": os.getenv("SLACK_WEBHOOK_URL"),
}

def get_webhook_for_message(self, message: EmailMessage) -> str:
    if "alert" in message.subject.lower():
        return WEBHOOKS["alerts"]
    return WEBHOOKS["default"]
```

### Use IMAP IDLE (Real-time)
```python
# Replace polling with IDLE for instant notifications
# Requires imaplib2 or asyncio IMAP library
pip install imapclient

# Then use IDLE mode instead of polling
```

---

## Troubleshooting

### "Authentication failed"
- Make sure you're using the **Bridge password**, not your Proton account password
- Check Bridge app is running
- Verify credentials in Bridge app settings

### "Connection refused"
- Proton Mail Bridge must be running
- Check port in Bridge settings (Settings → Advanced)
- Default is 1143 for IMAP

### Messages not appearing
- Check logs: `tail -f ~/Library/Logs/protonslack.log`
- Verify webhook URL is correct: `curl -X POST -H 'Content-Type: application/json' -d '{"text":"test"}' YOUR_WEBHOOK_URL`
- Check email is marked as unread in Proton

### Service not starting at boot
- Verify plist file syntax: `plutil ~/Library/LaunchAgents/com.protonslack.plist`
- Check file paths are absolute
- View system logs: `log show --predicate 'processImagePath contains "protonslack"' --last 10m`
