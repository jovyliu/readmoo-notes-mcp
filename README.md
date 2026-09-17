# readmoo-notes-mcp

把你在 [Readmoo 讀墨](https://readmoo.com) 電子書上的劃線與註記，變成 Claude（或其他支援 MCP 的工具）可以直接查詢、整理的資料來源。

這是一個非官方的個人專案，跟 Readmoo 官方沒有任何關係，也不使用任何未公開的 API——單純讀取 Readmoo 網頁版「匯出劃線」功能所產生的 CSV 檔案。

## 這個專案在做什麼

Readmoo 網頁版的「劃線與筆記」頁面，本來就有「匯出劃線 → 下載 CSV 檔」的官方功能。這個 MCP server 做的事情很單純：

1. 你手動把匯出的 CSV 放進一個資料夾
2. MCP server 讀取這個資料夾，解析、去重
3. 透過 MCP protocol，讓 Claude 可以查詢、搜尋、整理這些劃線與筆記

沒有登入自動化、沒有反向工程 API、沒有繞過任何匯出限制——你能透過這個工具拿到的資料，範圍跟你自己手動匯出時完全一樣。

> ⚠️ **關於匯出字數限制**：出版社通常會限制匯出字數上限為全書 15%、單則劃線不超過 150 字，這是版權保護機制，這個專案沒有、也不會嘗試繞過這個限制。

## 提供的 Tools

| Tool | 說明 |
|---|---|
| `list_books` | 列出資料夾內所有書籍，附劃線數、章節數、有寫註記的筆記數 |
| `get_highlights(book, chapter?)` | 取得某本書的劃線（書名支援部分比對，可選填章節篩選） |
| `search_highlights(keyword, book?)` | 跨書或限定單本書，在劃線內容 / 註記裡搜尋關鍵字 |
| `get_notes(book?)` | 只取出「有自己寫註記」的劃線，排除單純畫線沒加註的部分 |

會自動去除 Readmoo 匯出時常見的重複列（同章節 + 同劃線內容視為重複）。

## 安裝

需要 Python 3.10 以上。

```bash
git clone https://github.com/<你的帳號>/readmoo-notes-mcp.git
cd readmoo-notes-mcp
pip install -r requirements.txt
```

## 取得你的劃線資料

1. 打開 Readmoo 網頁版，進到某本書的「劃線與筆記」頁面
2. 點「匯出劃線」→「下載 CSV 檔」
3. 把下載的 CSV 放進一個資料夾（檔名就是書名，不用改名），例如：

```bash
mkdir -p ~/readmoo-notes
cp ~/Downloads/你的書名.csv ~/readmoo-notes/
```

CSV 欄位長這樣（以下是虛構範例，不是真實資料）：

```csv
章節,劃線時間,劃線內容,註記
1,2026-01-01,這是一段範例劃線內容，用來示範格式長什麼樣子,
1,2026-01-02,另一段範例劃線，這則沒有寫註記,
2,2026-01-03,這則範例劃線有搭配自己寫的想法,這是我自己寫的註記範例
```

## 設定 Claude Desktop

編輯設定檔：
- Mac：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

加入：

```json
{
  "mcpServers": {
    "readmoo-notes": {
      "command": "python3",
      "args": ["/絕對路徑/readmoo-notes-mcp/server.py"],
      "env": {
        "READMOO_DATA_DIR": "/絕對路徑/你放CSV的資料夾"
      }
    }
  }
}
```

存檔後重新啟動 Claude Desktop。

## 設定 Claude Code

```bash
claude mcp add readmoo-notes \
  --env READMOO_DATA_DIR=/絕對路徑/你放CSV的資料夾 \
  -- python3 /絕對路徑/readmoo-notes-mcp/server.py
```

## 使用範例

設定好之後，直接在 Claude 裡問：

- 「幫我列出目前有哪些書的劃線筆記」
- 「整理《書名》裡跟某個主題有關的劃線」
- 「我在哪些書裡寫過關於『成長』的註記？」
- 「把第 N 章的劃線整理成重點摘要」

## 限制與注意事項

- 這個工具**不會**幫你抓超過 Readmoo 匯出限制的內容，能拿到的資料範圍跟手動匯出一樣
- 沒有官方 API，純粹讀取本地 CSV 檔案，不會連線到 Readmoo 或儲存你的帳號資訊
- 多台裝置之間不會自動同步，CSV 資料要自己搬過去（或放在你自己的雲端同步資料夾裡）

## License

MIT
