import streamlit as st  
import pandas as pd  
import plotly.graph_objects as go  
from PIL import Image  
import requests  
from io import BytesIO  
import random  
import os  
import ast  
import base64  
import re

# Configuration de la page  
st.set_page_config(page_title="NETFIX Movies", page_icon=":movie_camera:", layout="wide", initial_sidebar_state="expanded")

# Chargement des données avec compression et colonnes spécifiques
@st.cache_data(ttl=3600)  # Cache d'une heure
def load_data():
    base_dir = os.path.dirname(__file__)
    columns_to_load = ['id', 'title_fr', 'startYear', 'duration', 'averageRating', 
                      'numVotes', 'genres', 'directors', 'actors', 'resume', 
                      'poster_path', 'url_bande_annonce']
    try:
        df_reco = pd.read_parquet("https://drive.google.com/uc?id=1F1Ht2JGQAI5nSoVAOFgRJOSXt0KSS2o2")
        df = pd.read_parquet(os.path.join(base_dir, 'df_complet.parquet'),
                            columns=columns_to_load)
    except FileNotFoundError as e:
        st.error(f"Erreur : Le fichier n'a pas été trouvé. Détails : {e}")
        return None, None
    except pd.errors.EmptyDataError:
        st.error("Erreur : Le fichier est vide.")
        return None, None
    except pd.errors.ParserError:
        st.error("Erreur : Problème lors de l'analyse du fichier.")
        return None, None
    return df_reco, df

df_reco, df = load_data()

# Chargement des données
df_reco, df = load_data()

# Preprocessing des données avec gestion d'erreurs
@st.cache_data  
def preprocess_data(df):
    if df is None:
        return set(), set(), set()

    all_genres = set()
    all_directors = set()
    all_actors = set()

    try:
        for _, row in df.iterrows():
            if pd.notna(row['genres']):
                genres_list = ast.literal_eval(row['genres'])
                all_genres.update(genres_list)
            if pd.notna(row['directors']):
                directors_list = ast.literal_eval(row['directors'])
                all_directors.update(directors_list)
            if pd.notna(row['actors']):
                actors_list = ast.literal_eval(row['actors'])
                all_actors.update(actors_list)
    except Exception as e:
        st.warning(f"Erreur lors du preprocessing des données : {str(e)}")

    return all_genres, all_directors, all_actors

if df is not None:
    all_genres, all_directors, all_actors = preprocess_data(df)

# Styles CSS avec correction pour l'image de fond
st.markdown("""
<style>
.stApp {
    background-color: #1a1a1d;
    color: red;
    font-family: 'San Francisco', sans-serif;
}
.navbar {
    background-color: #000;
    padding: 10px;
    display: flex;
    justify-content: space-around;
    position: sticky;
    top: 0;
    z-index: 1000;
}
.nav-item {
    color: white;
    text-decoration: none;
    padding: 10px;
    border-radius: 4px;
}
.nav-item:hover {
    background-color: rgba(233, 9, 20, 0.6);
}
.title {
    font-family: 'Archivo Black', sans-serif;
    font-size: 20rem; 
    font-weight: bold;
    text-align: center;
    color: #e50914;
    text-shadow: 0 0 20px #e50914, 0 0 40px #e50914;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
}
.movie-carousel {
    width: 100%;
    overflow: hidden;
    height: 200px;
    position: relative;
    margin: 20px 0;
}
.movie-carousel-inner {
    display: flex;
    animation: scroll 30s linear infinite;
    gap: 20px;
}
.movie-card {
    border: 1px solid #333;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.7);
}
.footer {
    text-align: center;
    padding: 20px;
    background: rgba(0, 0, 0, 0.9);
    color: #ffffff;
    opacity: 0.7;
    font-size: 0.9rem;
    border-top: 2px solid #e50914;
}
</style>
""", unsafe_allow_html=True)

# Chargement de l'image de fond avec gestion d'erreurs
try:
    image_path = os.path.join(os.path.dirname(__file__), 'background-pic.avif')
    with open(image_path, "rb") as f:
        background_image = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
                .stApp {{
                    background-image: url(data:image/jpeg;base64,{background_image});
                    background-size: cover;
                    background-repeat: no-repeat;
                }}
            </style>
        """, unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Impossible de charger l'image de fond : {str(e)}")

def navigation():
    st.markdown("""
    <div class="navbar">
        <a class="nav-item" href="#home">Accueil</a>
        <a class="nav-item" href="#search">Recherche & Recommandations</a>
        <a class="nav-item" href="#kpi">KPI</a>
    </div>
    """, unsafe_allow_html=True)

def afficher_affiche(poster_path, size=300):
    try:
        if isinstance(poster_path, str) and poster_path:
            # Vérifiez si le chemin de l'affiche commence par "http"
            if not poster_path.startswith("http"):
                poster_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
                
            # Effectuez la requête GET  
            response = requests.get(poster_path, timeout=5)
            response.raise_for_status()

            # Vérifiez si le contenu est de type image  
            if 'image' in response.headers.get('Content-Type', ''):
                img = Image.open(BytesIO(response.content))
                return img  
            else:
                st.warning("Le contenu récupéré n'est pas une image.")
                return None

    except requests.exceptions.RequestException as req_err:
        st.warning(f"Erreur lors de la requête : {str(req_err)}")
    except IOError as io_err:
        st.warning(f"Erreur lors de l'ouverture de l'image : {str(io_err)}")
    except Exception as e:
        st.warning(f"Erreur inattendue : {str(e)}")
    
    return None

def extraire_youtube_id(url):
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu.be\/|youtube.com\/embed\/)([^&\n?]*)',
        r'youtube.com/shorts/([^&\n?]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def afficher_indicateur_de_note(note, film_id, size=100):
    try:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(note),
            title={'text': "Note moyenne", 'font': {'color': '#ff6f61', 'size': 14}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 10], 'tickcolor': "white"},
                'bar': {'color': "#ff6f61"},
                'steps': [
                    {'range': [0, 3], 'color': "#d3d3d3"},
                    {'range': [3, 7], 'color': "#f2b40f"},
                    {'range': [7, 10], 'color': "#1fae2d"}
                ]
            }
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            font=dict(color="white", size=10),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=False, key=f"gauge_{film_id}_rating")
    except Exception as e:
        st.warning(f"Erreur lors de l'affichage de l'indicateur : {str(e)}")

def afficher_fiche_film(film_details):
    try:
        st.markdown('<div class="movie-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 4, 1])
        
        with col1:
            img = afficher_affiche(film_details['poster_path'], size=250)
            if img is not None:
                st.image(img, width=250)
            else:
                st.markdown("🎬 Affiche non disponible")
        
        with col2:
            st.subheader(film_details['title_fr'])
            if pd.notna(film_details['startYear']):
                st.text(f"Année : {int(film_details['startYear'])}")
            if pd.notna(film_details['duration']):
                st.text(f"Durée : {int(film_details['duration'])} minutes")
            if pd.notna(film_details['averageRating']) and pd.notna(film_details['numVotes']):
                st.text(f"Note moyenne : {film_details['averageRating']:.1f} / 10 ⭐ ({int(film_details['numVotes'])} votes)")
            
            # Affichage des genres, réalisateurs et acteurs avec gestion d'erreurs
            try:
                if pd.notna(film_details['genres']):
                    genres = ast.literal_eval(film_details['genres'])
                    st.text(f"Genres : {', '.join(genres)}")
            except:
                st.text("Genres : Information non disponible")
            
            try:
                if pd.notna(film_details['directors']):
                    directors = ast.literal_eval(film_details['directors'])
                    st.text(f"Réalisateur(s) : {', '.join(directors)}")
            except:
                st.text("Réalisateur(s) : Information non disponible")
            
            try:
                if pd.notna(film_details['actors']):
                    actors = ast.literal_eval(film_details['actors'])
                    st.text(f"Acteur(s) : {', '.join(actors)}")
            except:
                st.text("Acteur(s) : Information non disponible")

            if pd.notna(film_details['resume']):
                st.text(f"Résumé : {film_details['resume']}")
            else:
                st.text("Résumé : Aucun résumé disponible")
        
        with col3:
            if pd.notna(film_details['averageRating']):
                afficher_indicateur_de_note(film_details['averageRating'], film_details['id'])
        
        # Affichage de la bande-annonce
        if pd.notna(film_details['url_bande_annonce']):
            youtube_id = extraire_youtube_id(film_details['url_bande_annonce'])
            if youtube_id:
                st.subheader("Bande-annonce")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center;">
                        <div style="width: 80%;">
                            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
                                <iframe
                                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                                    src="https://www.youtube.com/embed/{youtube_id}"
                                    frameborder="0"
                                    allowfullscreen
                                ></iframe>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de la fiche film : {str(e)}")

def display_recommendations(selected_film, df, df_reco):
    try:
        if df_reco is None or df is None:
            st.warning("Les données de recommandation ne sont pas disponibles")
            return
            
        st.markdown("### Films recommandés")
        if selected_film.name not in df_reco.index:
            st.warning("Pas de recommandations disponibles pour ce film")
            return
            
        reco_row = df_reco.loc[selected_film.name]
        
        for i in range(5):
            reco_col = f'reco_{i+1}'
            if reco_col not in reco_row.index:
                continue
                
            reco_index = reco_row[reco_col]
            if pd.notna(reco_index) and reco_index in df.index:
                reco_film = df.loc[reco_index]
                afficher_fiche_film(reco_film)
                st.markdown("<hr>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur lors de l'affichage des recommandations : {str(e)}")

def create_movie_carousel():
    try:
        if df is None or df.empty:
            st.warning("Impossible de créer le carrousel : données non disponibles")
            return
            
        random_movies = df.sample(n=min(30, len(df)))
        carousel_html = '<div class="movie-carousel"><div class="movie-carousel-inner">'
        
        for _, movie in random_movies.iterrows():
            if isinstance(movie['poster_path'], str) and movie['poster_path']:
                poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                carousel_html += f'<img src="{poster_url}" alt="{movie["title_fr"]}" style="height: 200px;">'
        carousel_html += '</div></div>'
        st.markdown(carousel_html, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Erreur lors de la création du carrousel : {str(e)}")

def home_page():
    try:
        st.markdown('<a id="home"></a>', unsafe_allow_html=True)
        
        st.markdown('<div class="logo"><img src="https://i.ibb.co/2SD6NzT/NF1.webp" alt="Logo" width="100" /></div>', unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center;'>Bienvenue sur NETFIX</h1>", unsafe_allow_html=True)

        if df is not None:
            # Affichage des films aléatoires en grille
            cols = st.columns(4)
            random_movies = df.sample(n=min(16, len(df)))
            
            for i, (_, movie) in enumerate(random_movies.iterrows()):
                with cols[i % 4]:
                    if pd.notna(movie['poster_path']):
                        poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                        try:
                            st.image(poster_url, width=300)
                        except Exception:
                            st.image("https://via.placeholder.com/300x450?text=Image+non+disponible")

            # Vidéo d'accueil
            try:
                st.video('http://psengonemouity.fr/video-accueil.mp4')
            except Exception as e:
                st.warning("La vidéo d'accueil n'a pas pu être chargée")

            # Deuxième série de films aléatoires
            cols = st.columns(4)
            random_movies = df.sample(n=min(16, len(df)))
            
            for i, (_, movie) in enumerate(random_movies.iterrows()):
                with cols[i % 4]:
                    if pd.notna(movie['poster_path']):
                        poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                        try:
                            st.image(poster_url, width=300)
                        except Exception:
                            st.image("https://via.placeholder.com/300x450?text=Image+non+disponible")
        else:
            st.error("Impossible de charger les données des films")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page d'accueil : {str(e)}")

def search_page():
    try:
        st.markdown('<a id="search"></a>', unsafe_allow_html=True)
        st.header("Recherche de Films")
        
        if df is None:
            st.error("Impossible de charger les données de recherche")
            return
            
        create_movie_carousel()

        # Filtres de recherche
        search_term = st.text_input("🔍 Rechercher un film", "")
        
        sorted_genres = sorted(list(all_genres)) if all_genres else []
        genre_filter = st.multiselect("Filtres de genre", sorted_genres)
        
        year_min = int(df['startYear'].min()) if not df['startYear'].empty else 1900
        year_max = int(df['startYear'].max()) if not df['startYear'].empty else 2024
        year_filter = st.slider("Filtrer par année", 
                              min_value=year_min,
                              max_value=year_max,
                              value=(year_min, year_max))
        
        sorted_directors = sorted(list(all_directors)) if all_directors else []
        director_filter = st.multiselect("Filtres de réalisateur", sorted_directors)
        
        sorted_actors = sorted(list(all_actors)) if all_actors else []
        actor_filter = st.multiselect("Filtres d'acteur", sorted_actors)

        # Application des filtres
        mask = pd.Series(True, index=df.index)
        
        if search_term:
            mask &= df['title_fr'].str.contains(search_term, case=False, na=False)
        
        if genre_filter:
            mask &= df['genres'].apply(lambda x: 
                any(genre in genre_filter for genre in ast.literal_eval(x)) 
                if pd.notna(x) and isinstance(x, str) else False
            )
        
        mask &= (df['startYear'] >= year_filter[0]) & (df['startYear'] <= year_filter[1])
        
        if director_filter:
            mask &= df['directors'].apply(lambda x: 
                any(director in director_filter for director in ast.literal_eval(x))
                if pd.notna(x) and isinstance(x, str) else False
            )
        
        if actor_filter:
            mask &= df['actors'].apply(lambda x: 
                any(actor in actor_filter for actor in ast.literal_eval(x))
                if pd.notna(x) and isinstance(x, str) else False
            )

        filtered_df = df[mask]

        if not filtered_df.empty:
            selected_title = st.selectbox("Sélectionnez un film", filtered_df['title_fr'].tolist())
            if selected_title:
                try:
                    selected_index = df[df['title_fr'] == selected_title].index[0]
                    selected_film = df.iloc[selected_index]
                    afficher_fiche_film(selected_film)
                    display_recommendations(selected_film, df, df_reco)
                except Exception as e:
                    st.error(f"Erreur lors de l'affichage du film sélectionné : {str(e)}")
        else:
            st.warning("Aucun film ne correspond à ces critères de recherche.")
            
    except Exception as e:
        st.error(f"Erreur lors de la recherche : {str(e)}")

def top_20_movies_page():
    try:
        st.header("Top 20 Films les Plus Populaires")
        
        if df is None:
            st.error("Impossible de charger les données des films")
            return
            
        top_20_movies = df.nlargest(20, 'numVotes')
        
        for _, movie in top_20_movies.iterrows():
            afficher_fiche_film(movie)
            st.markdown("<hr>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erreur lors de l'affichage du top 20 : {str(e)}")

def footer():
    st.markdown("""
    <div class="footer">
        <p>© 2024 NETFIX - Votre plateforme futuriste de recommandation de films</p>
    </div>
    """, unsafe_allow_html=True)

# Interface principale
try:
    with st.sidebar:
        selection = st.selectbox(
            "Menu",
            ["Accueil", "Recherche & Recommandations", "Les plus populaires"]
        )

    if selection == "Accueil":
        home_page()
    elif selection == "Recherche & Recommandations":
        search_page()
    elif selection == "Les plus populaires":
        top_20_movies_page()

    footer()
    
except Exception as e:
    st.error(f"Erreur critique de l'application : {str(e)}")