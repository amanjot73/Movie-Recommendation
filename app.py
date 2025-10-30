import streamlit as st
import dask.dataframe as dd
import requests
import pandas as pd
from io import StringIO

# --- Google Drive Dataset URL ---
DRIVE_FILE_ID = "1ErVPn402X-xHzsfswvqU0uEggDZKAk6k"
DRIVE_URL = f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}"


# --- Function to Fetch Poster from OMDb API ---
@st.cache_data
def get_poster(title):
    """Fetch movie poster from OMDb API"""
    try:
        url = f"http://www.omdbapi.com/?t={title}&apikey=3d95779d"
        res = requests.get(url, timeout=5).json()
        poster = res.get("Poster", "")
        if not poster or poster == "N/A":
            return "https://via.placeholder.com/80x220?text=No+Poster"
        return poster
    except Exception:
        return "https://via.placeholder.com/80x220?text=No+Poster"


# --- Load Data from Google Drive (cached for speed) ---
@st.cache_data
def load_data():
    try:
        # Download CSV from Google Drive
        response = requests.get(DRIVE_URL)
        response.raise_for_status()
        
        # Load into pandas first, then convert to dask
        df_pandas = pd.read_csv(StringIO(response.text))
        df = dd.from_pandas(df_pandas, npartitions=4)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


df = load_data()

if df is None:
    st.stop()


# --- Background & Title ---
st.markdown(f"""
<style>
/* Animated gradient background */
[data-testid="stAppViewContainer"] {{
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
  background-size: 400% 400%;
  animation: gradientBG 15s ease infinite;
}}

@keyframes gradientBG {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}

@keyframes gradientFlow {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 80% 50%; }}
  80% {{ background-position: 0% 50%; }}
}}

.title {{
  text-align: center;
  font-size: 45px;
  font-weight: 800;
  background: linear-gradient(270deg, #ff6a00, #ee0979, #00c3ff);
  background-size: 600% 600%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradientFlow 6s ease infinite;
  margin-bottom: 8px;
}}

.subtitle {{
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  color: #ffffff;
  animation: fadeIn 2s ease;
  margin-bottom: 40px;
}}

@keyframes fadeIn {{
  from {{opacity: 0;}}
  to {{opacity: 1;}}
}}

div[data-testid="stHorizontalBlock"] {{
  justify-content: center;
  align-items: center;
}}

.stButton > button {{
  width: 90%;
  background: linear-gradient(90deg, #ff6a00, #ee0979);
  border: none;
  color: white;
  font-weight: 600;
  font-size: 16px;
  padding: 0.6em 1em;
  border-radius: 12px;
  transition: 0.3s;
}}

.stButton > button:hover {{
  transform: scale(1.05);
  background: linear-gradient(90deg, #ee0979, #00c3ff);
}}
</style>

<h1 class="title">🎥 Welcome to My Movie Recommendation Site 🎬</h1>
<h3 class="subtitle">Choose the factors to search the movies</h3>
""", unsafe_allow_html=True)


# --- Button Layout ---
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1], gap="large")


if "active_filter" not in st.session_state:
    st.session_state.active_filter = None


# Buttons
with col1:
    if st.button("🎯 Ratings"):
        st.session_state.active_filter = "rating"
with col2:
    if st.button("⭐ Cast"):
        st.session_state.active_filter = "actor"
with col3:
    if st.button("🎬 Genres"):
        st.session_state.active_filter = "genre"
with col4:
    if st.button("🌐 Language"):
        st.session_state.active_filter = "language"


# Clear previous results section before showing new
if "last_output" not in st.session_state:
    st.session_state.last_output = st.empty()
st.session_state.last_output.empty()


# ================= FILTER LOGIC ================= #


# --- Ratings Filter ---
if st.session_state.active_filter == "rating":
    st.success("You have selected Ratings filter")
    k = st.slider("Minimum Ratings", 1.0, 8.0, 5.0)
    filtered = df[df['averageRating'] >= k][['primaryTitle', 'averageRating', 'genres']]
    result = (
        filtered.compute()
        .drop_duplicates(subset=['primaryTitle'])
        .sort_values(by='averageRating', ascending=False)
        .head(8)
    )
    with st.session_state.last_output.container():
        if not result.empty:
            st.markdown("### 🍿 Recommended Movies:")
            for index, row in result.iterrows():
                poster = get_poster(row['primaryTitle'])
                st.markdown(f"""
                <div style='display:flex; align-items:center; background-color:rgba(30,30,30,0.8); border-radius:12px; padding:8px; margin-bottom:8px; box-shadow:0 0 8px rgba(255,255,255,0.1);'>
                    <img src="{poster}" width="120" height="170" style="border-radius:8px; margin-right:20px;">
                    <div>
                        <h3 style='color:#00c3ff; margin-bottom:5px;'>🎬 {row['primaryTitle']}</h3>
                        <p style='color:#ffaa00; margin:0;'>⭐ <b>Rating:</b> {row['averageRating']}</p>
                        <p style='color:#cccccc; margin:0;'>🎭 <b>Genre:</b> {row['genres']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No movies match this rating.")


# --- Genre Filter ---
elif st.session_state.active_filter == "genre":
    st.success("You have selected Genre filter")
    m = df['genres'].dropna().unique().compute().tolist()
    k = st.selectbox("Select a Genre", options=sorted(m))
    filtered = df[df['genres'] == k][['primaryTitle', 'averageRating', 'genres']]
    result = (
        filtered.compute()
        .drop_duplicates(subset=['primaryTitle'])
        .sort_values(by='averageRating', ascending=False)
        .head(8)
    )
    with st.session_state.last_output.container():
        if not result.empty:
            st.markdown("### 🍿 Recommended Movies:")
            for index, row in result.iterrows():
                poster = get_poster(row['primaryTitle'])
                st.markdown(f"""
                <div style='display:flex; align-items:center; background-color:rgba(30,30,30,0.8); border-radius:12px; padding:8px; margin-bottom:8px; box-shadow:0 0 8px rgba(255,255,255,0.1);'>
                    <img src="{poster}" width="120" height="170" style="border-radius:8px; margin-right:20px;">
                    <div>
                        <h3 style='color:#00c3ff; margin-bottom:5px;'>🎬 {row['primaryTitle']}</h3>
                        <p style='color:#ffaa00; margin:0;'>⭐ <b>Rating:</b> {row['averageRating']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No movies match this genre.")


# --- Actor Filter ---
elif st.session_state.active_filter == "actor":
    st.success("You have selected Actor/Actress filter")
    m = df['primaryName'].dropna().unique().compute().tolist()
    k = st.selectbox("Select your favourite cast", options=sorted(m), index=None)
    if k:
        st.write(f"Showing movies featuring: **{k}**")
        filtered = df[df['primaryName'] == k][['primaryTitle', 'averageRating', 'genres']]
        result = (
              filtered.compute()
              .drop_duplicates(subset=['primaryTitle'])
              .sort_values(by='averageRating', ascending=False)
              .head(8)
          )
        with st.session_state.last_output.container():
            if not result.empty:
                st.markdown("### 🍿 Recommended Movies:")
                for index, row in result.iterrows():
                    poster = get_poster(row['primaryTitle'])
                    st.markdown(f"""
                    <div style='display:flex; align-items:center; background-color:rgba(30,30,30,0.8); border-radius:12px; padding:8px; margin-bottom:8px; box-shadow:0 0 8px rgba(255,255,255,0.1);'>
                        <img src="{poster}" width="120" height="170" style="border-radius:8px; margin-right:20px;">
                        <div>
                            <h3 style='color:#00c3ff; margin-bottom:5px;'>🎬 {row['primaryTitle']}</h3>
                            <p style='color:#ffaa00; margin:0;'>⭐ <b>Rating:</b> {row['averageRating']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No movies match this cast.")


# --- Language Filter ---
elif st.session_state.active_filter == "language":
    st.success("You have selected Language filter")
    m = df['language_name'].dropna().unique().compute().tolist()
    k = st.selectbox("Select your favourite language", options=sorted(m), index=None)
    if k:
        st.write(f"Showing movies featuring: **{k}**")
        filtered = df[df['language_name'] == k][['primaryTitle', 'averageRating', 'genres']]
        result = (
            filtered.compute()
            .drop_duplicates(subset=['primaryTitle'])
            .sort_values(by='averageRating', ascending=False)
            .head(8)
        )
        with st.session_state.last_output.container():
            if not result.empty:
                st.markdown("### 🍿 Recommended Movies:")
                for index, row in result.iterrows():
                    poster = get_poster(row['primaryTitle'])
                    st.markdown(f"""
                    <div style='display:flex; align-items:center; background-color:rgba(30,30,30,0.8); border-radius:12px; padding:8px; margin-bottom:8px; box-shadow:0 0 8px rgba(255,255,255,0.1);'>
                        <img src="{poster}" width="120" height="170" style="border-radius:8px; margin-right:20px;">
                        <div>
                            <h3 style='color:#00c3ff; margin-bottom:5px;'>🎬 {row['primaryTitle']}</h3>
                            <p style='color:#ffaa00; margin:0;'>⭐ <b>Rating:</b> {row['averageRating']}</p>
                            <p style='color:#cccccc; margin:0;'>🎭 <b>Genre:</b> {row['genres']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No movies match this language.")
