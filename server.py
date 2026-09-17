"""
Readmoo 劃線筆記 MCP Server

用法：
    1. 把從 Readmoo「匯出劃線」下載的 CSV 檔全部放進同一個資料夾。
       （檔名就是書名，例如「你的書名.csv」）
    2. 設定環境變數 READMOO_DATA_DIR 指向這個資料夾，
       或執行時用 --data-dir 指定，沒指定的話預設是 ~/readmoo-notes
    3. 在 Claude Desktop / Claude Code 設定這個 server 即可使用。

提供的 tools：
    - list_books            列出所有書籍與劃線數量
    - get_highlights        取得某本書的劃線（可指定章節）
    - search_highlights     跨書或限定單本書搜尋關鍵字
    - get_notes             只取出「有寫註記」的劃線（排除純劃線）
"""

import argparse
import os
import sys
from typing import Optional

try:
    # mcp SDK 1.x
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    # mcp SDK 2.x：FastMCP 改名為 MCPServer，但介面相容
    from mcp.server.mcpserver import MCPServer as FastMCP

from readmoo_data import ReadmooLibrary

DEFAULT_DATA_DIR = "~/readmoo-notes"

# 資料夾路徑優先順序：command line > 環境變數 > 預設值
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--data-dir", dest="data_dir", default=None)
_args, _ = _parser.parse_known_args()

DATA_DIR = (
    _args.data_dir
    or os.environ.get("READMOO_DATA_DIR")
    or DEFAULT_DATA_DIR
)

library = ReadmooLibrary(DATA_DIR)

mcp = FastMCP("readmoo-notes")


@mcp.tool()
def list_books() -> list[dict]:
    """列出目前資料夾內所有 Readmoo 書籍，附上劃線數量、章節數與有寫註記的筆記數。"""
    books = library.list_books()
    if not books:
        return [
            {
                "訊息": f"在「{library.data_dir}」找不到任何 CSV 檔案，"
                "請確認已把 Readmoo 匯出的劃線 CSV 放進這個資料夾。"
            }
        ]
    return books


@mcp.tool()
def get_highlights(book: str, chapter: Optional[str] = None) -> dict:
    """
    取得某本書的所有劃線與註記，依章節、時間排序，已自動去除重複匯出的劃線。

    Args:
        book: 書名（可只打部分關鍵字，會比對到完整書名）。
        chapter: 選填，只看特定章節（章節編號用字串比對，例如 "16"）。
    """
    error, highlights = library.get_highlights(book, chapter)
    if error:
        return {"error": error}
    return {"book": book, "chapter_filter": chapter, "count": len(highlights), "highlights": highlights}


@mcp.tool()
def search_highlights(keyword: str, book: Optional[str] = None) -> dict:
    """
    在劃線內容或註記中搜尋關鍵字，預設搜尋所有書籍，也可指定只搜尋一本書。

    Args:
        keyword: 要搜尋的關鍵字（子字串比對，不分書名或內容）。
        book: 選填，只在這本書內搜尋。
    """
    error, results = library.search(keyword, book)
    if error:
        return {"error": error}
    return {"keyword": keyword, "book_filter": book, "count": len(results), "highlights": results}


@mcp.tool()
def get_notes(book: Optional[str] = None) -> dict:
    """
    只取出「有寫下自己註記」的劃線（排除單純畫線、沒有加註的部分），
    適合用來整理自己真正寫過想法的段落。

    Args:
        book: 選填，只看某一本書的註記。
    """
    error, results = library.get_notes_only(book)
    if error:
        return {"error": error}
    return {"book_filter": book, "count": len(results), "notes": results}


if __name__ == "__main__":
    mcp.run()
