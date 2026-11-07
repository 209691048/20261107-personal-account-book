"""JSON 文件读写入口；记录字段的业务校验由 models.py 负责。"""

import json
import os
from pathlib import Path
import tempfile


_DATA_FILE = Path(__file__).resolve().parent / "data" / "records.json"


def _validate_records(records: object) -> None:
    """存储格式必须是数组，数组中的每条记录必须是字典。"""
    if not isinstance(records, list):
        raise ValueError("记录数据必须是 JSON 数组（list）。")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"第 {index + 1} 条记录必须是 JSON 对象（dict）。")


def _reject_non_finite(value: str) -> None:
    raise ValueError(f"JSON 不支持非有限数字：{value}。")


def load_records() -> list[dict]:
    """读取全部记录；文件不存在时返回空列表，损坏时明确报错。"""
    try:
        with _DATA_FILE.open("r", encoding="utf-8") as source:
            records = json.load(source, parse_constant=_reject_non_finite)
    except FileNotFoundError:
        return []
    except (ValueError, OSError) as exc:
        raise ValueError(
            f"无法读取记录文件 {_DATA_FILE}：{exc}。"
            "请检查原文件；不会将读取失败当成空记录。"
        ) from exc

    _validate_records(records)
    return records


def save_records(records: list[dict]) -> None:
    """完整保存记录；先写同目录临时文件，再原子替换原文件。"""
    _validate_records(records)
    try:
        content = json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"记录无法转换为 JSON，原文件未修改：{exc}") from exc

    # 拒绝直接覆盖已有的损坏文件，避免把读取故障变成永久数据丢失。
    load_records()

    temporary_path = None
    try:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=_DATA_FILE.parent,
            prefix=f".{_DATA_FILE.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        # Windows 下必须先关闭临时文件，才能替换目标文件。
        os.replace(temporary_path, _DATA_FILE)
    except (OSError, UnicodeError) as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise ValueError(
                    f"保存记录失败：{exc}；临时文件 {temporary_path} "
                    f"清理失败：{cleanup_error}。"
                ) from exc
        raise ValueError(f"无法保存记录文件 {_DATA_FILE}：{exc}") from exc
