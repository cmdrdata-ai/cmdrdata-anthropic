"""
Auto-configuration support for CmdrData SDKs
Loads API keys from multiple sources in priority order
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class AutoConfig:
    """Automatic configuration loader for CmdrData"""

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Load CmdrData configuration from multiple sources:
        1. Environment variables (highest priority)
        2. .env file in current directory
        3. ~/.cmdrdata/config.json (from CLI setup)
        4. .cmdrdata.json in current directory

        Returns dict with 'api_key' and 'api_url' keys
        """
        config = {"api_key": None, "api_url": "https://api.cmdrdata.ai"}

        # 1. Check environment variables (highest priority)
        if os.getenv("CMDRDATA_API_KEY"):
            config["api_key"] = os.getenv("CMDRDATA_API_KEY")
        if os.getenv("CMDRDATA_API_URL"):
            config["api_url"] = os.getenv("CMDRDATA_API_URL")

        # 2. Check .env file in current directory
        env_file = Path(".env")
        if env_file.exists() and not config["api_key"]:
            try:
                with open(env_file) as f:
                    for line in f:
                        if line.startswith("CMDRDATA_API_KEY="):
                            config["api_key"] = line.split("=", 1)[1].strip()
                        elif line.startswith("CMDRDATA_API_URL="):
                            config["api_url"] = line.split("=", 1)[1].strip()
            except:
                pass

        # 3. Check user home config (from CLI setup)
        home_config = Path.home() / ".cmdrdata" / "config.json"
        if home_config.exists() and not config["api_key"]:
            try:
                with open(home_config) as f:
                    home_data = json.load(f)
                    if not config["api_key"]:
                        config["api_key"] = home_data.get("api_key")
                    if home_data.get("api_url"):
                        config["api_url"] = home_data.get("api_url", config["api_url"])
            except:
                pass

        # 4. Check project-level config
        project_config = Path(".cmdrdata.json")
        if project_config.exists() and not config["api_key"]:
            try:
                with open(project_config) as f:
                    project_data = json.load(f)
                    if not config["api_key"]:
                        config["api_key"] = project_data.get("api_key")
                    if project_data.get("api_url"):
                        config["api_url"] = project_data.get(
                            "api_url", config["api_url"]
                        )
            except:
                pass

        return config

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get the CmdrData API key from any configured source"""
        config = AutoConfig.load_config()
        return config.get("api_key")

    @staticmethod
    def get_api_url() -> str:
        """Get the CmdrData API URL (defaults to production)"""
        config = AutoConfig.load_config()
        return config.get("api_url", "https://api.cmdrdata.ai")

    @staticmethod
    def is_configured() -> bool:
        """Check if CmdrData is configured with an API key"""
        return AutoConfig.get_api_key() is not None

    @staticmethod
    def prompt_setup() -> bool:
        """
        Prompt user to run setup if not configured
        Returns True if setup was successful
        """
        if AutoConfig.is_configured():
            return True

        print("\n" + "=" * 60)
        print("CmdrData is not configured!")
        print("=" * 60)
        print("\nYou have several options:")
        print("\n1. Run interactive setup (recommended):")
        print("   python -m cmdrdata_anthropic.setup")
        print("\n2. Set environment variable:")
        print("   export CMDRDATA_API_KEY='your-api-key'")
        print("\n3. Create ~/.cmdrdata/config.json:")
        print('   {"api_key": "your-api-key"}')
        print("\n4. Pass API key directly in code:")
        print("   client = TrackedAnthropic(cmdrdata_api_key='your-key')")
        print("\nGet your free API key at: https://app.cmdrdata.ai")
        print("=" * 60)

        return False
