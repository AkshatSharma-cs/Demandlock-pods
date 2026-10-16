# DemandLock Pods ASR evaluation

- Requires Python 3.10+ and a working backend environment. From the repository root, install the CPU package: `python -m pip install faster-whisper`.
- Set `ENABLE_ASR=true` before running. Optional: set `WHISPER_MODEL=small`; the CLI `--model` value overrides it.
- The first run downloads the selected model. Run with network access once, then keep the model cache for offline evaluation. Tests need not call ASR or the network.
- Record 15 short, clear clips: one request per clip, in the language named by the filename. Use simulated job requests only; avoid personal information.
- Save clips as `hi_01.wav` … `hi_05.wav`, `ta_01.wav` … `ta_05.wav`, and `en_01.wav` … `en_05.wav` in `backend/scripts/audio/`. Mono 16-kHz PCM WAV is recommended; avoid background music and leave a short pause at each end.
- Speak each reference scenario clearly: mobile screen repair, 2 helpers, ₹12,000 per month; tailoring training, 5 seats; solar panel work, 2 helpers, ₹500 per day; computer operator; kitchen helper, 3 helpers, ₹600 per day. Local-language phrasing is fine, but keep the intended values unchanged.
- Review `refs_template.csv`: skill labels are canonical English labels, `expected_slots` is a count, and `expected_pay_minor` is paise (rupees × 100). Leave an expected field blank to skip its comparison.
- Run: `python backend/scripts/asr_eval.py --audio_dir backend/scripts/audio --refs backend/scripts/refs_template.csv --model small --report backend/scripts/asr_report.json`
- A language is GO when at least 80% of its clips pass all non-blank field checks. A failed/uncertain language should use typed input; passing this small evaluation is not a guarantee of production accuracy.