# PROTOTYPE: Using ML to Construct a Temporally-Evolving Heat Vulnerability Index (HVI) for NYC

## Relevant Scripts
### aggregateData.R
Inputs: Datasets from data folder

Outputs: allData.csv, data_NAandSteamOmitted.csv

Goal: take heat vulnerability-relevant datasets and create a .csv file with relevant variables across time and ZIP code.

### ML Tree Stuff.Rmd
Goal: prepare tree counts and 311 calls datasets for use in aggregateData.R

### Final_Prototype_Pipeline.ipynb
Inputs: data_NAandSteamOmitted.csv

Outputs: Decision tree, random forest, and XGBoost models for temporal HVI

Goal: Use machine learning to create baseline models with three different methods to predict HVI temporally for each ZIP code. Ground-truth these models against the given HVI from the NYC government and see if HVI changes temporally.

## Other Components
### environment.yml
Necessary dependencies for .ipynb files

### data folder
Stores .csv files for all used datasets

## Streamlit HVI Predictor

A lightweight Streamlit app to interactively query the trained LSTM model and visualize next-day HVI predictions by ZIP code.

Run the app:

```bash
conda env update -f environment.yml --prune
conda activate heated_rivalry
streamlit run app_streamlit.py
```

Or install pip packages and run:

```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```

Files added:
- `app_streamlit.py` — interactive Streamlit UI
- `requirements.txt` — pip installable deps

Notes:
- On macOS Apple Silicon, `tensorflow-macos` and `tensorflow-metal` are recommended (included in `environment.yml`).
- `geopandas` is installed via conda-forge to ensure native geospatial libs are available.
