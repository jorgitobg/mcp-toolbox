# Tender triage report provenance

`triage_report.json` is the unmodified JSON output of
[open-tender-radar](https://github.com/jorgitobg/open-tender-radar) at commit `8c39fa2`:

```bash
python -m open_tender_radar --profile examples/profile.yaml \
  --ted tests/fixtures/ted_search_sample.json --placsp tests/fixtures/placsp_sample.atom \
  --today 2026-11-04 --format json
```

Inputs are recorded public TED / PLACSP notices (already scrubbed of third-party data upstream)
screened against a fictional profile. Verdicts are rule-based screening results, not bid advice.
Evidence strings are pinned to the recording date 2026-11-04 ("days left" is not recomputed).
