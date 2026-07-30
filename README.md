# GTSS Pakistan — Tobacco Survey Dashboard

A multi-page Streamlit dashboard for Pakistan's Global Tobacco Survey (GATS + GYTS) data.

## Folder structure

```
pakistan_tobacco_dashboard/
├── app.py                              ← Overview / Home page (run this)
├── requirements.txt
├── assets/
│   └── cover.png                       ← Cover image shown on Overview page
├── data/
│   ├── gats_2014_LABELED.csv
│   ├── gyts_2022_LABELED.csv
│   ├── gyts_2013_aggregated_LABELED.csv
│   ├── gats_2024_key_indicators_LABELED.csv
│   ├── gyts_2022_derived_indicators_LABELED.csv
│   └── gats_2014_vs_2024_comparison_LABELED.csv
├── utils/
│   ├── data_loader.py                  ← cached CSV loading functions
│   └── styling.py                      ← shared colors/helpers
└── pages/
    ├── 1_📊_Adults_GATS_2014.py
    ├── 2_🎓_Youth_GYTS_2022.py
    ├── 3_📈_Youth_GYTS_2013.py
    ├── 4_🚬_Adults_GATS_2024.py
    ├── 5_⭐_KPI_Cards_GYTS_2022.py
    └── 6_🔀_Trend_2014_vs_2024.py
```

Streamlit automatically turns every file in `pages/` into a sidebar navigation entry —
you don't need to wire this up manually.

## Setup on Windows (Python 3.11)

Open **Command Prompt** or **PowerShell** in the folder that CONTAINS
`pakistan_tobacco_dashboard` (i.e. one level above it), then run:

```powershell
cd pakistan_tobacco_dashboard

:: 1. Create a virtual environment using Python 3.11
py -3.11 -m venv venv

:: 2. Activate it
venv\Scripts\activate

:: 3. Install dependencies
pip install -r requirements.txt

:: 4. Run the dashboard
streamlit run app.py
```

If `py -3.11` doesn't work, replace it with the full path to your Python 3.11 install, e.g.:
```powershell
"C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
```

After `streamlit run app.py`, it will open automatically in your browser
(usually at `http://localhost:8501`). Use the sidebar to move between pages.

## Notes

- All filtering/charts run on the CSVs already in `data/` — nothing needs to be
  downloaded again.
- `GATS_2014` and `GYTS_2022` are row-level, so their pages have live sidebar filters
  (age, gender/sex, region, grade).
- `GYTS_2013`, `GATS_2024`, the derived-indicators file, and the comparison file are
  pre-aggregated, so those pages show fixed percentage charts/KPI cards instead of
  live filters.
- To stop the app, go back to the terminal and press `Ctrl + C`.
- Next time you want to run it, you only need steps 2 and 4 (activate + run) —
  no need to recreate the venv or reinstall packages.
