from __future__ import annotations
from os import getenv
from pathlib import Path
from platform import system, processor
import sys
from admitted.exceptions import ChromeDriverVersionError


class PlatformVariables:
    """Platform-specific variables for private class methods."""

    home = Path.home()

    def __init__(self):
        self.chromedriver_filename: str = "chromedriver"
        system_type = system()
        if system_type == "Windows":
            self._set_windows()
        elif system_type == "Linux":
            self._set_linux()
        elif system_type == "Darwin":
            processor_type = processor()
            self._set_mac(processor_type)
        else:
            raise ChromeDriverVersionError(f"{system()} operating system not supported.")

        self.download_urls = {}

    def __repr__(self):
        return (
            f"PlatformVariables(platform={repr(self.platform)}, "
            f"chromedriver_filename={repr(self.chromedriver_filename)}, "
            f"user_bin_path={repr(self.user_bin_path)}, "
            f"user_data_path={repr(self.user_data_path)}, "
            f"chrome_for_testing_version_command={repr(self.cft_version_command)})"
        )

    def _set_windows(self):
        self.platform = "win64" if sys.maxsize > 2**32 else "win32"
        self.chromedriver_filename = "chromedriver.exe"
        self.user_bin_path = self.home / "AppData" / "Local" / "Microsoft" / "WindowsApps" / f"chrome-{self.platform}"
        local_app_data_env = getenv("LOCALAPPDATA")
        local_app_data = Path(local_app_data_env) if local_app_data_env else (self.home / "AppData" / "Local")
        self.user_data_path = str(local_app_data / "Google" / "Chrome" / "User Data")
        self.cft_version_command = [
            "reg",
            "query",
            r"HKCU\Software\Google\Chrome for Testing\BLBeacon",
            "/v",
            "version",
        ]

    def _set_linux(self):
        self.platform = "linux64"
        self.user_bin_path = self.home / ".local" / "bin" / f"chrome-{self.platform}"
        self.user_data_path = str(self.home / ".config" / "google-chrome" / "Default")
        self.cft_version_command = ["./chrome", "--version"]

    def _set_mac(self, proc: str):
        self.platform = "mac-arm64" if proc == "arm" else "mac-x64"
        self.user_bin_path = Path("/usr/local/bin") / f"chrome-{self.platform}"
        self.user_data_path = str(self.home / "Library" / "Application Support" / "Google" / "Chrome" / "Default")
        self.cft_version_command = [
            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            "--version",
        ]
