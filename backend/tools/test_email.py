"""
Debug tool to test the email sender.
Usage: python test_email.py <recipient_email> [template_type] [key=value ...]
Default template_type: "test"
"""

import sys
import traceback
from pathlib import Path

# Allow running directly from this directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.email_sender import send_template_email

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_email.py <recipient_email> [template_type] [key=value ...]")
        sys.exit(1)

    recipient = sys.argv[1]
    template_type = sys.argv[2] if len(sys.argv) > 2 else "welcome"
    placeholders = {}

    for arg in sys.argv[3:]:
        if "=" not in arg:
            print(f"Skipping invalid placeholder argument: {arg} (expected key=value)")
            continue
        key, value = arg.split("=", 1)
        placeholders[key] = value

    print(f"Sending '{template_type}' email to: {recipient} ...")
    try:
        result = send_template_email(recipient, template_type, placeholders)
        if result:
            print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
