# Voice-to-txt

免費語音轉文字：用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)（OpenAI Whisper 的開源加速版，MIT 授權，本機執行、不用 API 費用）。

```bash
pip install -r requirements.txt
python3 transcribe.py "<音檔路徑 / 直連網址 / Google Drive 分享連結>" --language zh
```

選項：`--model`（tiny/base/small/medium/large-v3/large-v3-turbo，預設 large-v3-turbo）、
`--prompt`（人名、術語提示，提高辨識率）、`--keep-simplified`（不轉繁體）、`--out-dir`。

在 Claude Code 裡直接說「幫我把 <音檔連結> 轉成逐字稿，存到 <雲端資料夾連結>」，
Claude 會照 `CLAUDE.md` 的流程：下載 → 轉文字 → 依上下文修正 → 上傳。
