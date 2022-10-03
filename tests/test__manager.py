import pytest
from pathlib import Path
import subprocess
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome import service, webdriver
from webfetch import _manager, _outside, models


class Mock:
    def __init__(self):
        self.session_id = "test_driver"
        self.pid = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.wait = lambda: None
        self.kill = lambda: None

    def terminate(self):
        self.session_id = "terminated"


def mock_run(command, stdout, check):
    class MockRun:
        returncode = 0
        stdout = b"Chrome(Driver) 42.42.42.42"

    return MockRun()


def test_platform_variables():
    # Antecedent
    instances = [
        _manager.PlatformVariables(),
        _manager.PlatformVariables(),
        _manager.PlatformVariables(),
        _manager.PlatformVariables(),
    ]

    # Behavior
    instances[1]._set_windows()
    instances[2]._set_mac("not-arm")
    instances[3]._set_linux()

    # Consequence
    assert all((obj.platform in ("win32", "linux64", "mac64", "mac64_m1") for obj in instances))
    assert all((obj.chromedriver_filename in ("chromedriver", "chromedriver.exe") for obj in instances))
    assert all((isinstance(obj.user_bin_path, Path) for obj in instances))
    assert all((isinstance(obj.user_data_path, str) for obj in instances))
    assert all(
        (
            isinstance(obj.chrome_version_command, list)
            and all((isinstance(o, str) for o in obj.chrome_version_command))
            for obj in instances
        )
    )


def test_chrome_wait():
    # Antecedent
    instance = _manager.ChromeWait(Mock(), 0, 0.001)

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
    # Antecedent
    zip_content = (
        b"PK\x03\x04\x14\x00\x00\x00\x08\x00\xc7j=Uh\x1f\xac\x8d\x0e\x00\x00\x00\x0c\x00\x00\x00\x11\x00\x00\x00"
        b"chromedriver_testK\xce(\xca\xcfMM)\xca,K-\x02\x00PK\x01\x02\x14\x03\x14\x00\x00\x00\x08\x00\xc7j=Uh\x1f\xac"
        b"\x8d\x0e\x00\x00\x00\x0c\x00\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4\x81\x00\x00\x00\x00"
        b"chromedriver_testPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00?\x00\x00\x00=\x00\x00\x00\x00\x00"
    )
    response = models.Response("", 200, "OK", None)
    response._content = zip_content
    _manager.ChromeManager._platform_vars = _manager.PlatformVariables()
    _manager.ChromeManager._platform_vars.chromedriver_filename = "chromedriver_test"
    _manager.ChromeManager._platform_vars.user_bin_path = tmp_path
    monkeypatch.setattr(_outside, "outside_request", lambda *a, **kw: response)
    subprocess.run = mock_run
    instance = object.__new__(_manager.ChromeManager)

    # Behavior
    instance._upgrade_chromedriver("42.42.42.42")
    subprocess.run = None

    # Consequence
    file = tmp_path / "chromedriver_test"
    assert file.is_file()
    assert file.read_bytes() == b"chromedriver"


def test_get_chrome_version(monkeypatch):
    # Antecedent
    subprocess.run = mock_run
    _manager.ChromeManager._platform_vars = _manager.PlatformVariables()
    instance = object.__new__(_manager.ChromeManager)

    # Behavior
    version = instance._get_chrome_version()
    subprocess.run = None

    # Consequence
    assert version == "42"


def test_instantiate_chrome_manager(monkeypatch):
    # Antecedent
    monkeypatch.setattr(webdriver.WebDriver, "start_session", lambda *a, **kw: None)
    monkeypatch.setattr(_manager.ChromeManager, "_upgrade_chromedriver", lambda *a: None)
    response = models.Response("", 200, "OK", None)
    response._text = "42.42.42.43"
    monkeypatch.setattr(_outside, "outside_request", lambda *args: response)
    subprocess.run = mock_run
    service.Service.start = lambda _: None
    service.Service.process = Mock()

    # Behavior
    instance = _manager.ChromeManager(0)
    subprocess.run = None
    has_chrome_wait_instance = isinstance(instance.wait, _manager.ChromeWait)
    has_service_process = instance.service.process
    # trigger kill_pids
    _manager.kill_pids(instance, [])

    # Consequence
    assert has_chrome_wait_instance is True
    assert has_service_process.session_id == "terminated"
