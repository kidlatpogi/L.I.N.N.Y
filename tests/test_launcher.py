"""Tests for AppLauncher alias mapping and resolution."""

from linny.system.launcher import AppLauncher


def test_alias_resolution():
    aliases = {
        "browser": "https://google.com",
        "code": "C:\\VSCode\\code.exe",
        "spotify": "spotify:",
    }
    launcher = AppLauncher(aliases)

    assert launcher.resolve_target("browser") == "https://google.com"
    assert launcher.resolve_target("BROWSER") == "https://google.com"
    assert launcher.resolve_target("code") == "C:\\VSCode\\code.exe"
    assert launcher.resolve_target("unknown_app") == "unknown_app"


def test_empty_launch():
    launcher = AppLauncher({})
    success, msg = launcher.launch("")
    assert success is False
