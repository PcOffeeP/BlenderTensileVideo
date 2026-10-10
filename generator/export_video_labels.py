#!/usr/bin/env python3
"""Export indexed whole-video labels without changing source metadata.

Requires Python 3.10+, openpyxl and ffprobe. Example from any directory::

    python generator/export_video_labels.py --index outputs/index.json \
        --output-dir /path/to/export

The five label columns match the real experiment workbook. Exporting includes
both accepted videos and checked candidates, and does not authorize training.
Version 1 preserves unknown directly usable visual event times as blanks;
authored/mesh events never become visual-time annotations automatically.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from fractions import Fraction
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

VERSION = "unified-video-label-export/1.0"
TAG_COLUMNS = ("id", "断裂时间点", "断裂模式", "材料类型", "清晰度")
SIX_GROUPS = ("材料类别", "断裂结果", "单一主要破坏类别", "断裂位置", "夹持异常", "拍摄异常")
V4_FIELDS = ("clip_state", "fracture_mechanism", "fracture_site", "special_case")
STATUSES = ("user_accepted_video", "checked_pending_user_acceptance")
DETAIL_COLUMNS = (
    "id", "标题", "源视频ID", "接受状态", "索引状态", "user_accepted", "training_released",
    "video_path", "metadata_path", *SIX_GROUPS, "六组核验依据", "核验标签读取位置",
    *V4_FIELDS, "V4已有字段依据及范围", "视频SHA256", "metadata_SHA256", "SHA核对",
    "视频时长秒", "视频帧率", "视频总帧数", "编码宽", "编码高", "媒体核对",
    "首次视觉分离时间秒", "首次视觉分离帧", "时间留空原因",
    "已记录模拟测量事件", "已记录作者工程事件与时序", "事件范围说明", "源时间记录",
    "原有未知项", "字段映射", "验收及审查记录",
)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def review_summary(metadata):
    """Keep review references and conclusions; large reports stay in metadata."""
    records = {}
    for key in ("acceptance_scope", "independent_review_record", "user_acceptance_record",
                "user_label_confirmation", "mode_evidence_adjudication"):
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, dict):
            value = {k: v for k, v in value.items() if not isinstance(v, (dict, list))}
        records[key] = value
    return records


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def label_values(labels):
    if not isinstance(labels, dict):
        return None
    labels = labels.get("labels", labels)
    if not all(key in labels for key in SIX_GROUPS):
        return None
    return {key: (labels[key].get("value") if isinstance(labels[key], dict) else labels[key])
            for key in SIX_GROUPS}


def checked_labels(item, metadata):
    indexed = label_values(item.get("checked_labels"))
    if indexed is None:
        raise ValueError(f"{item['id']}: index lacks complete checked labels")
    found = []
    for key in ("checked_labels", "checked_labels_six_groups", "verified_labels"):
        labels = label_values(metadata.get(key))
        if labels is not None:
            if labels != indexed:
                raise ValueError(f"{item['id']}: {key} differs from indexed checked labels")
            found.append(key)
    if not found:
        raise ValueError(f"{item['id']}: metadata lacks matching six-group labels")
    return indexed, found


def media_info(video_path, ffprobe):
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate,nb_frames,duration:format=duration",
         "-of", "json", str(video_path)], check=True, capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return {
        "duration_s": float(stream.get("duration", data["format"]["duration"])),
        "fps": float(Fraction(stream["avg_frame_rate"])),
        "frames": int(stream["nb_frames"]),
        "width": int(stream["width"]), "height": int(stream["height"]),
    }


def event_records(metadata):
    """Select engineering records, preserving their source paths and wording."""
    measured = {}
    for key in ("engineering_check_gate", "technical_checks", "technical_verification"):
        block = metadata.get(key, {})
        if not isinstance(block, dict):
            continue
        for name in ("measured_events", "last_connection_to_complete_fracture"):
            if name in block:
                measured[f"{key}.{name}"] = block[name]
        # Older baselines keep measured topology events in a summary object.
        for name in ("mesh", "mesh_summary", "actual_evaluated_mesh",
                     "actual_evaluated_mesh_summary", "all_600_frame_summary"):
            summary = block.get(name)
            if isinstance(summary, dict):
                selected = {k: v for k, v in summary.items()
                            if any(token in k for token in ("first_", "event", "rupture", "disconnect", "path_absent"))}
                if selected:
                    measured[f"{key}.{name}"] = selected
    timeline = metadata.get("time_mapping") or metadata.get("generated_time_map") or {}
    if isinstance(timeline, dict) and "measured_events" in timeline:
        measured["time_mapping.measured_events"] = timeline["measured_events"]
    authored = {"timeline": timeline}
    # Current configuration, never inherited baseline_context configuration.
    for key in ("configuration", "complete_config", "full_generation_configuration", "full_generation_config"):
        config = metadata.get(key)
        if isinstance(config, dict):
            selected = {k: v for k, v in config.items()
                        if any(token in k for token in ("event", "rupture", "crack_start", "last_connected", "first_separated", "stop_from"))}
            if selected:
                authored[key] = selected
    return measured, authored


def export_rows(index_path, ffprobe):
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes)
    rows, details, checks = [], [], []
    seen = set()
    for item in index["items"]:
        video_id = item["id"]
        if video_id in seen:
            raise ValueError(f"Duplicate indexed ID: {video_id}")
        seen.add(video_id)
        status = item["status"]
        if status not in STATUSES:
            raise ValueError(f"{video_id}: unsupported export status {status!r}")
        accepted = status == "user_accepted_video"
        if item.get("user_accepted") is not accepted:
            raise ValueError(f"{video_id}: acceptance flag/status mismatch")
        video_path = (index_path.parent / item["video_path"]).resolve()
        metadata_path = (index_path.parent / item["metadata_path"]).resolve()
        video_hash, metadata_hash = sha256(video_path), sha256(metadata_path)
        if video_hash != item["sha256"] or metadata_hash != item["metadata_sha256"]:
            raise ValueError(f"{video_id}: indexed SHA256 mismatch")
        metadata = json.loads(metadata_path.read_bytes())
        if metadata.get("user_accepted") is not accepted:
            raise ValueError(f"{video_id}: metadata acceptance flag mismatch")
        if metadata.get("training_released") != item.get("training_released"):
            raise ValueError(f"{video_id}: training release flag mismatch")
        labels, label_paths = checked_labels(item, metadata)
        media = media_info(video_path, ffprobe)
        for field in ("duration_s", "fps", "frames"):
            if not math.isclose(media[field], float(item[field]), abs_tol=1e-6):
                raise ValueError(f"{video_id}: actual {field} differs from index")
        # Pixel height follows the real workbook's P suffix, without claiming
        # subjective sharpness, or borrowing the source experiment resolution.
        row = {"id": video_id, "断裂时间点": None,
               "断裂模式": labels["单一主要破坏类别"],
               "材料类型": labels["材料类别"], "清晰度": f"{media['height']}P"}
        preview = metadata.get("downstream_label_preview") or {}
        v4 = preview.get("labels", {})
        if v4 and set(v4) != set(V4_FIELDS):
            raise ValueError(f"{video_id}: incomplete existing V4 payload")
        indexed_v4 = item.get("v4_1_whole_video_labels")
        if indexed_v4 is not None and indexed_v4 != v4:
            raise ValueError(f"{video_id}: existing V4 labels differ from index")
        bound_hash = preview.get("video_sha256")
        if bound_hash is not None and bound_hash != video_hash:
            raise ValueError(f"{video_id}: existing V4 video binding mismatch")
        measured, authored = event_records(metadata)
        source = metadata.get("source", {})
        source_times = {k: v for k, v in source.items()
                        if any(s in k for s in ("event", "annotation_time", "observed_separation"))}
        reason = "真实表未细分事件口径；当前模拟JSON未核验可供断裂时间点列直接采用的精确视觉事件时刻，留空。作者事件、拓扑失贯通、首次正间隙及源实验标签时间不代填。"
        detail = {
            "id": video_id, "标题": item.get("title"), "源视频ID": item.get("source_id") or source.get("id"),
            "接受状态": "用户已接受单条视频" if accepted else "已核验，待用户逐条接受",
            "索引状态": status, "user_accepted": accepted, "training_released": item.get("training_released"),
            "video_path": str(video_path), "metadata_path": str(metadata_path), **labels,
            "六组核验依据": compact({key: metadata[key] for key in label_paths}),
            "核验标签读取位置": ", ".join(label_paths) + "；已逐字段对照 index.items.checked_labels",
            **{key: v4.get(key) for key in V4_FIELDS},
            "V4已有字段依据及范围": compact({k: v for k, v in preview.items() if k != "labels"}) if v4 else "未记录已有四字段payload；不从六组标签自动补写",
            "视频SHA256": video_hash, "metadata_SHA256": metadata_hash, "SHA核对": "实际文件与索引一致",
            "视频时长秒": media["duration_s"], "视频帧率": media["fps"], "视频总帧数": media["frames"],
            "编码宽": media["width"], "编码高": media["height"], "媒体核对": "实际ffprobe与索引时长/帧率/帧数一致；本次未重做全解码/600帧网格检查",
            "首次视觉分离时间秒": None, "首次视觉分离帧": None, "时间留空原因": reason,
            "已记录模拟测量事件": compact(measured), "已记录作者工程事件与时序": compact(authored),
            "事件范围说明": "仅转录原有工程/测量记录，未重新求值；native path、接触焊接路径、正间隙和视觉分离是不同事件。旧timeline可能继承模板，具体测量记录及当前配置分别保留，不合并成视觉时刻。",
            "源时间记录": compact(source_times), "原有未知项": compact(metadata.get("unknowns", [])),
            "字段映射": "id=索引模拟视频ID；模式=当前核验单一主要破坏类别；材料=当前核验材料类别；清晰度=实际编码帧高P；断裂时间点=未知留空。",
            "验收及审查记录": compact(review_summary(metadata)),
        }
        rows.append(row)
        details.append(detail)
        checks.append({"id": video_id, "status": status, "video_sha256": video_hash,
                       "metadata_sha256": metadata_hash, "media": media,
                       "labels": labels, "label_paths": label_paths, "existing_v4": bool(v4),
                       "first_visual_event": None, "time_unknown_reason": reason})
    if index_path.read_bytes() != index_bytes:
        raise ValueError("Index changed during export")
    for item, check in zip(index["items"], checks):
        for key, hash_key in (("video_path", "video_sha256"), ("metadata_path", "metadata_sha256")):
            if sha256((index_path.parent / item[key]).resolve()) != check[hash_key]:
                raise ValueError(f"{item['id']}: file changed during export")
    return rows, details, checks, hashlib.sha256(index_bytes).hexdigest()


def write_sheet(workbook, name, columns, rows):
    sheet = workbook.create_sheet(name)
    sheet.append(columns)
    for row in rows:
        for key in columns:
            value = row.get(key)
            if isinstance(value, str) and len(value) > 32767:
                raise ValueError(f"{name}/{row.get('id')}/{key}: evidence exceeds Excel cell limit")
        sheet.append([row.get(key) for key in columns])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="304B63")
    for column, key in enumerate(columns, 1):
        sheet.column_dimensions[get_column_letter(column)].width = 50 if key in ("id", "video_path", "metadata_path") else 26
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            # Treat text as text, including leading formula characters.
            if isinstance(cell.value, str):
                cell.data_type = "s"
        for key in ("video_path", "metadata_path"):
            if key in columns:
                cell = row[columns.index(key)]
                cell.hyperlink = Path(cell.value).as_uri()
                cell.style = "Hyperlink"
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path(__file__).resolve().parents[1] / "outputs/index.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    index_path = args.index.resolve()
    rows, details, checks, index_hash = export_rows(index_path, args.ffprobe)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    csv_path, xlsx_path = output / "all_videos_tag.csv", output / "all_videos_tag.xlsx"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TAG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    workbook = Workbook()
    workbook.remove(workbook.active)
    write_sheet(workbook, "Sheet1", TAG_COLUMNS, rows)
    write_sheet(workbook, "核验说明", DETAIL_COLUMNS, details)
    counts = Counter(check["status"] for check in checks)
    notes = [
        {"字段或范围": "实现版本", "说明": VERSION},
        {"字段或范围": "主表用途", "说明": "与真实实验现有XLSX相同5列；每条完整模拟视频1行。CSV与Sheet1相同。核验说明按id关联。"},
        {"字段或范围": "数量与状态", "说明": compact(dict(counts)) + f"；共{len(rows)}条，待接受视频不会自动变成已接受。"},
        {"字段或范围": "id", "说明": "模拟视频索引ID，保留原ID和文件名；源实验video_XXXX仅在核验说明源视频ID列。"},
        {"字段或范围": "断裂时间点", "说明": "真实表未细分事件口径；当前模拟JSON未核验可供该列直接采用的精确视觉事件时刻，留空。已有工程/测量时刻单独转录；不把首次正间隙、拓扑失贯通或来源实验标签时间自动映射到该列。"},
        {"字段或范围": "断裂模式", "说明": "当前核验单一主要破坏类别原词；包括半脆半韧断裂、无法确认。旧0040来源爆炸性原标签不覆盖模拟核验无法确认。齐根是位置，不改写为模式。"},
        {"字段或范围": "材料类型", "说明": "当前核验材料类别；保留用户已确认材料，不按外观或历史源标签推翻。"},
        {"字段或范围": "清晰度", "说明": "实际ffprobe编码帧高加P（720P/540P等），不是主观质量，也不是原实验源分辨率。核验说明同时给出完整宽高。"},
        {"字段或范围": "六组核验标签", "说明": "与index的当前checked_labels一致；适配metadata checked_labels、checked_labels_six_groups、verified_labels。原记录包含历史限定状态，当前接受状态以索引和metadata顶层旗标核对。"},
        {"字段或范围": "已有V4四字段", "说明": "仅复制已有downstream_label_preview并核对索引有记录的payload；缺失不推导。special_case空白在已有payload中可表示null，不能以空白判定缺证据，详见相邻依据及范围。"},
        {"字段或范围": "训练与切片", "说明": "本次集中导出不是训练发布；待接受状态不变。整段视频标签不复制给未来切片，必须按实际切片输入重新标注。"},
        {"字段或范围": "下游兼容", "说明": "未生成13列source_bootstrap输入，未改写ID/文件名/状态，未知时间为空；本表不宣称可直接消费或发布。"},
        {"字段或范围": "实际验证", "说明": "65条实际video/metadata SHA、当前标签、接受旗标、ffprobe时长帧率帧数逐项核对；CSV与XLSX保存后重读比较。未重渲染、未重做600帧网格检查或首次视觉时刻判定。"},
        {"字段或范围": "索引SHA256", "说明": index_hash},
    ]
    write_sheet(workbook, "字段说明", ("字段或范围", "说明"), notes)
    workbook.save(xlsx_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    if csv_rows != [{key: "" if row[key] is None else str(row[key]) for key in TAG_COLUMNS} for row in rows]:
        raise ValueError("CSV roundtrip mismatch")
    reread = load_workbook(xlsx_path, read_only=False, data_only=False)
    if list(reread["Sheet1"].values) != [TAG_COLUMNS] + [tuple(row[key] for key in TAG_COLUMNS) for row in rows]:
        raise ValueError("XLSX label roundtrip mismatch")
    if list(reread["核验说明"].values) != [DETAIL_COLUMNS] + [tuple(row.get(key) for key in DETAIL_COLUMNS) for row in details]:
        raise ValueError("XLSX evidence roundtrip mismatch")
    for row in reread["核验说明"].iter_rows(min_row=2):
        cell = row[DETAIL_COLUMNS.index("video_path")]
        if cell.hyperlink.target != Path(cell.value).as_uri():
            raise ValueError("XLSX video hyperlink mismatch")
    reread.close()
    report = {"schema": VERSION, "index_path": str(index_path), "index_sha256": index_hash,
              "count": len(rows), "status_counts": dict(counts), "columns": TAG_COLUMNS,
              "first_visual_time_unknown_count": len(rows), "existing_v4_count": sum(c["existing_v4"] for c in checks),
              "csv_xlsx_roundtrip": "passed", "file_and_media_checks": checks,
              "outputs": {str(path): sha256(path) for path in (csv_path, xlsx_path)}}
    (output / "export_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("count", "status_counts", "first_visual_time_unknown_count", "existing_v4_count", "csv_xlsx_roundtrip", "outputs")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
