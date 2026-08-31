from dataclass import dataclass
from android_cookbook.adb import run_adb

@dataclass(frozen=True)
class ProcessInfo:
    user: str
    pid: int
    name: str

@dataclass(frozen=True)
class ShellResult:
    command: str
    output: str

def run_shell(serial: str, *command: str) -> ShellResult:
    output = run_adb(
        "-s",
        serial,
        "shell",
        *command,
    )

    return ShellResult(
        command=" ".join(command),
        output=output,
    )

def get_working_directory(serial: str) -> str:
    result = run_shell(serial, "pwd")
    return result.output

def get_current_user(serial: str) -> str:
    result = run_shell(serial, "whoami")
    return result.output

def get_kernel_info(serial: str) -> str:
    result = run_shell(serial, "uname", "-a")
    return result.output

def list_root_directory(serial: str) -> list[str]:
    result = run_shell(serial, "ls", "/")
    return [
        line.strip()
        for line in result.output.splitlines()
        if line.strip()
    ]