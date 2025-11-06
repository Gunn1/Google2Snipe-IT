"""
Configuration module for Google2Snipe-IT.

Centralizes all configurable values from environment variables with sensible defaults.
Validates required configuration at startup.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for Google2Snipe-IT application."""

    # ==================== SNIPE-IT Configuration ====================
    API_TOKEN = os.getenv("API_TOKEN")
    ENDPOINT_URL = os.getenv("ENDPOINT_URL")

    # Snipe-IT custom field IDs (instance-specific)
    # These should match your Snipe-IT instance's custom field IDs
    SNIPE_IT_FIELD_MAC_ADDRESS = os.getenv("SNIPE_IT_FIELD_MAC_ADDRESS", "_snipeit_mac_address_1")
    SNIPE_IT_FIELD_SYNC_DATE = os.getenv("SNIPE_IT_FIELD_SYNC_DATE", "_snipeit_sync_date_9")
    SNIPE_IT_FIELD_IP_ADDRESS = os.getenv("SNIPE_IT_FIELD_IP_ADDRESS", "_snipeit_ip_address_3")
    SNIPE_IT_FIELD_USER = os.getenv("SNIPE_IT_FIELD_USER", "_snipeit_user_10")

    # Snipe-IT IDs (instance-specific)
    SNIPE_IT_DEFAULT_MODEL_ID = int(os.getenv("SNIPE_IT_DEFAULT_MODEL_ID", "87"))
    SNIPE_IT_FIELDSET_ID = int(os.getenv("SNIPE_IT_FIELDSET_ID", "9"))
    SNIPE_IT_DEFAULT_STATUS_ID = int(os.getenv("SNIPE_IT_DEFAULT_STATUS_ID", "2"))
    SNIPE_IT_ACTIVE_STATUS = os.getenv("SNIPE_IT_ACTIVE_STATUS", "ACTIVE")

    # ==================== Google Workspace Configuration ====================
    GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    GOOGLE_DELEGATED_ADMIN = os.getenv("DELEGATED_ADMIN")
    GOOGLE_CHROMEOS_PAGE_SIZE = int(os.getenv("GOOGLE_CHROMEOS_PAGE_SIZE", "300"))
    GOOGLE_CHROMEOS_PROJECTION = os.getenv("GOOGLE_CHROMEOS_PROJECTION", "FULL")

    # ==================== Gemini AI Configuration ====================
    GEMINI_API_KEY = os.getenv("Gemini_APIKEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_CATEGORIES = os.getenv(
        "GEMINI_CATEGORIES",
        "IMac,Tablets,Mobile Devices,Servers,Networking Equipment,Printers & Scanners,Desktop,Chromebook"
    )

    # ==================== Retry Configuration ====================
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "4"))
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "20"))
    RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "1.0"))

    # ==================== Logging Configuration ====================
    LOG_FILE = os.getenv("LOG_FILE", "snipeit_errors.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
    LOG_FORMAT = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # ==================== Application Configuration ====================
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # "development" or "production"

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate required configuration is present.

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        # Required Snipe-IT config
        if not cls.API_TOKEN:
            errors.append("API_TOKEN environment variable is required")
        if not cls.ENDPOINT_URL:
            errors.append("ENDPOINT_URL environment variable is required")

        # Required Google config
        if not cls.GOOGLE_DELEGATED_ADMIN:
            errors.append("DELEGATED_ADMIN environment variable is required")
        if not os.path.exists(cls.GOOGLE_SERVICE_ACCOUNT_FILE):
            errors.append(
                f"Google service account file not found: {cls.GOOGLE_SERVICE_ACCOUNT_FILE}"
            )

        # Required Gemini config
        if not cls.GEMINI_API_KEY:
            errors.append("Gemini_APIKEY environment variable is required")

        return len(errors) == 0, errors

    @classmethod
    def print_config(cls, include_secrets=False) -> None:
        """
        Print current configuration for debugging.

        Args:
            include_secrets: If True, include API keys (use with caution)
        """
        print("\n" + "=" * 60)
        print("Google2Snipe-IT Configuration")
        print("=" * 60)

        config_items = {
            "Environment": cls.ENVIRONMENT,
            "Debug Mode": cls.DEBUG,
            "Dry Run": cls.DRY_RUN,
            "Snipe-IT Endpoint": cls.ENDPOINT_URL,
            "Google Delegated Admin": cls.GOOGLE_DELEGATED_ADMIN,
            "Google Service Account File": cls.GOOGLE_SERVICE_ACCOUNT_FILE,
            "Snipe-IT Default Model ID": cls.SNIPE_IT_DEFAULT_MODEL_ID,
            "Snipe-IT Fieldset ID": cls.SNIPE_IT_FIELDSET_ID,
            "Log File": cls.LOG_FILE,
            "Log Level": cls.LOG_LEVEL,
            "Max Retries": cls.MAX_RETRIES,
            "Retry Delay (seconds)": cls.RETRY_DELAY_SECONDS,
        }

        for key, value in config_items.items():
            print(f"  {key:<35} {value}")

        if include_secrets:
            print(f"  {'API Token':<35} {cls.API_TOKEN[:20]}..." if cls.API_TOKEN else "  NOT SET")
            print(f"  {'Gemini API Key':<35} {cls.GEMINI_API_KEY[:20]}..." if cls.GEMINI_API_KEY else "  NOT SET")

        print("=" * 60 + "\n")
