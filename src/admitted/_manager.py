from __future__ import annotations
import atexit
import logging
from os import getenv
from pathlib import Path
from platform import system, processor
import subprocess
import sys
from tempfile import TemporaryFile
from typing import Any
from warnings import warn
from zipfile import ZipFile

from selenium.webdriver.chrome import options, webdriver
from selenium.webdriver.support.wait import WebDriverWait

from . import _service, _url
from .element import Element
from .exceptions import ChromeDriverVersionError

HOME = Path.home()
logger = logging.getLogger(__name__)


class ChromeManager(webdriver.WebDriver):
    """Container to manage the Selenium Chrome WebDriver instance and ChromeDriver executable.

    Google Chrome should already be installed, and this class will manage upgrading ChromeDriver
    to the appropriate version when necessary. ChromeDriver is installed into a user binary
    folder so that admin/superuser rights are not required.

    Attributes
      driver (selenium.webdriver.Chrome): the Selenium Chrome WebDriver instance
      debugger_url (str): the URL to access the ChromeDriver debugger

    Methods
      navigate(url): navigates Chrome to the specified URL, retrying up to `retries` times
      debug_show_page(): prints the current page to the console as text
    """

    _platform_vars = None
    # selenium.webdriver.remote.webdriver.WebDriver (grandparent of Chrome WebDriver) uses
    # `self._web_element_cls` to instantiate WebElements from the find_element(s) methods
    _web_element_cls = Element

    def __init__(self, timeout: int = 30, debug: bool = False, reuse_service: bool = False):
        """Initialize the Chrome class

        Args:
          timeout: Default timeout in seconds for wait operations.
          debug: If True, will output chromedriver.log on the desktop, suppress retries, and run NOT headless.
          reuse_service: If True and an instance of chromedriver is running, we will attach to existing process.
        """
        version = self._chromedriver_upgrade_needed()
        if version == "LATEST":
            self._install_cft()
        elif version:
            self._upgrade_chromedriver(version)

        # Start Chrome
        super().__init__(options=self._driver_options(debug), service=self._driver_service(debug, reuse_service))
        if not debug:
            logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
            logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
            logging.getLogger("filelock").setLevel(logging.WARNING)
        # TODO: move wait to elements
        self._wait = timeout

        # get PIDs of the Chromedriver and Chrome processes as they
        # tend to not properly exit when the script has completed
        chromedriver_process = self.service.process
        pids = [p.pid for p in chromedriver_process.children(recursive=True)]
        if chromedriver_process.name() == self._var.chromedriver_filename:
            pids.append(chromedriver_process.pid)
        # register a function to kill Chromedriver and Chrome at exit
        if not reuse_service:
            atexit.register(_service.kill_pids, self, pids)

    @property
    def wait(self):
        warn("The method `wait` is moving to Element/locator methods.", PendingDeprecationWarning, 2)
        if isinstance(self._wait, int):
            self._wait = ChromeWait(self, timeout=self._wait)
        return self._wait

    @property
    def _var(self):
        """Platform-specific variables for private class methods."""
        if self._platform_vars is None:
            ChromeManager._platform_vars = PlatformVariables()
        return ChromeManager._platform_vars

    def _driver_options(self, debug: bool) -> options.Options:
        chrome_options = options.Options()
        if not debug:
            chrome_options.add_argument("--headless=new")
        # using user's default user-data-dir means fewer 2FA requests
        chrome_options.add_argument(f"user-data-dir={self._var.user_data_path}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        # download PDFs rather than opening them within Chrome
        chrome_options.add_experimental_option(
            "prefs",
            {
                "plugins.always_open_pdf_externally": True,
                "download.default_directory": str(HOME / "Downloads"),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
            },
        )
        if not debug:
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
        return chrome_options

    def _driver_service(self, debug: bool, reuse_service: bool) -> _service.Service:
        return _service.Service(
            executable_path=self._var.user_bin_path / self._var.chromedriver_filename,
            log_path=(HOME / "Desktop" / "chromedriver.log") if debug else None,
            reuse_service=reuse_service,
        )

    def _chromedriver_upgrade_needed(self) -> str:
        """Compare Chrome and ChromeDriver and return the recommended ChromeDriver version if an upgrade is needed."""
        # get version of installed Chrome and ChromeDriver
        chrome_version = self._get_chrome_version()
        major_chrome_version = int(chrome_version.split(".", 1)[0])
        chromedriver_version = self._get_chromedriver_version()

        # get recommended chromedriver version
        if major_chrome_version >= 115:
            recommended = self._get_chrome_for_testing_version()
            if not recommended:
                return "LATEST"
        else:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_chrome_version}"
            recommended = _url.direct_request("GET", url).text
        if recommended == chromedriver_version:
            return ""
        chromedriver_version_parts = [int(p) for p in chromedriver_version.split(".")]
        recommended_parts = [int(p) for p in recommended.split(".")]
        if any((cd < r for cd, r in zip(chromedriver_version_parts, recommended_parts))):
            return recommended
        raise ChromeDriverVersionError(
            f"This will Never Happen\u2122: somehow we have a newer version of ChromeDriver "
            f"({chromedriver_version}) than is recommended ({recommended})."
        )

    def _get_chrome_version(self) -> str:
        """Return the current Google Chrome version on this system."""
        out = subprocess.run(self._var.chrome_version_command, stdout=subprocess.PIPE, check=False)
        if out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get Chrome version, returned {out}")
        full_chrome_version = out.stdout.decode().strip().rsplit(" ", 1)[-1]
        if not all((p.isnumeric() for p in full_chrome_version.split("."))):
            raise ChromeDriverVersionError(f"Invalid Chrome version received: '{full_chrome_version}'")
        return full_chrome_version

    def _get_chrome_for_testing_version(self) -> str:
        """Return the current Google Chrome for Testing version on this system."""
        out = subprocess.run(
            self._var.chrome_for_testing_version_command,
            stdout=subprocess.PIPE,
            check=False,
            cwd=self._var.user_bin_path,
        )
        if out.returncode == 1:
            # return code 1 probably means it's not installed
            return ""
        elif out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get Chrome for Testing version, returned {out}")
        full_chrome_for_testing_version = out.stdout.decode().strip().rsplit(" ", 1)[-1]
        if not all((p.isnumeric() for p in full_chrome_for_testing_version.split("."))):
            raise ChromeDriverVersionError(
                f"Invalid Chrome for Testing version received: '{full_chrome_for_testing_version}'"
            )
        return full_chrome_for_testing_version

    def _get_cft_urls(self) -> list[str]:
        versions = self._get_cft_versions()
        downloads = versions[-1]["downloads"]
        return [
            self._get_cft_version_download(downloads, "chrome", "LATEST"),
            self._get_cft_version_download(downloads, "chromedriver", "LATEST"),
        ]

    def _get_chromedriver_url(self, version: str) -> str:
        major_version = int(version.split(".", 1)[0])
        if major_version < 115:
            warn("Use of Chrome versions before 115 are deprecated.", DeprecationWarning, stacklevel=2)
            if self._var.platform in ("win32", "win64"):
                return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
            if self._var.platform == "mac-arm64":
                return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_mac64_m1.zip"
            if self._var.platform == "mac-x64":
                return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_mac64.zip"
            return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{self._var.platform}.zip"
        versions = self._get_cft_versions()
        for item in versions:
            if item["version"] == version:
                return self._get_cft_version_download(item["downloads"], "chromedriver", version)
        raise ChromeDriverVersionError(f"Version {version} not found in Chrome for Testing downloads.")

    @staticmethod
    def _get_cft_versions() -> list[dict[str, Any]]:
        return _url.direct_request(
            "GET", "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        ).json["versions"]

    def _get_cft_version_download(self, downloads: dict[str, Any], key: str, version: str):
        # Chrome for Testing has different platform names.
        plat = self._var.platform
        try:
            cft_url = next((dl for dl in downloads[key] if dl["platform"] == plat))["url"]
        except (StopIteration, KeyError):
            raise ChromeDriverVersionError(f"Failed getting Chrome for Testing versions for Chrome {version} on {plat}")
        return cft_url

    def _get_chromedriver_version(self) -> str:
        """Return the current ChromeDriver version on this system."""
        filepath = self._var.user_bin_path / self._var.chromedriver_filename
        if not filepath.is_file():
            # ChromeDriver is not installed
            return "0.0.0.0"
        try:
            out = subprocess.run([str(filepath), "--version"], stdout=subprocess.PIPE, check=False)
        except OSError as exc:
            # winerror 216 means chromedriver.exe is incompatible with current version of Windows
            if getattr(exc, "winerror", None) not in (None, 216):
                raise ChromeDriverVersionError(f"Failed to get ChromeDriver version: {exc}") from exc
            return "0.0.0.0"
        if out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get ChromeDriver version, returned {out}")
        chromedriver_version = out.stdout.decode().split()[1]
        return chromedriver_version

    def _upgrade_chromedriver(self, version: str) -> None:
        """Download, unzip, and install ChromeDriver."""
        url = self._get_chromedriver_url(version)
        fp = _url.direct_request("GET", url, stream=True).write_stream(TemporaryFile())
        # replace current chromedriver with downloaded version
        path = self._var.user_bin_path
        filename = self._var.chromedriver_filename
        download_file = path / filename
        download_file.unlink(missing_ok=True)
        fp.seek(0)
        with ZipFile(fp) as zip_file:
            for file in zip_file.infolist():
                this_file_name = file.filename.rsplit("/", 1)[-1]
                if file.is_dir() or not this_file_name == filename:
                    continue
                file.filename = filename
                zip_file.extract(file, path=path)
                break
        fp.close()
        download_file.chmod(0o755)
        # confirm upgrade was successful
        current_version = self._get_chromedriver_version()
        if current_version != version:
            raise ChromeDriverVersionError(f"Failed up upgrade ChromeDriver from {current_version} to {version}.")

    def _install_cft(self):
        urls = self._get_cft_urls()
        # TODO: install from the two URLs in `urls`
        raise ChromeDriverVersionError(f"Chrome for Testing is not installed. Install from {urls[0]}")

    def debug_show_page(self):
        """For debugging: Quick dump of current page content to console as text."""
        try:
            # noinspection PyPackageRequirements
            from html2text import HTML2Text  # pylint:disable=import-outside-toplevel
        except ImportError:
            print(self.page_source)
            return

        print(f"URL: {self.current_url}")
        parser = HTML2Text()
        parser.unicode_snob = True
        parser.images_to_alt = True
        parser.default_image_alt = "(IMG)"
        parser.body_width = 120
        parser.wrap_links = False
        parser.wrap_list_items = False
        parser.pad_tables = True
        parser.mark_code = True
        print(parser.handle(self.page_source))


class ChromeWait(WebDriverWait):
    # todo: move to `element`

    def until(self, method, message: str | None = None) -> bool:
        # todo: better message, `method` is not useful
        return super().until(method, message or f"Time expired waiting for {method}")

    def until_not(self, method, message: str | None = None) -> bool:
        # todo: better message, `method` is not useful
        return super().until_not(method, message or f"Time expired waiting for not {method}")


class PlatformVariables:
    """Platform-specific variables for private class methods."""

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

    def __repr__(self):
        return (
            f"PlatformVariables(platform={repr(self.platform)}, "
            f"chromedriver_filename={repr(self.chromedriver_filename)}, "
            f"user_bin_path={repr(self.user_bin_path)}, "
            f"user_data_path={repr(self.user_data_path)}, "
            f"chrome_version_command={repr(self.chrome_version_command)}, "
            f"chrome_for_testing_version_command={repr(self.chrome_for_testing_version_command)})"
        )

    def _set_windows(self):
        self.platform = "win64" if sys.maxsize > 2**32 else "win32"
        self.chromedriver_filename = "chromedriver.exe"
        self.user_bin_path = HOME / "AppData" / "Local" / "Microsoft" / "WindowsApps" / f"chrome-{self.platform}"
        local_app_data_env = getenv("LOCALAPPDATA")
        local_app_data = Path(local_app_data_env) if local_app_data_env else (HOME / "AppData" / "Local")
        self.user_data_path = str(local_app_data / "Google" / "Chrome" / "User Data")
        # although HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon /v version is recommended in various places online,
        # I have discovered that between the time that Chrome is updated and the next time that it is run, this
        # registry key is NOT updated.
        # I suspect the Google Update state for Chrome will be updated sooner...
        # {8A69D345-D564-463C-AFF1-A69D9E530F96} is the GUID for Chrome, which you can also find referenced under
        # HKCU\Software\Microsoft\Active Setup\Installed Components, HKCU\Software\Google\Update\ClientState, or
        # HKLM\SOFTWARE\Microsoft\Active Setup\Installed Components
        self.chrome_version_command = [
            "reg",
            "query",
            r"HKLM\SOFTWARE\WOW6432Node\Google\Update\ClientState\{8A69D345-D564-463C-AFF1-A69D9E530F96}",
            "/v",
            "pv",
        ]
        self.chrome_for_testing_version_command = [
            "reg",
            "query",
            r"HKCU\Software\Google\Chrome for Testing\BLBeacon",
            "/v",
            "version",
        ]

    def _set_linux(self):
        self.platform = "linux64"
        self.user_bin_path = HOME / ".local" / "bin" / f"chrome-{self.platform}"
        self.user_data_path = str(HOME / ".config" / "google-chrome" / "Default")
        self.chrome_version_command = ["google-chrome", "--version"]
        self.chrome_for_testing_version_command = ["./chrome", "--version"]

    def _set_mac(self, proc: str):
        self.platform = "mac-arm64" if proc == "arm" else "mac-x64"
        self.user_bin_path = Path("/usr/local/bin") / f"chrome-{self.platform}"
        self.user_data_path = str(HOME / "Library" / "Application Support" / "Google" / "Chrome" / "Default")
        self.chrome_version_command = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
        self.chrome_for_testing_version_command = [
            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            "--version",
        ]
