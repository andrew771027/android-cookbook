from android_cookbook.shell import get_current_user, get_kernel_info, get_working_directory, list_root_directory, run_shell

def test_run_shll(monkeypatch):

    captured_args = None

    def fake_run_adb(*args):
        nonlocal captured_args

        captured_args = args
        
        return "shell"
    
    monkeypatch.setattr(
        "android_cookbook.shell.run_adb",
        fake_run_adb
    )

    result = run_shell("emulator-5554", "whoami")

    assert result.command == "whoami"
    assert result.output == "shell"

    assert captured_args == (
        "-s",
        "emulator-5554",
        "shell",
        "whoami"
    )

def test_get_current_user(monkeypatch):

    def fake_run_adb(*args):
        return "shell"
    
    monkeypatch.setattr(
        "android_cookbook.shell.run_adb",
        fake_run_adb
    )

    actual = get_current_user("emulator-5554")

    assert actual == "shell"

def test_get_working_directory(monkeypatch):

    def fake_run_adb(*args):
        return "/"
    
    monkeypatch.setattr(
        "android_cookbook.shell.run_adb",
        fake_run_adb
    )

    actual = get_working_directory("emulator-5554")

    assert actual == "/"

def test_list_root_directory(monkeypatch):

    output = """
    system
    vender
    proc
    sdcard
    """

    def fake_run_adb(*args):
        return output
    
    monkeypatch.setattr(
        "android_cookbook.shll.run_adb",
        fake_run_adb
    )

    actual = list_root_directory("emulator-5554")

    assert actual == [
        "system",
        "vendor",
        "data",
        "proc",
        "sdcard",
    ]