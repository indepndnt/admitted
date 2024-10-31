from __future__ import annotations
import atexit
import logging
import re
import subprocess
from tempfile import TemporaryFile
from warnings import warn
from zipfile import ZipFile

from selenium.webdriver.chrome import options, webdriver
from selenium.webdriver.support.wait import WebDriverWait

from admitted import _service, _url
from admitted.element import Element
from admitted.exceptions import ChromeDriverVersionError
from admitted._executables._platform import PlatformVariables

logger = logging.getLogger(__name__)


class ChromeManager(webdriver.WebDriver):
    """Container to manage the Selenium Chrome WebDriver instance and ChromeDriver executable.

    Google Chrome for Testing should already be installed, and this class will manage upgrading
    ChromeDriver to the appropriate version when necessary. ChromeDriver is installed into a user
    binary folder so that admin/superuser rights are not required.

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
        self._check_chrome_for_testing()

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
                "download.default_directory": str(self._var.home / "Downloads"),
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
            log_path=(self._var.home / "Desktop" / "chromedriver.log") if debug else None,
            reuse_service=reuse_service,
        )

    def _check_chrome_for_testing(self) -> None:
        """Compare Chrome and ChromeDriver and install or upgrade as needed."""

        cft_version = self._get_chrome_for_testing_version()
        if not cft_version:
            cft_version = self._install_chrome_for_testing()

        chromedriver_version = self._get_chromedriver_version()
        if cft_version != chromedriver_version:
            self._install_chromedriver()

    def _get_chrome_for_testing_version(self) -> str:
        """Return the current Google Chrome for Testing version on this system."""
        out = subprocess.run(
            self._var.cft_version_command,
            stdout=subprocess.PIPE,
            check=False,
            cwd=self._var.user_bin_path,
        )
        if out.returncode == 1:
            # return code 1 probably means it's not installed
            return ""
        elif out.returncode != 0:
            raise ChromeDriverVersionError(f"Failed to get Chrome for Testing version, returned {out}")
        result = out.stdout.decode()
        match = re.match(r"Google Chrome for Testing ([\d.]+).*", result)
        if not match:
            raise ChromeDriverVersionError(f"Invalid Chrome for Testing version received: '{result}'")
        return match[1]

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
        result = out.stdout.decode()
        match = re.match(r"ChromeDriver ([\d.]+).*", result)
        if out.returncode != 0 or not match:
            raise ChromeDriverVersionError(f"Failed to get ChromeDriver version, returned {out}")
        return match[1]

    def _get_cft_url(self, key: str) -> str:
        if key not in self._var.download_urls:
            versions = _url.direct_request(
                "GET", "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            ).json["versions"]
            downloads = versions[-1]["downloads"]
            for pkg in downloads:
                dl = next((dl for dl in downloads[pkg] if dl["platform"] == self._var.platform), None)
                if dl:
                    self._var.download_urls[pkg] = dl["url"]
        return self._var.download_urls[key]

    def _install_chrome_for_testing(self) -> str:
        """Download, unzip, and install program into user's local bin folder."""
        url = self._get_cft_url("chrome")
        fp = _url.direct_request("GET", url, stream=True).write_stream(TemporaryFile())
        # replace current chrome-{platform} folder with downloaded version
        path = self._var.user_bin_path.parent
        folder_name = self._var.user_bin_path.name
        fp.seek(0)
        with ZipFile(fp) as zip_file:
            if any((f.parts[0] != folder_name for f in zip_file.filelist)):
                raise ChromeDriverVersionError(f"Unexpected content in download {url}")
            zip_file.extractall(path)
        fp.close()
        return self._get_chrome_for_testing_version()

    def _install_chromedriver(self) -> None:
        """Download, unzip, and install program into user's local bin folder."""
        url = self._get_cft_url("chromedriver")
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

    def debug_show_page(self):
        """For debugging: Quick dump of current page content to console as text."""
        try:
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
