# FAT NM

Working pages for the First American New Mexico pending parcels: `pull-list/` (starter parcels) and `catalog/` (document catalog). Rebuild with `python3 build/build_site.py build/shell.html <artifact_data.json> <starters.json> <docs.json> .`

## Hourly refresh

`scan-nm-uploads.ps1` runs hourly (Mon–Fri, 7:05 AM–9:05 PM Central) on JONDESK as the Windows task "FAT NM hourly upload scan". It copies new uploads into the pending parcel folders (copy only) and writes `On file status (auto).csv` and `Scan log (auto).csv` to `Shared Documents/Pending Parcels - Pull List & Catalogue (2026-11-17)/Hourly scan/`.

A scheduled Claude task refreshes these pages afterwards:
- incremental: `python3 build/refresh_from_log.py <scan log csv> . "<label>"` applies copied rows newer than `build/last_log_run.txt`;
- full: `python3 build/refresh_onfile.py "<On file status (auto).csv>" . "<label>"` recomputes On file and the catalog's recorded-doc and index lists.
