from __future__ import annotations
import errno
from os import kill
from pathlib import Path
import signal
from time import sleep
from subprocess import DEVNULL, PIPE, Popen
import psutil
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common import utils
from .exceptions import ChromeDriverServiceError


class Service:
    """Object that manages the ChromeDriver process"""

    start_err = "Please see https://chromedriver.chromium.org/home"

    def __init__(self, executable_path: Path, log_path: Path | None, reuse_service: bool = False):
        """Creates a new instance of the Service

        Args:
          executable_path: Path to the ChromeDriver
          log_path: Path for the chromedriver service to log to
          reuse_service: If True and an existing ChromeDriver instance is running, it will be reused
        """
        print("Start Service.__init__")
        self.path = executable_path
        self.port = None
        self.process = None
        self.subprocess = None
        if reuse_service is True:
            self.process = self._find_chromedriver_process(executable_path.name)
        if self.process is not None:
            self.path = Path(self.process.exe())
            try:
                connection = next((conn for conn in self.process.connections("inet4") if conn.status == "LISTEN"))
            except StopIteration:
                raise ChromeDriverServiceError(f"Cannot find connection for Service PID {self.process.pid}.")
            self.port = connection.laddr.port
            self.cmdline = self.process.cmdline()
        else:
            self.port = utils.free_port()
            service_args = ["--silent"] if log_path is None else ["--verbose", f"--log-path={log_path}"]
            self.cmdline = [str(executable_path), f"--port={self.port}"] + service_args
        self.service_url = f"http://localhost:{self.port}"
        print("Completed Service.__init__")

    @staticmethod
    def _find_chromedriver_process(name: str) -> psutil.Process | None:
        """Return a process of a running ChromeDriver instance."""
        for process in psutil.process_iter(["name"]):
            # noinspection PyUnresolvedReferences
            if process.info["name"] == name and process.is_running():
                return process
        return None

    def start(self):
        """Starts the Service.

        Exceptions:
          ChromeDriverServiceError: Raised when it can't either start or connect to the service
        """
        if self.process is not None:
            return
        try:
            self.subprocess = Popen(self.cmdline, stdout=DEVNULL, stderr=DEVNULL, stdin=PIPE)
        except OSError as err:
            if err.errno == errno.ENOENT:
                err.strerror = f"Executable needs to be in PATH. {self.start_err}"
            elif err.errno == errno.EACCES:
                err.strerror = f"Executable may have wrong permissions. {self.start_err}"
            raise
        self.process = psutil.Process(pid=self.subprocess.pid)
        # wait for process to start up, raise error if it exits or can't connect within 30 seconds
        for _ in range(60):
            self.assert_process_still_running()
            if self.is_connectable():
                break
            sleep(0.5)
        else:
            self.stop()
            raise ChromeDriverServiceError(f"Cannot connect to the Service {self.path}.")

    def assert_process_still_running(self):
        if not self.process.is_running():
            self.stop()
            raise ChromeDriverServiceError(f"Service {self.path} unexpectedly exited.")

    def is_connectable(self):
        return utils.is_connectable(self.port)

    def send_remote_shutdown_command(self):
        from urllib import request
        from urllib.error import URLError

        try:
            request.urlopen(f"{self.service_url}/shutdown")
        except URLError:
            return

        for x in range(30):
            if not self.is_connectable():
                break
            sleep(1)

    def stop(self):
        """Stops the service."""
        if self.process is None:
            return
        if self.process.is_running():
            try:
                self.send_remote_shutdown_command()
            except TypeError:
                pass
        try:
            self.process.terminate()
            self.process.wait()
            self.process.kill()
        except psutil.Error:
            # most likely psutil.NoSuchProcess
            pass
        finally:
            self.process = None

    def __del__(self):
        # `subprocess.Popen` doesn't send signal on `__del__`, so we attempt to close the
        # launched process when `__del__` is triggered.

        # noinspection PyBroadException,TryExceptPass
        try:
            self.stop()
        except Exception:
            pass

    def env_path(self) -> str:
        return str(self.path)


def kill_pids(driver: webdriver.WebDriver, process_ids: list[int]) -> None:
    """Function registered in `atexit` to kill Chromedriver and Chrome so we don't leave orphan processes."""
    # first let the ChromeDriver service shut itself down
    # WebDriver.quit first sends a "quit" command to ChromeDriver, then calls Service.stop
    driver.quit()
    # for all spawned Chrome/ChromeDriver processes, first ask nicely, then force terminate
    # although Service.stop should have shut everything down, sometimes it leaves orphans
    for process_signal in (getattr(signal, s) for s in ("SIGTERM", "SIGKILL") if hasattr(signal, s)):
        for pid in process_ids:
            if not psutil.pid_exists(pid):
                continue
            try:
                kill(pid, process_signal)
            except ProcessLookupError:
                pass
        process_ids = [pid for pid in process_ids if psutil.pid_exists(pid)]
        if not process_ids:
            break
        sleep(0.1)
