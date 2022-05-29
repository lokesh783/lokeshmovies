import pandas as pandas_lib
import pickle
import matplotlib.pyplot as mat_lib
import seaborn as seaborn_lib
import pickle
import pyrebase
import numpy as np
import pandas as pd
import pickle
from flask import Flask
import requests
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# PICKLE FILE IMPORTS
final_data = pickle.load(open('movies.pkl', 'rb'))                # MOVIE LENS DATAS
corrMatrix = pickle.load(open('corrMatrix.pkl', 'rb'))            # USED FOR ITEM ITEM RECOMMENDATION 
most_rated = pickle.load(open('most_rated.pkl', 'rb'))            # MOST RATED MOVIES PICKLE FILE
p_t = pickle.load(open('KNN.pkl', 'rb'))                          # PIVOT TABLE FROM KNN BASED PICKLE FILE
most_popular = pickle.load(open('most_popular.pkl','rb'))         # MOST POPULAR MOVIES PICKLE FILE

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# DATA FILE IMPORTS   
KNN_data = pandas_lib.read_csv(r"Datasets\clean_dataa.csv")
movieLens = pd.read_csv('Datasets/movies.csv')
links = pd.read_csv('Datasets/links.csv')
tmdb_movies = pd.read_csv('Datasets/tmdb_5000_credits.csv')
data = pandas_lib.read_csv( r'Datasets/clean_data.csv')

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# CONTENT BASED MODELLING TASKS STARTS
feat = ['id', 'original_title']
mov_and_id = data[feat]
similarities = pickle.load(open('content_engine.pkl', 'rb'))
indexes = data.index

# indices is storing index of each tmdb movie
indices = pandas_lib.Series(indexes, index=data['original_title'])

# # CONTENT BASED MODELLING TASKS ENDS
# --------------*---------------*----------------*--------------*-----------------*------------------ #

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# KNN IMPORTANT TASKS MODEL MAKING STARTS
mat = csr_matrix(p_t.values)
ML = NearestNeighbors(metric='cosine', algorithm='brute')
ML.fit(mat)
# KNN END

# --------------*---------------*----------------*--------------*-----------------*------------------ #
# FETCH MOVIE DETAILS WITH CAST DETAILS
def movie_det(movie_id):
    cast_apip = "https://api.themoviedb.org/3/movie/{}/credits?api_key=99ffc5d2819f29106760b616189e633a&language=en-US".format(
        movie_id)
    apip = "https://api.themoviedb.org/3/movie/{}?api_key=99ffc5d2819f29106760b616189e633a&append_to_response=videos".format(
        movie_id)
    movv_det = requests.get(apip)
    cast_deta = requests.get(cast_apip)
    movv_det = movv_det.json()
    cast_deta = cast_deta.json()
    mov_cast = cast_deta['cast']
    cast_pic = []
    cast_name = []
    k=0;
    for parr in mov_cast:
        k=k+1
        if k==21:
            break
        cast_pic_path = parr['profile_path']
        cast_pic.append("https://image.tmdb.org/t/p/w500" + str(cast_pic_path))
        cast_name_path = parr['name']
        cast_name.append(cast_name_path)
    poster_path_url = str(movv_det['poster_path'])
    back_path_url = str(movv_det['backdrop_path'])
    full_pospath_url = "https://image.tmdb.org/t/p/w500" + poster_path_url
    full_backpath_url = "https://image.tmdb.org/t/p/w500" + back_path_url

    mov_year_det = movv_det['release_date']
    mov_time_det = movv_det['runtime']
    mov_overview_det = movv_det['overview']
    mov_trail = movv_det['videos']['results']
    mov_trail2 = mov_trail[0]
    mov_trail3 = mov_trail2['key']
    full_vid_path = 'https://vimeo.com/'+mov_trail3
    genres_det = []
    for i in movv_det['genres']:
        genres_det.append(i['name'])
    return full_pospath_url, full_backpath_url, mov_year_det, mov_time_det, mov_overview_det, genres_det, full_vid_path, cast_pic, cast_name

# FETCH ONLY MOVIE DETAILS
def fetch_poster(movie_id):
    apip = "https://api.themoviedb.org/3/movie/{}?api_key=99ffc5d2819f29106760b616189e633a".format(
        movie_id)
    data = requests.get(apip)
    data = data.json()
    poster_path = data['poster_path']
    poster_link = "https://image.tmdb.org/t/p/w500" + str(poster_path)
    mov_year = data['release_date']
    mov_time = data['runtime']
    mov_vote = data['vote_average']
    mov_name = data['original_title']
    mov_overview = data['overview']
    return poster_link, mov_year, mov_time, mov_vote, mov_name , mov_overview

# CONTENT BASED RECOMMENDATION FUNCTION
def content_based_rec(searched_movie):
    # find the searched movie index
    searched_movie_index = indices[searched_movie]
    searched_movie_id = mov_and_id['id'].iloc[searched_movie_index]

    # find the similarity scores
    similarity_score_searched_movie = similarities[searched_movie_index]

    model_scores = list(similarity_score_searched_movie)
    model_scores = list(enumerate(model_scores))

    # sort them in decreasing order
    model_scores = sorted(model_scores, key=lambda x: x[1], reverse=True)
    recommended_movie_indices = [index[0] for index in model_scores[1:13]]
    content_based_recomm_movies = [[], [], [], [], [], []]

    full_pospath_url, full_backpath_url, mov_year_det, mov_time_det, mov_overview_det, genres_det, full_vid_path, cast_pic, cast_name = movie_det(
        searched_movie_id)

    for i in recommended_movie_indices:
        idd = mov_and_id['id'].iloc[i]
        # print(idd)

        pic, date, dur, rating, nameee , overvie = fetch_poster(idd)
        content_based_recomm_movies[0].append(nameee)
        content_based_recomm_movies[1].append(pic)
        content_based_recomm_movies[2].append(dur)
        content_based_recomm_movies[3].append(date)
        content_based_recomm_movies[4].append(rating)

    return content_based_recomm_movies, full_pospath_url, full_backpath_url, mov_year_det, mov_time_det, mov_overview_det, genres_det, full_vid_path, cast_pic, cast_name

def main_func(movie_name, rating):
    similar_ratings = corrMatrix[movie_name]*(rating-2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings

def item_item(dyn_rating):
    similar_movies = pd.DataFrame()
    for i in dyn_rating:
        for apir1, apir2 in i.items():
            n = int(apir2)
            similar_movies = similar_movies.append(
                main_func(apir1, n), ignore_index=True)
    val = similar_movies.sum().sort_values(ascending=False).head(20)
    item_item_based_rec_movies = [[], [], [], [], [], []]
    for i in val.index:
        print(i)
        movie_lens_id = movieLens.loc[movieLens['title'] == i, 'movieId']
        movie_lens_id = movie_lens_id.iloc[0]

        if movie_lens_id not in links['movieId'].values:
            continue
        main_id = links.loc[links['movieId'] == movie_lens_id, 'tmdbId']
        main_id = int(main_id.iloc[0])
        pic, date, dur, rating, name, overvie = fetch_poster(main_id)
        item_item_based_rec_movies[0].append(name)
        item_item_based_rec_movies[1].append(pic)
        item_item_based_rec_movies[2].append(dur)
        item_item_based_rec_movies[3].append(date)
        item_item_based_rec_movies[4].append(rating)
        item_item_based_rec_movies[5].append(overvie)

    return item_item_based_rec_movies

def KNN_based(searched_movie):
    # GET TMDB ID OF SEARCHED MOVIE
    names = []
    arr_KNN = [[], [], [], [], []]
    searched_movie_index = indices[searched_movie]
    searched_movie_tmdb_id = mov_and_id['id'].iloc[searched_movie_index]

    # LENS ID
    if searched_movie_tmdb_id in links['tmdbId'].values:
        searched_movie_lens_id = links.loc[links['tmdbId']
                                           == searched_movie_tmdb_id, 'movieId']
        searched_movie_lens_id = searched_movie_lens_id.iloc[0]
    else:
        return arr_KNN ,  names

    # LENS NAME
    if searched_movie_lens_id in KNN_data['movieId'].values:
        searched_movie_lens_name = KNN_data.loc[KNN_data['movieId']
                                                == searched_movie_lens_id, 'title']
        searched_movie_lens_name = searched_movie_lens_name.iloc[0]
    else:
        return arr_KNN , names

    if searched_movie_lens_name in KNN_data['title'].values:
        distances, ids = ML.kneighbors(
            p_t.loc[searched_movie_lens_name, :].values.reshape(1, -1), n_neighbors=9)
    else:
        return arr_KNN , names

    # GETTING LENS MOVIES NAME FROM INDEXES
    names = p_t.iloc[ids.flatten()].index

    for i in names:
        if i == searched_movie_lens_name:
            continue
        # GETTING MOVIE LENS ID FROM LENS MOVIE NAME
        
        rec_mov_lens_id = KNN_data.loc[KNN_data['title'] == i, 'movieId']
        rec_mov_lens_id = rec_mov_lens_id.iloc[0]
        
        
        # GETTING MOVIE TMDB ID FROM MOVIE LENS ID
        if rec_mov_lens_id in links['movieId'].values:
            rec_mov_tmdb_id = links.loc[links['movieId']== rec_mov_lens_id, 'tmdbId']
            rec_mov_tmdb_id = rec_mov_tmdb_id.iloc[0]
        else:
            continue
        
        
        if rec_mov_tmdb_id in data['id'].values:
            pic, date, dur, rating, nameee, overvie = fetch_poster(rec_mov_tmdb_id)
        else:
            continue
        arr_KNN[0].append(pic)
        arr_KNN[1].append(nameee)
        arr_KNN[2].append(dur)
        arr_KNN[3].append(date)
        arr_KNN[4].append(rating)

    return arr_KNN , names


