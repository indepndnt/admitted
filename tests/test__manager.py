import pytest
from pathlib import Path
import subprocess
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome import webdriver

from admitted import _service, _url, models
from admitted._executables import _manager, _platform


class MockProcess:
    def __init__(self):
        self.pid = -1
        self.wait = lambda: None
        self.kill = lambda: None
        self.name = lambda: "chromedriver"
        self.children = lambda **kw: []

    def terminate(self):
        self.pid = "terminated"

    def is_running(self):
        return self.pid != "terminated"


def mock_run(output: bytes | None = None):
    # noinspection PyUnusedLocal
    def subprocess_run(command, stdout, check, cwd):
        """mock of subprocess.run, which is globally removed for tests"""

        class MockRun:
            returncode = 0
            stdout = output or b"Google Chrome for Testing 42.42.42.42"

        return MockRun()

    return subprocess_run


def test_platform_variables():
    # Antecedent
    instances = [
        _platform.PlatformVariables(),
        _platform.PlatformVariables(),
        _platform.PlatformVariables(),
        _platform.PlatformVariables(),
    ]

    # Behavior
    instances[1]._set_windows()
    instances[2]._set_mac("not-arm")
    instances[3]._set_linux()

    # Consequence
    assert all((obj.platform in ("win32", "win64", "linux64", "mac-x64", "mac-arm64") for obj in instances))
    assert all((obj.chromedriver_filename in ("chromedriver", "chromedriver.exe") for obj in instances))
    assert all((isinstance(obj.user_bin_path, Path) for obj in instances))
    assert all((isinstance(obj.user_data_path, str) for obj in instances))
    assert all(
        (
            isinstance(obj.cft_version_command, list) and all((isinstance(o, str) for o in obj.cft_version_command))
            for obj in instances
        )
    )


def test_chrome_wait(chromedriver):
    # Antecedent: an instance of ChromeWait
    instance = _manager.ChromeWait(chromedriver(), 0, 0.001)

    # Behavior
    until_result = instance.until(lambda _: "until")
    until_not_result = instance.until_not(lambda _: 0)

    # Consequence
    assert until_result == "until"
    assert until_not_result == 0
    with pytest.raises(TimeoutException, match=r"^Message: Time expired waiting for .*"):
        instance.until(lambda _: None)
    with pytest.raises(TimeoutException, match=r"^Message: Time expired waiting for .*"):
        instance.until_not(lambda _: 1)


def test_upgrade_chromedriver(monkeypatch, tmp_path):
    # Antecedent: an instance of ChromeManager

    def mock_direct_request(m, u, **kw):
        # noinspection PyTypeChecker
        response = models.Response(url="", status=200, reason="OK", headers=None)
        if u.endswith("downloads.json"):
            response._json = {
                "versions": [
                    {
                        "downloads": {
                            pkg: [
                                {"platform": "linux64", "url": ""},
                                {"platform": "mac-arm64", "url": ""},
                                {"platform": "mac-x64", "url": ""},
                                {"platform": "win32", "url": ""},
                                {"platform": "win64", "url": ""},
                            ]
                            for pkg in ("chrome", "chromedriver", "chrome-headless-shell")
                        }
                    }
                ]
            }
        else:
            # force the call to direct_request to return a mock chromedriver zip file
            response._content = (
                b"PK\x03\x04\x14\x00\x00\x00\x08\x00\xc7j=Uh\x1f\xac\x8d\x0e\x00\x00\x00\x0c\x00\x00\x00\x11\x00\x00"
                b"\x00chromedriver_testK\xce(\xca\xcfMM)\xca,K-\x02\x00PK\x01\x02\x14\x03\x14\x00\x00\x00\x08\x00\xc7"
                b"j=Uh\x1f\xac\x8d\x0e\x00\x00\x00\x0c\x00\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4"
                b"\x81\x00\x00\x00\x00chromedriver_testPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00?\x00\x00\x00=\x00"
                b"\x00\x00\x00\x00"
            )
        return response

    monkeypatch.setattr(_url, "direct_request", mock_direct_request)
    # set platform variables such that ChromeManager will expect what's in our zip file
    _manager.ChromeManager._platform_vars = _platform.PlatformVariables()
    _manager.ChromeManager._platform_vars.chromedriver_filename = "chromedriver_test"
    _manager.ChromeManager._platform_vars.user_bin_path = tmp_path
    # force calls to subprocess.run to return our chrome/chromedriver version of 42.42.42.42
    subprocess.run = mock_run()
    # create the instance
    instance = object.__new__(_manager.ChromeManager)

    # Behavior: call the _upgrade_chromedriver method
    instance._install_chromedriver()
    subprocess.run = None

    # Consequence: ChromeManager downloaded and installed chromedriver version 42.42.42.42
    file = tmp_path / "chromedriver_test"
    assert file.is_file()
    assert file.read_bytes() == b"chromedriver"


def test_get_chrome_version():
    # Antecedent: an instance of ChromeManager
    subprocess.run = mock_run()
    _manager.ChromeManager._platform_vars = _platform.PlatformVariables()
    instance = object.__new__(_manager.ChromeManager)

    # Behavior
    version = instance._get_chrome_for_testing_version()
    subprocess.run = None

    # Consequence
    assert version == "42.42.42.42"


def test_instantiate_chrome_manager(monkeypatch):
    # Antecedent: an environment for instantiating ChromeManager
    monkeypatch.setattr(webdriver.WebDriver, "start_session", lambda *a, **kw: None)
    monkeypatch.setattr(_manager.ChromeManager, "_check_chrome_for_testing", lambda *a: None)
    # noinspection PyTypeChecker
    response = models.Response(url="", status=200, reason="OK", headers=None)
    response._text = "42.42.42.43"
    monkeypatch.setattr(_url, "direct_request", lambda *a, **kw: response)
    subprocess.run = mock_run()

    def mock_start(self):
        self.process = MockProcess()

    monkeypatch.setattr(_service.Service, "start", mock_start)

    # Behavior: ChromeManager is instantiated and then shut down
    instance = _manager.ChromeManager(0)
    instance.service.process.pid = "running"
    subprocess.run = None
    # pre-acquire assertion values so they're not lost when kill_pids calls quit
    has_service_process = instance.service.process
    # trigger kill_pids
    _service.kill_pids(instance, [])

    # Consequence: no exceptions, instance has attributes created in __init__, and process.terminate was called
    assert has_service_process.pid == "terminated"
