# Using an LSTM Model to Construct a Temporally-Evolving Heat Vulnerability Index (HVI) for NYC

## Relevant Scripts
### aggregateData.R
Inputs: Datasets from data folder

Outputs: allData.csv, data_NAandSteamOmitted.csv

Goal: take heat vulnerability-relevant datasets and create a .csv file with relevant variables across time and ZIP code.

### ML Tree Stuff.Rmd
Goal: prepare tree counts and 311 calls datasets for use in aggregateData.R

### TemporalHVI_LSTM_model.ipynb
Inputs: data_NAandSteamOmitted.csv

Outputs (in the "model" folder): Final LSTM model & hyperparameter tuning outputs

Goal: Create and evaluate initial baseline models (XGBoost, Decision Tree, Random Forest), then create (and tune hyperparameters for) the final LSTM model. Export the final LSTM model and create figures exploring the results and comparing them to the XGBoost baseline.

### final_maps.ipynb
Inputs: NYC zip code polygons from the "data" folder, LSTM model from the "model" folder

Outputs (in the "model" folder): Map figures and gif showing predictions from the LSTM model.

Goal: Make maps to visualize predicted temporal HVI and how it varies over time.

## Other Components
### environment.yml
Creates the heated_rivalry Conda environment (with some pip dependencies) necessary to run all .ipynb and .py scripts.

### model folder
Stores the hyperparameter tuning results (.csv), map figures (.png, .gif), and all components of the model itself for the final LSTM model.

### data folder
Stores .csv files for all used datasets

### hollander_applet.py
An applet (titled after Shane Hollander from Heated Rivalry!) to interactively query the trained LSTM model and visualize next-day HVI predictions by ZIP code. In order to run the app, use the following Terminal commands to create the heated_rivalry environment and open the app in-browser:

```bash
conda env create -f environment.yml
conda activate heated_rivalry
streamlit run app_streamlit.py
```
In case the applet does not run or if there are issues with creating the Conda environment, please refer to "model_applet_demo.mov" to see a demo of the applet.
