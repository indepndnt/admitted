from __future__ import annotations
import atexit
import logging
from os import getenv, kill
from pathlib import Path
from platform import system, processor
from signal import SIGKILL, SIGTERM
import subprocess
from tempfile import TemporaryFile
import time
from typing import List, Any, Iterable
from zipfile import ZipFile

import psutil
from requests import get as get_request
from selenium.common.exceptions import WebDriverException, JavascriptException
from selenium.webdriver.chrome import options, service, webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

from .constants import DEFAULT_WINDOW_ATTRIBUTES
from .exceptions import ChromeDriverVersionError

HOME = Path.home()
logger = logging.getLogger(__name__)


class Element(WebElement):
    """Version of WebElement that returns self from click, clear, and send_keys."""

    def click(self) -> "Element":
        super().click()
        return self

    def clear(self) -> "Element":
        super().clear()
        # allow element to settle down before following up with a send_keys or other action
        time.sleep(0.1)
        return self

    def send_keys(self, *value) -> "Element":
        super().send_keys(*value)
        return self


# selenium.webdriver.remote.webdriver.WebDriver (grandparent of Chrome WebDriver) uses
# `self._web_element_cls` to instantiate WebElements from the find_element(s) methods
webdriver.WebDriver._web_element_cls = Element


class PlatformVariables:
    """Platform-specific variables for private class methods."""

    def __init__(self):
        self.chromedriver_filename: str = "chromedriver"
        system_type = system().lower()
        if system_type == "windows":
            self._set_windows()
        elif system_type == "linux":
            self._set_linux()
        elif system_type == "darwin":
            processor_type = processor().lower()
            self._set_mac(processor_type)
        else:
            raise ChromeDriverVersionError(f"{system()} operating system not supported.")

    def _set_windows(self):
        self.platform = "win32"
        self.chromedriver_filename = "chromedriver.exe"
        self.user_bin_path = HOME / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        local_app_data_env = getenv("LOCALAPPDATA")
        local_app_data = Path(local_app_data_env) if local_app_data_env else (HOME / "AppData" / "Local")
        self.user_data_path = str(local_app_data / "Google" / "Chrome" / "User Data")
        self.chrome_version_command = [
            "reg",
            "query",
            "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon",
            "/v",
            "version",
        ]

    def _set_linux(self):
        self.platform = "linux64"
        self.user_bin_path = HOME / ".local" / "bin"
        self.user_data_path = str(HOME / ".config" / "google-chrome" / "Default")
        self.chrome_version_command = ["google-chrome", "--version"]

    def _set_mac(self, proc: str):
        self.platform = "mac64_m1" if proc == "arm" else "mac64"
        self.user_bin_path = Path("/usr/local/bin")
        self.user_data_path = str(HOME / "Library" / "Application Support" / "Google" / "Chrome" / "Default")
        self.chrome_version_command = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]


class ChromeWait(WebDriverWait):
    def until(self, method, message: str | None = None):
        super().until(method, message or f"Time expired waiting for {method}")

    def until_not(self, method, message: str | None = None):
        super().until_not(method, message or f"Time expired waiting for not {method}")


class ChromeManager:
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

    def __init__(self, retries: int = 3, timeout: int = 30, debug: bool = False):
        """Initialize the Chrome class

        Args:
          retries: Number of times the `navigate` method should try to open the requested URL.
          timeout: Default timeout in seconds for wait operations.
          debug: If True, will output chromedriver.log on the desktop and suppress retries.
        """
        version = self._chromedriver_upgrade_needed()
        if version:
            self._upgrade_chromedriver(version)
        self.retries = 0 if debug else retries

        # Start Chrome
        self.driver = webdriver.WebDriver(options=self._driver_options(debug), service=self._driver_service(debug))
        if not debug:
            logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
            logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
            logging.getLogger("filelock").setLevel(logging.WARNING)
        self.window = Window(self.driver)
        self.wait = ChromeWait(self.driver, timeout=timeout)
        debugger = self.driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        # noinspection HttpUrlsUsage
        self.debugger_url = f"http://{debugger}"
        logger.info("Chrome Debugger at %s", self.debugger_url)

        # get PIDs of the Chromedriver and Chrome processes as they
        # tend to not properly exit when the script has completed
        chromedriver_process = psutil.Process(self.driver.service.process.pid)
        pids = [p.pid for p in chromedriver_process.children(recursive=True)] + [chromedriver_process.pid]

        # register a function to kill Chromedriver and Chrome at exit
        def kill_pids(driver: webdriver.WebDriver, process_ids: List[int]) -> None:
            # first let the ChromeDriver service shut itself down
            driver.quit()
            # for all spawned Chrome/ChromeDriver processes, first ask nicely, then force terminate
            for signal in (SIGKILL, SIGTERM):
                for pid in process_ids:
                    if not psutil.pid_exists(pid):
                        continue
                    try:
                        kill(pid, signal)
                    except ProcessLookupError:
                        pass
                process_ids = [pid for pid in process_ids if psutil.pid_exists(pid)]
                if not process_ids:
                    break
                time.sleep(0.1)

        atexit.register(kill_pids, self.driver, pids)

    @property
    def _var(self):
        """Platform-specific variables for private class methods."""
        if self._platform_vars is None:
            ChromeManager._platform_vars = PlatformVariables()
        return ChromeManager._platform_vars

    def _driver_options(self, debug: bool) -> options.Options:
        chrome_options = options.Options()
        chrome_options.headless = True
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

    def _driver_service(self, debug: bool) -> service.Service:
        return service.Service(
            executable_path=str(self._var.user_bin_path / self._var.chromedriver_filename),
            service_args=["--verbose" if debug else "--silent"],
            log_path=str(HOME / "Desktop" / "chromedriver.log") if debug else None,
        )

    def _chromedriver_upgrade_needed(self) -> str:
        """Compare Chrome and ChromeDriver and return the recommended ChromeDriver version if an upgrade is needed."""
        # get version of installed Chrome and ChromeDriver
        chrome_version = self._get_chrome_version()
        chromedriver_version = self._get_chromedriver_version()

        # get recommended chromedriver version
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
        response = get_request(url)
        recommended = response.text
        if recommended == chromedriver_version:
            return ""
        chromedriver_version_parts = [int(p) for p in chromedriver_version.split(".")]
        recommended_parts = [int(p) for p in recommended.split(".")]
        if any([cd < r for cd, r in zip(chromedriver_version_parts, recommended_parts)]):
            return recommended
        else:
            raise ChromeDriverVersionError(
                f"This will Never Happen\u2122: somehow we have a newer version of ChromeDriver "
                f"({chromedriver_version}) than is recommended ({recommended})."
            )

    def _get_chrome_version(self) -> str:
        """Return the current Google Chrome version on this system."""
        out = subprocess.run(self._var.chrome_version_command, stdout=subprocess.PIPE)
        if out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get Chrome version, returned {out}")
        full_chrome_version = out.stdout.decode().strip().rsplit(" ", 1)[-1]
        chrome_version = full_chrome_version.split(".", 1)[0]
        return chrome_version

    def _get_chromedriver_version(self) -> str:
        """Return the current ChromeDriver version on this system."""
        filepath = self._var.user_bin_path / self._var.chromedriver_filename
        if not filepath.is_file():
            # ChromeDriver is not installed
            return "0.0.0.0"
        out = subprocess.run([str(filepath), "--version"], stdout=subprocess.PIPE)
        if out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get ChromeDriver version, returned {out}")
        chromedriver_version = out.stdout.decode().split()[1]
        return chromedriver_version

    def _upgrade_chromedriver(self, version: str) -> None:
        """Download, unzip, and install ChromeDriver."""
        url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{self._var.platform}.zip"
        fp = TemporaryFile()
        with get_request(url, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                fp.write(chunk)
        # replace current chromedriver with downloaded version
        path = self._var.user_bin_path
        filename = self._var.chromedriver_filename
        download_file = path / filename
        download_file.unlink(missing_ok=True)
        fp.seek(0)
        with ZipFile(fp) as zip_file:
            zip_file.extract(filename, path=path)
        fp.close()
        download_file.chmod(0o755)
        # confirm upgrade was successful
        current_version = self._get_chromedriver_version()
        if current_version != version:
            raise ChromeDriverVersionError(f"Failed up upgrade ChromeDriver from {current_version} to {version}.")

    def navigate(self, url: str) -> None:
        """Navigate Chrome to the specified URL, retrying with exponential back-off.

        Args:
          url: The URL to navigate to.
        """
        retry_wait = 10
        retry = 0
        while True:
            try:
                return self.driver.get(url)
            except WebDriverException as exc:
                if retry >= self.retries:
                    logger.debug(f"Tried {retry + 1} times.")
                    raise
                retry += 1
                pause = retry_wait * (retry**2)
                logger.debug(f"Error on try {retry}: {exc}. Waiting {pause} seconds.")
                time.sleep(pause)

    def debug_show_page(self):
        """For debugging: Quick dump of current page content to console as text."""
        try:
            # noinspection PyPackageRequirements
            from html2text import HTML2Text
        except ImportError:
            print(self.driver.page_source)
            return

        print(f"URL: {self.driver.current_url}")
        parser = HTML2Text()
        parser.unicode_snob = True
        parser.images_to_alt = True
        parser.default_image_alt = "(IMG)"
        parser.body_width = 120
        parser.wrap_links = False
        parser.wrap_list_items = False
        parser.pad_tables = True
        parser.mark_code = True
        print(parser.handle(self.driver.page_source))


class Window:
    """Class to manage accessing global variables from the Chrome console"""

    def __init__(self, driver: webdriver.WebDriver):
        # shortcut to enable e.g. chrome.window.run("javascript", arg=val)
        self.run = driver.execute_script

    def __getitem__(self, item: str) -> Any:
        # shortcut to enable e.g. local_storage = chrome.window["localStorage"]
        try:
            value = self.run(f"return window.{item};")
        except JavascriptException:
            value = None
        return value

    def new_keys(self) -> Iterable[str]:
        attribs = set(self.run("return Object.keys(window);"))
        added = attribs.difference(DEFAULT_WINDOW_ATTRIBUTES)
        return sorted(added)

    def scroll_to(self, *, top: bool = False, element: WebElement = None) -> None:
        if top:
            self.run("window.scrollTo(0, 0);")
        elif element:
            self.run("arguments[0].scrollIntoView();", element)
