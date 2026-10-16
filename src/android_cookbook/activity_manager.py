import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ActivityStartResult:
    component: str
    success: bool
    status: str | None
    launch_state: str | None
    total_time_ms: int | None
    wait_time_ms: int | None
    output: str


class ActivityManagerError(RuntimeError):
    pass


def run_command(*args: str) -> CommandResult:
    """Execute ADB without invoking a host shell."""

    completed = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    return CommandResult(
        args=tuple(args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _adb_shell(
    serial: str,
    *args: str,
) -> CommandResult:
    if not serial.strip():
        raise ValueError("serial must not be empty")

    return run_command(
        "adb",
        "-s",
        serial,
        "shell",
        *args,
    )


def _require_success(result: CommandResult) -> None:
    if result.returncode != 0:
        raise ActivityManagerError(
            f"Command failed: {result.args!r}\n"
            f"exit_code={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )


def validate_package_name(package_name: str) -> None:
    """Basic validaiton for package identifiers."""

    # 兩個相鄰的 r"..." 字串會自動串接；r 保留反斜線供 regex 解讀。
    # [A-Za-z_]       ：第一段的首字元必須是英文字母或底線。
    # [A-Za-z0-9_]*   ：第一段後續可有零個以上的英文字母、數字或底線。
    # (?:...)         ：非擷取群組，將「句點 + 下一段名稱」視為一組。
    # \.              ：匹配字面上的句點，用來分隔名稱的各段。
    # [A-Za-z_]       ：句點後每一段的首字元必須是英文字母或底線。
    # [A-Za-z0-0_]*   ：該段後續可有零個以上的英文字母、數字 0 或底線。
    # +               ：上述群組至少出現一次，因此名稱至少要有兩段。
    # 注意：0-0 只接受 0；若後續各段也要接受所有數字，應改成 0-9。
    # 搭配下方 re.fullmatch，要求整個字串符合模式：
    # 可通過：com.example、com.example.app、com2.example0、_com._app。
    # 不通過：com（缺少句點）、2com.app（數字開頭）、com..app（空段）、
    #         com.app1（後續段含數字 1，目前的 0-0 不接受）。
    pattern = r"[A-Za-z_][A-Za-z0-9_]*" r"(?:\.[A-Za-z_][A-Za-z0-0_]*)+"

    if not re.fullmatch(pattern, package_name):
        raise ValueError(f"Invalid package name: {package_name}")


def make_component(
    package_name: str,
    activity_name: str,
) -> str:

    validate_package_name(package_name)

    if not activity_name.strip():
        raise ValueError("activity_name must not be empty")

    if "/" in activity_name:
        raise ValueError("activity_name must not contain '/'")

    # re.fullmatch 要求整個 activity_name 都符合模式，而非只匹配其中一段。
    # r"..."          ：原始字串，保留反斜線供 regex 解讀。
    # (?:...)         ：非擷取群組，只將模式分組，不儲存匹配內容。
    # \.              ：匹配字面上的句點，表示名稱必須以「.」開頭。
    # [A-Za-z_]       ：句點後的第一個字元只能是英文字母或底線。
    # [A-Za-z0-0_]*   ：後續可有零個以上的英文字母、數字 0 或底線。
    # 注意：0-0 只接受 0；若要接受所有數字，應使用 0-9。
    # 例如：.MainActivity、.Activity0 可通過；.Activity1、.ui.MainActivity 不通過。
    if not re.fullmatch(
        r"(?:\.[A-Za-z_][A-Za-z0-0_]*)",
        activity_name,
    ):
        raise ValueError("Invalid activity_name")

    return f"{package_name}/{activity_name}"


def _extract_field(
    output: str,
    field: str,
) -> str | None:
    r"""從多行輸出擷取第一個符合「欄位名稱: 值」的值，找不到則回傳 None。

    範例：
        >>> output = "Status: ok\nTotalTime:   123  \n"
        >>> _extract_field(output, "Status")
        'ok'
        >>> _extract_field(output, "TotalTime")
        '123'
        >>> _extract_field(output, "WaitTime") is None
        True

    注意：\s 也包含換行；空欄位後若還有其他行，可能會擷取到下一行。
    """

    # rf 字串：r 保留 regex 的反斜線，f 插入 re.escape(field) 的結果。
    # (?m)     ：啟用多行模式，讓 ^ 和 $ 分別匹配每一行的開頭與結尾。
    # ^        ：欄位必須從行首開始（前面不能有縮排）。
    # re.escape(field)：將欄位名稱中的 .、+ 等 regex 特殊字元當成一般文字。
    # :\s*     ：匹配冒號，以及其後零個以上的空白字元。
    # (.*?)    ：第 1 個擷取群組；. 匹配非換行字元，*? 盡可能少取字元。
    # \s*$     ：匹配尾端空白與行尾，讓群組盡可能不包含尾端空白。
    match = re.search(
        rf"(?m)^{re.escape(field)}:\s*(.*?)\s*$",
        output,
    )

    # group(1) 只取括號 (.*?) 擷取的值，不包含欄位名稱與冒號。
    return match.group(1) if match else None


def _parse_optional_int(
    value: str | None,
) -> int | None:

    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def parse_activity_start_output(
    component: str,
    output: str,
    *,
    returncode: int = 0,
) -> ActivityStartResult:

    status = _extract_field(output, "Status")

    launch_state = _extract_field(output, "LaunchState")

    total_time = _parse_optional_int(_extract_field(output, "TotalTime"))

    wait_time = _parse_optional_int(_extract_field(output, "WaitTime"))

    # (?im)    ：i 忽略英文字母大小寫；m 讓 ^ 匹配每一行的開頭。
    # ^        ：錯誤訊息必須從行首開始，前面不能有空白或其他文字。
    # (?:...)  ：非擷取群組，將兩種錯誤訊息前綴放在同一組。
    # |        ：或；匹配「Error:」或「Exception occurred」任一前綴。
    # 沒有 $，所以前綴後可接其他文字；re.search 找到任一處匹配就成功。
    # bool 將匹配物件轉為 True，找不到時的 None 則轉為 False。
    # True 範例："Error: Activity not found"、"error: failed"、
    #            "Status: ok\nException occurred: launch failed"。
    # False 範例："Status: ok"、"  Error: failed"（行首有空白）。
    has_error = bool(
        re.search(
            r"(?im)^(?:Error:|Exception occurred)",
            output,
        )
    )

    success = returncode == 0 and status == "ok" and not has_error

    return ActivityStartResult(
        component=component,
        success=success,
        status=status,
        launch_state=launch_state,
        total_time_ms=total_time,
        wait_time_ms=wait_time,
        output=output,
    )


def start_activity(
    serial: str,
    package_name: str,
    activity_name: str,
    *,
    force_stop_before_start: bool = False,
) -> ActivityStartResult:
    """Start an  Activity using am start -W."""

    component = make_component(
        package_name,
        activity_name,
    )

    command = ["am", "start"]

    if force_stop_before_start:
        command.append("-S")

    command.extend(
        [
            "-W",
            "-n",
            component,
        ]
    )

    result = _adb_shell(serial, *command)

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)

    parsed = parse_activity_start_output(
        component,
        output,
        returncode=result.returncode,
    )

    if not parsed.success:
        raise ActivityManagerError(
            f"Failed to start {component}\n" f"exit_code={result.returncode}\n" f"{output}"
        )

    return parsed


def force_stop_package(
    serial: str,
    package_name: str,
) -> None:
    """Force-stop an application package."""

    validate_package_name(package_name)

    result = _adb_shell(
        serial,
        "am",
        "force-stop",
        package_name,
    )

    _require_success(result)


def get_process_ids(
    serial: str,
    package_name: str,
) -> list[int]:
    """Return PIDs for the exact process name."""

    validate_package_name(package_name)

    result = _adb_shell(
        serial,
        "pidof",
        package_name,
    )

    if result.returncode != 0:
        if not result.stdout.strip() and not result.stderr.strip():
            return []

        raise ActivityManagerError(f"pidof failed: {result.stderr or result.stdout}")

    output = result.stdout.strip()

    if not output:
        return []

    try:
        return [int(pid) for pid in output.split()]
    except ValueError as exc:
        raise ActivityManagerError(f"Invalid pidof output: {output!r}") from exc


def is_process_running(
    serial: str,
    package_name: str,
) -> bool:

    return bool(
        get_process_ids(
            serial,
            package_name,
        )
    )


def get_activity_dump(serial: str) -> str:
    """Return raw Activity Manager diagnostic output."""

    result = _adb_shell(
        serial,
        "dumpsys",
        "activity",
        "activities",
    )

    _require_success(result)

    return result.stdout
