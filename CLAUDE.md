# Voice-to-txt：語音轉逐字稿流程

使用者會給「音檔雲端連結」和「逐字稿要存的雲端位置」。依序執行：

1. **取得音檔**
   - Google Drive 連結：從連結取出 fileId，用 Google Drive 連接器 `download_file_content` 下載，
     把 base64 解碼存成 `downloads/<檔名>`（不要直接連 drive.google.com，環境可能擋）。
   - 其他公開直連網址（Dropbox、一般 https）：直接把網址交給 `transcribe.py`。
2. **轉文字**（免費本地模型 faster-whisper，預設 `large-v3-turbo`）
   ```
   pip install -r requirements.txt
   python3 transcribe.py downloads/<檔名> --language zh --prompt "<已知人名、專有名詞>"
   ```
   產出 `output/<名>.raw.txt`、`.srt`、`.json`。中文預設轉成台灣繁體。
   若 huggingface.co 被網路政策擋住，模型無法下載 —— 告訴使用者把 `huggingface.co`
   加到環境的 Allowed domains（或用 `--model <本機模型資料夾>`）。
3. **根據上下文修正逐字稿**（由 Claude 完成，不是模型）
   - 讀 `output/<名>.json` 全文，先理解主題、人物、專有名詞。
   - 修正同音錯字、斷詞、人名／術語前後不一致、標點；補上適當分段。
   - 不改變原意、不刪減內容、不腦補；聽不清楚的地方標 `[聽不清]`。
   - 有多位講者且能從上下文判斷時，標示「講者A／講者B」。
   - 存成 `output/<名>.corrected.txt`（可保留 `[hh:mm:ss]` 段落時間戳）。
4. **上傳到指定位置**
   - Google Drive 資料夾連結：取出 folderId，用 `create_file`（`parentId`=folderId，
     `textContent`=修正後全文，`contentMimeType`=`text/plain`）。使用者要 Google 文件格式就允許轉換，
     否則設 `disableConversionToGoogleType: true`。
   - 回報檔案連結，並簡述主要修正了哪些地方。
