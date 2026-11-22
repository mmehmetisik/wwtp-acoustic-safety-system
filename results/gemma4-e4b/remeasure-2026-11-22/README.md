# Re-measurement — 22 November 2026

The April 2026 headline (91.0/100, S5 "CERTAIN SURVIVAL") came from a single run ([`../run_output.txt`](../run_output.txt)). In that configuration the few-shot reference spectrograms for S1–S4 were taken from the same scenes that were scored, and the S4 human reference was itself one of the scored windows. This folder re-measures the result.

## Setup

- **Machine:** Windows 11 laptop, NVIDIA RTX 3060 Laptop GPU (6 GB VRAM).
- **Model:** `gemma4:e4b`, manifest digest `c6eb396dbd59…`, pulled 2026-04-03. These are the same weights as the April run.
- **Engine:** `acoustic_engine.py` as of commit `73fe901` (the April version), plus the reference-selection fix (`referanslari_sec`).
  - With the fix, no reference spectrogram comes from the scene being scored.
  - The `--sizintili-referans` flag ("leaky references") restores the April reference set.
- **Command:** `python acoustic_engine.py PROTOCOL --spectrogram [--sizintili-referans]` at temperature 0, as in April.
- **Runtimes:**
  - **Ollama 0.40.17:** the installed Windows app, which had updated itself that day.
  - **Ollama 0.20.2:** the portable build from the official GitHub release (`ollama-windows-amd64.zip`, sha256 `f26ead8baa55e919828ffe88cddf3e588444891e43e19a059f1d6c933fb1a5b6`). It was the newest release when the April log was committed (2026-04-06).
  - The 0.20.2 runs went through a wrapper that changed only the Ollama port (11434 → 11435), so the installed app stayed untouched. That is the `[sarmalayıcı]` ("wrapper") line at the top of those logs.

## Results

All scores are PROTOCOL mode, weighted average: S1 ×0.1, S2 ×0.2, S3 ×0.1, S4 ×0.2, S5 ×0.4.

| Run | S1 | S2 | S3 | S4 | S5 | Weighted | Log |
|-----|----|----|----|----|----|----------|-----|
| April 2026, single run, runtime likely 0.20.x | 60 | 95 | 60 | 100 | 100 | 91.0 | [`../run_output.txt`](../run_output.txt) |
| 0.20.2, April references, run 1 | 60 | 75 | 60 | 100 | 0 | 47.0 | [`ollama-0.20.2_legacy-refs_run1.txt`](ollama-0.20.2_legacy-refs_run1.txt) |
| 0.20.2, April references, run 2 | 60 | 95 | 60 | 100 | 0 | 51.0 | [`ollama-0.20.2_legacy-refs_run2.txt`](ollama-0.20.2_legacy-refs_run2.txt) |
| **0.20.2, leak-free references** | **60** | **75** | **60** | **90** | **0** | **45.0** | [`ollama-0.20.2_leak-free_run1.txt`](ollama-0.20.2_leak-free_run1.txt) |
| 0.40.17, April references | 60 | 0 | 60 | 0 | 0 | 12.0 | [`ollama-0.40.17_legacy-refs.txt`](ollama-0.40.17_legacy-refs.txt) |
| 0.40.17, leak-free references | 60 | 0 | 60 | 0 | 0 | 12.0 | [`ollama-0.40.17_leak-free.txt`](ollama-0.40.17_leak-free.txt) |

Every run in the table is a valid log: 60/60 windows `parse:ok` and no `[FAILED]` request. One more log is kept as evidence of a bug and is **not** a result (see finding 5).

The engine's final line, `GRAND WEIGHTED AVERAGE`, divides by three modes even when only PROTOCOL runs; for example, 45.0 is printed as 15.0. Read the PROTOCOL row instead.

## Findings

1. **91.0 did not reproduce.**
   - Same code and weights on the April-era runtime gave 47.0 and 51.0.
   - Almost the whole gap is S5. Its single April alarm window (25–30 s, confidence 0.75) did not alarm in any 0.20.2 run (confidence 0.3).
2. **The reference leak was real but small on this set: 47.0 → 45.0.**
   - In S4, two windows lost their alarm: the April human reference itself (25–30 s) and the window right after it (30–35 s).
   - The 40–45 s and 50–55 s windows still alarm.
3. **Temperature 0 did not make runs identical.**
   - The two identical 0.20.2 runs differ in 5 of 60 windows. In S2 at 25–30 s, one run gave no alarm (0.2) and the other an alarm (0.75).
   - April vs. run 1 agree on 55/60 windows, the same size as this run-to-run noise.
   - A single run is not a reliable score. Report the mean and range of several runs.
4. **The Ollama version changes the result.**
   - [`vision-check_ollama-0.40.17.txt`](vision-check_ollama-0.40.17.txt): on 0.40.17, gemma4:e4b describes the S4 spectrogram as a "line chart". It answers "no human" (0.2) for a target image byte-identical to its own human reference. The control model qwen3.5:4b reads the same image correctly.
   - [`vision-check_ollama-0.20.2.txt`](vision-check_ollama-0.20.2.txt): on 0.20.2, the same test gives "human detected" (0.9) and a correct description.
   - Prompt tokens for the same single-image request: 184 on 0.40.17, 282 on 0.20.2.
   - Tested on this machine only.
5. **An analysis failure is scored as "no human".**
   - [`INVALID_ollama-0.20.2_leak-free_model-deleted-http404.txt`](INVALID_ollama-0.20.2_leak-free_model-deleted-http404.txt): during this run the model files were deleted, most likely by an automatic temp-folder cleanup.
   - From the third window of S2 on, every request returned HTTP 404. The engine recorded each window as `parse:empty_response`, confidence 0.0, no alarm, and finished normally with 12.0.
   - A safety system must report this as a fault (fail-closed), not as "no human detected".
6. **No false alarms in the no-human scenes (S1, S3)** in any run.
