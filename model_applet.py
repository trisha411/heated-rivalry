import os
import json
import pickle
import subprocess
import sys
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
# Paths
BASE_DIR = os.path.dirname(__file__)
PRED_CSV = os.path.join(BASE_DIR, "model", "predictions_merged.csv")
MODEL_CONFIG = os.path.join(BASE_DIR, "model", "model_config.json")
MODEL_PATH = os.path.join(BASE_DIR, "model", "final_lstm_model_inference.keras")
SCALER_PATH = os.path.join(BASE_DIR, "model", "feature_scaler.pkl")
GEOJSON = os.path.join(BASE_DIR, "data", "nyc-zip-code-tabulation-areas-polygons.geojson")

@st.cache_data
def load_config():
    with open(MODEL_CONFIG, "r") as f:
        return json.load(f)

@st.cache_data
def load_scaler():
    with open(SCALER_PATH, "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_data():
    df = pd.read_csv(PRED_CSV, parse_dates=["date"]) 
    return df

@st.cache_data
def load_geo():
    gdf = gpd.read_file(GEOJSON)
    # ensure ZIP column exists and is numeric
    # try common property names
    if 'postalCode' in gdf.columns:
        gdf['zip'] = gdf['postalCode'].astype(int)
    elif 'ZIPCODE' in gdf.columns:
        gdf['zip'] = gdf['ZIPCODE'].astype(int)
    elif 'zip' not in gdf.columns:
        # try name field
        if 'boro_zip' in gdf.columns:
            gdf['zip'] = gdf['boro_zip'].astype(int)
    else:
        gdf['zip'] = gdf['zip'].astype(int)
    return gdf

def build_sequence(df_zip, features, lookback, temp_val, call_val, scaler):
    # df_zip is sorted by date ascending
    # take last `lookback` rows
    if len(df_zip) < lookback:
        return None
    seq = df_zip.tail(lookback).copy()
    # overwrite the most recent day's temp and call_count with user inputs
    last_idx = seq.index[-1]
    seq.loc[last_idx, 'max_temp'] = temp_val
    seq.loc[last_idx, 'call_count'] = call_val
    # ensure feature order
    arr = seq[features].to_numpy(dtype=float)
    # CRITICAL: Scale features using the fitted scaler
    arr = scaler.transform(arr)
    # shape (1, lookback, n_features)
    return arr.reshape((1, arr.shape[0], arr.shape[1]))


def predict_for_zip(seq, class_labels):
    payload = {
        "model_path": MODEL_PATH,
        "sequence": seq.tolist(),
        "class_labels": class_labels,
    }
    runner = r"""
import json
import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

payload = json.loads(sys.argv[1])
model = tf.keras.models.load_model(payload["model_path"], compile=False)
sequence = np.asarray(payload["sequence"], dtype=float)
preds = model.predict(sequence, verbose=0)

result = {"predicted": None, "probs": None}
if preds.ndim == 2 and preds.shape[1] == len(payload["class_labels"]):
    probs = preds[0].tolist()
    cls = int(np.argmax(probs))
    try:
        predicted = payload["class_labels"][cls]
    except Exception:
        predicted = int(cls + 1)
    result["predicted"] = predicted
    result["probs"] = probs
else:
    result["predicted"] = float(preds.ravel()[0])

print(json.dumps(result))
"""
    completed = subprocess.run(
        [sys.executable, "-c", runner, json.dumps(payload)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None, completed.stderr.strip() or completed.stdout.strip()
    try:
        result = json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        return None, f"Could not parse model output: {completed.stdout.strip()}"
    return result, None


def add_legend(map_object):
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border: 2px solid rgba(0,0,0,0.2);
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        font-size: 13px;
        line-height: 1.45;
    ">
      <strong>Predicted HVI</strong><br>
      <i style="background:#2b8cbe;width:12px;height:12px;display:inline-block;margin-right:6px"></i>1<br>
      <i style="background:#7bccc4;width:12px;height:12px;display:inline-block;margin-right:6px"></i>2<br>
      <i style="background:#fdb863;width:12px;height:12px;display:inline-block;margin-right:6px"></i>3<br>
      <i style="background:#e34a33;width:12px;height:12px;display:inline-block;margin-right:6px"></i>4<br>
      <i style="background:#7a0177;width:12px;height:12px;display:inline-block;margin-right:6px"></i>5
    </div>
    """
    map_object.get_root().html.add_child(folium.Element(legend_html))

def main():
    st.title("HVI Next-day Predictor — Interactive Explorer")
    st.write("Enter a ZIP code and adjust temperature / 311 call sliders to see next-day predicted HVI projected onto the map.")

    cfg = load_config()
    scaler = load_scaler()
    features = cfg.get('features', [])
    lookback = cfg.get('best_config', {}).get('lookback', 14)
    class_labels = cfg.get('class_labels', [1,2,3,4,5])

    df = load_data()
    gdf = load_geo()

    available_zips = sorted(df['zip'].unique())
    zip_sel = st.selectbox("Choose ZIP code", available_zips, index=0, key="zip_selector")

    # Determine slider ranges from data
    temp_min = int(df['max_temp'].min() - 5)
    temp_max = int(df['max_temp'].max() + 5)
    call_min = int(max(0, df['call_count'].min() - 10))
    call_max = int(df['call_count'].max() + 50)

    zip_median = df[df['zip'] == zip_sel]
    temp_default = int(zip_median['max_temp'].median()) if not zip_median.empty else int(df['max_temp'].median())
    call_default = int(zip_median['call_count'].median()) if not zip_median.empty else int(df['call_count'].median())

    temp_val = st.slider("Max temperature for prediction day", temp_min, temp_max, temp_default, key="temp_slider")
    call_val = st.slider("311 call count for prediction day", call_min, call_max, call_default, key="call_slider")

    df_zip = df[df['zip'] == zip_sel].sort_values('date')
    if df_zip.empty:
        st.error("No data for selected ZIP code.")
        return

    last_date = df_zip['date'].max()
    next_date = last_date + timedelta(days=1)

    seq = build_sequence(df_zip, features, lookback, temp_val, call_val, scaler)
    if seq is None:
        st.warning(f"Not enough history for ZIP {zip_sel} to build a {lookback}-day sequence.")
        st.stop()

    result, error_text = predict_for_zip(seq, class_labels)
    if result is None:
        st.error(f"Model prediction failed: {error_text}")
        return

    predicted = result["predicted"]
    probs = result["probs"]

    st.subheader(f"Next-day prediction for {next_date.date()} (ZIP {int(zip_sel)})")
    st.markdown(f"**Predicted HVI class:** {predicted}")
    if probs is not None:
        prob_df = pd.DataFrame({'HVI Class': class_labels, 'Probability': probs})
        # show HVI class as a normal column (not index) and format probabilities
        prob_df['Probability'] = prob_df['Probability'].round(4)
        st.table(prob_df)
    st.caption("The selected ZIP is colored by the predicted HVI class using a cool-to-warm sequential scale.")

    gdf_copy = gdf.copy()
    gdf_copy['zip'] = gdf_copy['zip'].astype(int)
    gdf_copy['predicted'] = np.nan
    gdf_copy['fill_value'] = np.nan
    gdf_copy.loc[gdf_copy['zip'] == zip_sel, 'predicted'] = int(predicted)
    gdf_copy.loc[gdf_copy['zip'] == zip_sel, 'fill_value'] = float(predicted)

    centroid = gdf_copy[gdf_copy['zip'] == zip_sel].geometry.centroid.iloc[0]
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=12, tiles='cartodbpositron')

    color_map = {
        1: '#2b8cbe',
        2: '#7bccc4',
        3: '#fdd49e',
        4: '#fc8d59',
        5: '#d7301f',
    }
    
    discrete_legend_html = '''
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border: 2px solid rgba(0,0,0,0.2);
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        font-size: 13px;
        line-height: 1.5;
        font-weight: 500;
    ">
        <div style="margin-bottom: 8px; font-weight: bold;">Max Probability Predicted HVI Class</div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="background:#2b8cbe; width: 14px; height: 14px; margin-right: 8px; border: 1px solid #333;"></div>
            <span>1 (Least Vulnerable)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="background:#7bccc4; width: 14px; height: 14px; margin-right: 8px; border: 1px solid #333;"></div>
            <span>2</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="background:#fdd49e; width: 14px; height: 14px; margin-right: 8px; border: 1px solid #333;"></div>
            <span>3</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="background:#fc8d59; width: 14px; height: 14px; margin-right: 8px; border: 1px solid #333;"></div>
            <span>4</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background:#d7301f; width: 14px; height: 14px; margin-right: 8px; border: 1px solid #333;"></div>
            <span>5 (Most Vulnerable)</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(discrete_legend_html))

    def style_function(feature):
        is_selected = feature['properties'].get('zip') == int(zip_sel)
        fill_value = feature['properties'].get('fill_value')
        fill_color = color_map.get(int(fill_value), '#f0f0f0') if fill_value is not None and not np.isnan(fill_value) else '#f0f0f0'
        return {
            'fillColor': fill_color if is_selected else '#f0f0f0',
            'color': '#111111' if is_selected else '#bdbdbd',
            'weight': 2.5 if is_selected else 0.7,
            'fillOpacity': 0.85 if is_selected else 0.12,
        }

    folium.GeoJson(
        data=gdf_copy.to_json(),
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['zip', 'predicted'],
            aliases=['ZIP Code', 'Predicted HVI'],
            localize=False,
            sticky=False,
        ),
        highlight_function=lambda feature: {'weight': 4, 'color': '#000000', 'fillOpacity': 0.9},
    ).add_to(m)

    st.subheader('Map')
    st_folium(m, width=900, height=650)

    # Show last few rows used for sequence
    st.subheader('Rows used for LSTM sequence')
    st.dataframe(df_zip.tail(lookback)[features + ['date']].reset_index(drop=True))

if __name__ == '__main__':
    main()
