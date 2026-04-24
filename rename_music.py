#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从文件名写入 mp3/flac 的 title / track 标签，支持可选重命名。
使用示例: python "C:\Users\35723\Documents\Heighliner\rename_music.py" "path"
选项: [--recursive] [--dry-run] [--infer-track] [--start N] [--rename]
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import mutagen

ROOT     = Path(__file__).resolve().parent
EXTS     = {".flac", ".mp3"}
RE_NAME  = re.compile(r"^\s*(?P<track>\d{1,3})\s*[.\-\)]*\s*(?P<title>.+?)\s*$", re.UNICODE)

# ---------- 数据结构 ----------
class Entry:
    __slots__ = ("path", "orig_name", "track", "title")
    def __init__(self, path: Path):
        self.path      = path
        self.orig_name = path.stem
        self.track, self.title = parse_title_from_name(self.orig_name)


# ---------- 解析 ----------
def parse_title_from_name(name: str) -> tuple[int | None, str | None]:
    """从不含扩展名的文件名解析 (track, title). 不匹配时返回 (None, name or None)."""
    m = RE_NAME.match(name)
    if m:
        return int(m.group("track")), m.group("title").strip()
    title = name.strip()
    return None, title if title else None


# ---------- 基础工具 ----------
def gather_audio_files(root: Path, recursive: bool):
    """按需递归收集支持的音频文件。"""
    if recursive:
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in EXTS:
                yield p
    else:
        for p in sorted(root.iterdir()):
            if p.is_file() and p.suffix.lower() in EXTS:
                yield p


def infer_missing_tracks(entries: list[Entry], start: int) -> None:
    """为缺少 track 的条目按排序填充连续序号，避免与已存在序号冲突。"""
    missing = [e for e in entries if e.track is None]
    if not missing:
        return
    used = {e.track for e in entries if e.track is not None}
    next_track = start
    for e in sorted(missing, key=lambda x: str(x.path).lower()):
        while next_track in used:
            next_track += 1
        e.track = next_track
        used.add(next_track)
        next_track += 1


def sanitize_title(title: str) -> str:
    """清理文件名非法字符。"""
    return re.sub(r'[\\/:"*?<>|]+', "_", title)


def write_tags(entry: Entry, dry_run: bool) -> None:
    """将 title/track 写入文件元数据。"""
    ext = entry.path.suffix.lower()
    print(f"[->] {entry.path.name}: title={entry.title!r}, track={entry.track}")
    if dry_run:
        return

    if ext == ".flac":
        audio = FLAC(str(entry.path))
        if entry.title is not None:
            audio["title"] = [entry.title]
        if entry.track is not None:
            audio["tracknumber"] = [str(entry.track)]
        audio.save()
        return

    if ext == ".mp3":
        try:
            audio = EasyID3(str(entry.path))
        except ID3NoHeaderError:
            audio = mutagen.File(str(entry.path), easy=True)
            if audio is None:
                print(f"  [!] 无法打开（mutagen 不能解析）: {entry.path}")
                return
            audio.add_tags(); audio.save()
            audio = EasyID3(str(entry.path))
        if entry.title is not None:
            audio["title"] = entry.title
        if entry.track is not None:
            audio["tracknumber"] = str(entry.track)
        audio.save()
        return

    print(f"  [!] 不支持的后缀: {ext}")


def rename_entry(entry: Entry) -> None:
    """按 'NN - Title.ext' 重命名（若 track 缺失则用 00）。"""
    track_str   = f"{entry.track:02d}" if entry.track is not None else "00"
    safe_title  = sanitize_title(entry.title or entry.orig_name)
    new_name    = f"{track_str} - {safe_title}{entry.path.suffix}"
    new_path    = entry.path.with_name(new_name)
    if new_path.exists():
        print(f"  [!] 重命名失败：目标已存在 {new_path}")
        return
    entry.path.rename(new_path)
    entry.path = new_path
    print(f"  [renamed] -> {new_name}")


# ---------- CLI ----------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="从文件名为 mp3/flac 写入 title / track 元数据")
    ap.add_argument("path", type=str, help="文件或目录路径")
    ap.add_argument("--recursive", "-r", action="store_true", help="递归处理子目录")
    ap.add_argument("--dry-run", action="store_true", help="只显示会做什么，不写入")
    ap.add_argument("--infer-track", action="store_true", help="当文件名无序号时按排序自动分配连续序号")
    ap.add_argument("--start", type=int, default=1, help="infer-track 时的起始序号（默认 1）")
    ap.add_argument("--rename", action="store_true", help="写标签后按 'NN - Title.ext' 重命名")
    return ap


def resolve_targets(target: Path, recursive: bool, parser: argparse.ArgumentParser) -> list[Path]:
    """校验目标并返回待处理文件列表。"""
    if not target.exists():
        parser.error("路径不存在")

    if target.is_file():
        if target.suffix.lower() not in EXTS:
            parser.error("只支持 .flac 和 .mp3 文件")
        return [target]

    return list(gather_audio_files(target, recursive))


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    files = resolve_targets(Path(args.path), args.recursive, parser)
    entries = [Entry(f) for f in files]

    if args.infer_track:
        infer_missing_tracks(entries, args.start)

    for e in entries:
        if e.title is None:
            print(f"[!] 跳过 {e.path.name}：无法解析标题")
            continue
        write_tags(e, dry_run=args.dry_run)
        if args.rename and not args.dry_run:
            rename_entry(e)


if __name__ == "__main__":
    main()
