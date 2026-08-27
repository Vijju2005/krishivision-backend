import os
import urllib.request
import urllib.parse
import base64
from abc import ABC, abstractmethod

class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, to_phone: str, message: str) -> bool:
        pass

class MockSMSProvider(SMSProvider):
    def send_sms(self, to_phone: str, message: str) -> bool:
        print(f"\n[Mock SMS Provider] Sending SMS to {to_phone}: {message}\n")
        # Log to file in the uploads directory
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.abspath(os.path.join(base_dir, "..", "uploads", "sms_dev.log"))
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"TO: {to_phone} | MESSAGE: {message}\n")
        except Exception as e:
            print(f"[Mock SMS Provider] Logging failed: {e}")
        return True

class TwilioSMSProvider(SMSProvider):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_sms(self, to_phone: str, message: str) -> bool:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        # Twilio API expects POST parameters as application/x-www-form-urlencoded
        data = urllib.parse.urlencode({
            "To": to_phone,
            "From": self.from_number,
            "Body": message
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, method="POST")
        
        # Basic Auth header construction
        auth_str = f"{self.account_sid}:{self.auth_token}"
        auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        req.add_header("Authorization", f"Basic {auth_bytes}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201):
                    print(f"[Twilio SMS Provider] Successfully sent message to {to_phone}")
                    return True
                else:
                    print(f"[Twilio SMS Provider] Failed to send message to {to_phone}: status {response.status}")
                    return False
        except Exception as e:
            print(f"[Twilio SMS Provider] Exception sending SMS to {to_phone}: {e}")
            return False

def get_sms_provider() -> SMSProvider:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    
    if account_sid and auth_token and from_number:
        print("[SMS Service] Using Twilio SMS Provider")
        return TwilioSMSProvider(account_sid, auth_token, from_number)
    else:
        print("[SMS Service] Twilio config not fully set. Falling back to Mock SMS Provider")
        return MockSMSProvider()
