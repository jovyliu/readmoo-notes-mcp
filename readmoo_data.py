"""
Readmoo 劃線筆記資料層
負責讀取一個資料夾內所有 Readmoo 匯出的 CSV 檔案，解析、去重，
並提供給 MCP tools 查詢用的函式。

CSV 格式（Readmoo「匯出劃線」功能產生）：
    章節,劃線時間,劃線內容,註記
檔名（去掉副檔名）視為書名。
"""

import csv
import io
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Highlight:
    book: str
    chapter: str
    date: str
    text: str
    note: str

    def to_dict(self) -> dict:
        return {
            "book": self.book,
            "chapter": self.chapter,
            "date": self.date,
            "text": self.text,
            "note": self.note,
        }


def _read_csv_robust(path: Path) -> list[dict]:
    """讀取 Readmoo 匯出的 CSV，處理 BOM 與常見編碼問題。"""
    raw = path.read_bytes()
    # Readmoo 匯出的檔案帶 UTF-8 BOM
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        # 保護：欄位名稱可能因為奇怪的空白而對不上，做一次 strip
        clean_row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        rows.append(clean_row)
    return rows


def load_book(path: Path) -> list[Highlight]:
    """讀取單一書籍的 CSV 檔案，回傳去重後的劃線清單。"""
    book_name = path.stem
    rows = _read_csv_robust(path)

    seen = set()
    highlights: list[Highlight] = []
    for row in rows:
        chapter = row.get("章節", "")
        date = row.get("劃線時間", "")
        text = row.get("劃線內容", "")
        note = row.get("註記", "")

        if not text:
            continue

        # 去重 key：同章節 + 同劃線內容 視為重複匯出
        dedupe_key = (chapter, text)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        highlights.append(
            Highlight(book=book_name, chapter=chapter, date=date, text=text, note=note)
        )

    # 依章節（數字優先）再依時間排序，方便閱讀
    def sort_key(h: Highlight):
        try:
            chapter_num = int(h.chapter)
        except (ValueError, TypeError):
            chapter_num = float("inf")
        return (chapter_num, h.date)

    highlights.sort(key=sort_key)
    return highlights


class ReadmooLibrary:
    """管理資料夾內所有書籍的劃線資料，支援按需重新載入。"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir).expanduser()

    def _csv_files(self) -> list[Path]:
        if not self.data_dir.exists():
            return []
        return sorted(self.data_dir.glob("*.csv"))

    def list_books(self) -> list[dict]:
        """列出資料夾內所有書籍，附上劃線數量與章節數。"""
        result = []
        for path in self._csv_files():
            highlights = load_book(path)
            chapters = {h.chapter for h in highlights}
            notes_count = sum(1 for h in highlights if h.note)
            result.append(
                {
                    "book": path.stem,
                    "highlight_count": len(highlights),
                    "chapter_count": len(chapters),
                    "note_count": notes_count,
                    "file": path.name,
                }
            )
        return result

    def _find_book_path(self, book: str) -> Optional[Path]:
        """依書名（完整或部分符合）找到對應的 CSV 檔案。"""
        candidates = self._csv_files()
        # 完全符合優先
        for path in candidates:
            if path.stem == book:
                return path
        # 部分符合（不分大小寫）
        lowered = book.lower()
        matches = [p for p in candidates if lowered in p.stem.lower()]
        if len(matches) == 1:
            return matches[0]
        return None

    def get_highlights(
        self, book: str, chapter: Optional[str] = None
    ) -> tuple[Optional[str], list[dict]]:
        """取得某本書的劃線。回傳 (錯誤訊息或 None, 劃線清單)。"""
        path = self._find_book_path(book)
        if path is None:
            available = [p.stem for p in self._csv_files()]
            return (
                f"找不到符合「{book}」的書。目前資料夾裡的書有：{available}",
                [],
            )
        highlights = load_book(path)
        if chapter is not None:
            highlights = [h for h in highlights if h.chapter == str(chapter)]
        return None, [h.to_dict() for h in highlights]

    def search(
        self, keyword: str, book: Optional[str] = None
    ) -> tuple[Optional[str], list[dict]]:
        """跨書（或限定單本書）搜尋劃線內容或註記中的關鍵字。"""
        if book:
            path = self._find_book_path(book)
            if path is None:
                available = [p.stem for p in self._csv_files()]
                return (
                    f"找不到符合「{book}」的書。目前資料夾裡的書有：{available}",
                    [],
                )
            paths = [path]
        else:
            paths = self._csv_files()

        results = []
        for p in paths:
            for h in load_book(p):
                if keyword in h.text or keyword in h.note:
                    results.append(h.to_dict())
        return None, results

    def get_notes_only(self, book: Optional[str] = None) -> tuple[Optional[str], list[dict]]:
        """只取出「有寫註記」的劃線（排除單純劃線、無筆記的部分）。"""
        if book:
            path = self._find_book_path(book)
            if path is None:
                available = [p.stem for p in self._csv_files()]
                return (
                    f"找不到符合「{book}」的書。目前資料夾裡的書有：{available}",
                    [],
                )
            paths = [path]
        else:
            paths = self._csv_files()

        results = []
        for p in paths:
            for h in load_book(p):
                if h.note:
                    results.append(h.to_dict())
        return None, results
