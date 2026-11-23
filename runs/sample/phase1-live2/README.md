# Sample run (live run 2, 8 GB M2)

The only complete live run from Phase 1: `qwen2.5:7b` + `nomic-embed-text`, extraction
prompt v1.1.0, design v1.0.0, risk v1.0.0, critic v1.0.0. Kept as evidence for the
failure log (`notes/phase1_failures.md`, F4-F10). It predates the later fixes, so it shows
known problems: 94 requirements (over-extraction), a catch-all approach item, risk
repetition. Wall time 72.8 min, 2 critic revisions, critic passed on the final pass.
