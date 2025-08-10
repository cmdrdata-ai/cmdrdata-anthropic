#!/usr/bin/env python3
"""
CLI setup wizard for CmdrData - allows users to register and get API keys from the command line
Can be integrated into the SDK for easy onboarding
"""
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Default to production, but allow override for testing
CMDRDATA_API_URL = os.getenv("CMDRDATA_API_URL", "https://api.cmdrdata.ai")


class CmdrDataSetup:
    """Setup wizard for CmdrData accounts"""

    def __init__(self, api_url: str = CMDRDATA_API_URL):
        self.api_url = api_url
        self.config_dir = Path.home() / ".cmdrdata"
        self.config_file = self.config_dir / "config.json"

    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration if it exists"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to user's home directory"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
        # Set restrictive permissions on Unix-like systems
        if os.name != "nt":
            os.chmod(self.config_file, 0o600)

    def register_user(self) -> Optional[Dict[str, Any]]:
        """Interactive user registration"""
        print("\n=== CmdrData Account Registration ===")
        print("Create a free account to start tracking AI usage\n")

        # Get user details
        email = input("Email address: ").strip()
        name = input("Your name: ").strip()

        # Get password securely
        while True:
            password = getpass.getpass("Password (min 8 chars): ")
            if len(password) < 8:
                print("[ERROR] Password must be at least 8 characters")
                continue

            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("[ERROR] Passwords don't match")
                continue
            break

        # Register with API
        register_data = {"email": email, "password": password, "name": name}

        try:
            response = requests.post(
                f"{self.api_url}/auth/register", json=register_data, timeout=10
            )

            if response.status_code == 200:
                print(f"\n[OK] Account created successfully!")

                # Now login to get token
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )

                if login_response.status_code == 200:
                    return login_response.json()
                else:
                    print(
                        f"[ERROR] Login failed after registration: {login_response.text}"
                    )
                    return None

            elif response.status_code == 400 and "already exists" in response.text:
                print("\n[INFO] Account already exists. Please login instead.")
                return None
            else:
                print(f"\n[ERROR] Registration failed: {response.text}")
                return None

        except requests.RequestException as e:
            print(f"\n[ERROR] Network error: {e}")
            return None

    def login_user(self) -> Optional[Dict[str, Any]]:
        """Interactive user login"""
        print("\n=== CmdrData Login ===")

        email = input("Email address: ").strip()
        password = getpass.getpass("Password: ")

        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10,
            )

            if response.status_code == 200:
                print(f"\n[OK] Logged in successfully!")
                return response.json()
            else:
                print(f"\n[ERROR] Login failed: Invalid credentials")
                return None

        except requests.RequestException as e:
            print(f"\n[ERROR] Network error: {e}")
            return None

    def create_api_key(self, access_token: str) -> Optional[str]:
        """Create an API key for SDK usage"""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Check existing keys first
        try:
            response = requests.get(
                f"{self.api_url}/user/api-keys", headers=headers, timeout=10
            )

            if response.status_code == 200:
                existing_keys = response.json().get("api_keys", [])

                # Look for SDK key
                for key in existing_keys:
                    if "SDK" in key.get("name", "") and key.get("is_active"):
                        print("\n[INFO] Found existing SDK API key")
                        return "existing-key-hidden"  # Can't retrieve raw key

        except requests.RequestException:
            pass

        # Create new API key
        key_data = {"name": "SDK Auto-Generated Key", "permissions": ["read", "write"]}

        try:
            response = requests.post(
                f"{self.api_url}/user/api-keys",
                json=key_data,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                api_key = response.json().get("key")
                print(f"\n[OK] API key created successfully")
                return api_key
            else:
                print(f"\n[ERROR] Failed to create API key: {response.text}")
                return None

        except requests.RequestException as e:
            print(f"\n[ERROR] Network error: {e}")
            return None

    def interactive_setup(self) -> bool:
        """Run the interactive setup wizard"""

        print("\n" + "=" * 60)
        print("       CmdrData - AI Intelligence Platform")
        print("    Track every AI call with unlimited metadata")
        print("=" * 60)

        # Check for existing config
        config = self.load_config()
        if config.get("api_key"):
            print(f"\n[INFO] You already have CmdrData configured")
            print(f"       Email: {config.get('email', 'unknown')}")
            use_existing = input("\nUse existing configuration? (Y/n): ").lower()
            if use_existing != "n":
                return True

        # Main menu
        print("\nChoose an option:")
        print("1. Create new account (recommended)")
        print("2. Login with existing account")
        print("3. Enter API key manually")
        print("4. Skip setup")

        choice = input("\nYour choice (1-4): ").strip()

        if choice == "1":
            # Register new account
            auth_data = self.register_user()
            if auth_data:
                access_token = auth_data.get("access_token")
                user_info = auth_data.get("user", {})

                # Create API key
                api_key = self.create_api_key(access_token)
                if api_key and api_key != "existing-key-hidden":
                    # Save configuration
                    config = {
                        "api_key": api_key,
                        "email": user_info.get("email"),
                        "api_url": self.api_url,
                    }
                    self.save_config(config)

                    print("\n" + "=" * 60)
                    print("SUCCESS! CmdrData is configured")
                    print(f"\nYour API key: {api_key}")
                    print(f"Dashboard: https://app.cmdrdata.ai")
                    print("\nConfiguration saved to:", self.config_file)
                    return True

        elif choice == "2":
            # Login existing account
            auth_data = self.login_user()
            if auth_data:
                access_token = auth_data.get("access_token")
                user_info = auth_data.get("user", {})

                # Create or get API key
                api_key = self.create_api_key(access_token)
                if api_key:
                    if api_key == "existing-key-hidden":
                        print(
                            "\n[WARNING] You have an existing API key but we can't retrieve it"
                        )
                        print(
                            "          Please get it from: https://app.cmdrdata.ai/dashboard/api-keys"
                        )
                        manual_key = input("\nEnter your API key: ").strip()
                        if manual_key:
                            api_key = manual_key
                        else:
                            return False

                    # Save configuration
                    config = {
                        "api_key": api_key,
                        "email": user_info.get("email"),
                        "api_url": self.api_url,
                    }
                    self.save_config(config)

                    print("\n" + "=" * 60)
                    print("SUCCESS! CmdrData is configured")
                    print(f"\nDashboard: https://app.cmdrdata.ai")
                    print("\nConfiguration saved to:", self.config_file)
                    return True

        elif choice == "3":
            # Manual API key entry
            print("\n=== Manual API Key Configuration ===")
            api_key = input("Enter your CmdrData API key: ").strip()

            if api_key:
                config = {"api_key": api_key, "api_url": self.api_url}
                self.save_config(config)

                print("\n[OK] Configuration saved")
                return True

        elif choice == "4":
            # Skip setup
            print("\n[INFO] Setup skipped. You can run this again anytime.")
            return False

        print("\n[ERROR] Setup failed. Please try again.")
        return False

    def get_api_key(self) -> Optional[str]:
        """Get the configured API key"""
        config = self.load_config()
        return config.get("api_key")


def main():
    """CLI entry point"""
    # Allow testing with local server
    if "--local" in sys.argv:
        api_url = "http://127.0.0.1:8000"
        print(f"[INFO] Using local server: {api_url}")
    else:
        api_url = CMDRDATA_API_URL

    setup = CmdrDataSetup(api_url)

    if setup.interactive_setup():
        print("\nYou can now use CmdrData in your code:")
        print("```python")
        print("from cmdrdata_anthropic import TrackedAnthropic")
        print("client = TrackedAnthropic()  # Auto-loads config")
        print("```")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
