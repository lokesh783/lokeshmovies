#  SERVER

import pyrebase
import pandas as pd
import pickle
from flask import Flask, request, render_template
import fun

# --------------*---------------*----------------*--------------*-----------------*------------------

# PICKLE FILE IMPORTS
final_data = pickle.load(open('movies.pkl','rb'))

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# DATA FILE IMPORTS
links = pd.read_csv('Datasets/links.csv')                   # to get tmdb id from movie lens id and vice versa
movieLens = pd.read_csv('Datasets/movies.csv')              # for getting the datas in between such as name to id and vice versa
tmdb_movies = pd.read_csv('Datasets/tmdb_5000_credits.csv') # for getting the datas in between such as name to id and vice versa
suggest = list(tmdb_movies['title'].values)                 # Array sent at front end for auto suggestion
# --------------*---------------*----------------*--------------*-----------------*------------------ #

# FIREBASE DATA
firebaseConfig = {
    "apiKey": "AIzaSyBeDWkzuxpu6_dGvxl9YA3wA80JGmoxjms",
    "authDomain": "hopeful-expanse-319811.firebaseapp.com",
    "projectId": "hopeful-expanse-319811",
    "storageBucket": "hopeful-expanse-319811.appspot.com",
    "messagingSenderId": "307429013940",
    "appId": "1:307429013940:web:c878bf870c7ac0ad0a9ae1",
    "measurementId": "G-TEQZERL1JJ",
    "databaseURL": "https://hopeful-expanse-319811-default-rtdb.firebaseio.com"
}

# --------------*---------------*----------------*--------------*-----------------*------------------ #

# FIREBASE AUTH AND DATABASE INITIALIZATION 
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# INITIAL FUNCTIONS FOR TRENDING AND POPULAR
most_rated = fun.most_rated
most_popular = fun.most_popular
# --------------*---------------*----------------*--------------*-----------------*------------------ #

# APP INITIALIZATION
app = Flask(__name__)

# INITIAL REQUEST
@app.route("/")
def hello():
    return render_template("land.html" , suggest=suggest, most_rated = most_rated , most_popular = most_popular)

# DATABASE ADDING REQUEST
@app.route("/rating/<val>",methods=['POST'])
def add(val):
    if request.method == 'POST':
        movie_rating = request.form["rating"]
        user_unique_id = auth.current_user['localId']
        searched_movie_index = final_data[final_data['title'] == val].index[0]
        searched_movie_tmdb_id = final_data[final_data['title'] == val].movie_id[searched_movie_index]
        
        # checked if movie's tmdb id is present in links or not
        if searched_movie_tmdb_id in links['tmdbId'].values:
            movie_Lens_Id = links.loc[links['tmdbId'] == searched_movie_tmdb_id, 'movieId']
            movie_Lens_Id = movie_Lens_Id.iloc[0]
        else:
            return render_template("index.html", suggest=suggest , most_rated = most_rated , most_popular = most_popular)
        
        # checked if movie lens id is present in movielens data set or not
        if movie_Lens_Id not in movieLens['movieId'].values:
            return render_template("index.html", suggest=suggest, most_rated = most_rated , most_popular = most_popular)
        
        # conversion of name to movie lens name format (means with year ) spectre -> spectre (2015)
        search_mov_wy = movieLens.loc[movieLens['movieId'] == movie_Lens_Id, 'title']
        search_mov_wy = search_mov_wy.iloc[0]
        
        # PUSH NAME AND RATING TO DATABASE
        db.child(user_unique_id).push({search_mov_wy:movie_rating});
        return render_template("index.html", suggest=suggest, most_rated = most_rated , most_popular = most_popular)

# REGISTRATION REQUEST
@app.route("/register_done" , methods=['POST'])
def signup():
    email = request.form["email"]
    password = request.form["password"]
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return render_template("land.html",suggest=suggest, flag=1 ,most_rated = most_rated , most_popular = most_popular)
    except:
        return render_template("register.html",flag=2)
        
# REGISTRATION PAGE REDIRECTION
@app.route("/register")
def register():
    return render_template("register.html" ,flag=0)

# LOGIN PAGE REDIRECTION
@app.route("/login")
def login():
    return render_template('login.html')

# LOGIN REQUEST
@app.route("/index" , methods = ['GET','POST'])
def signin():
    
    # IF USER IS NOT SIGNED IN WE WILL RETURN THE LANDING PAGE
    # THIS WILL BE USED IN THE CASE WHEN USER MANUALLY TRY TO GET THE ROUTE INDEX
    if request.method =='GET':
        if auth.current_user==None:
            return render_template("land.html",suggest=suggest,reg_for_it=1, most_rated= most_rated , most_popular = most_popular)
        else:
            return render_template("index.html",suggest=suggest, most_rated = most_rated , most_popular = most_popular)
      
    email = request.form["email"]
    password = request.form["password"]
    
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return render_template("index.html" , suggest=suggest, most_rated = most_rated , most_popular = most_popular)
    except:
        # We are returning flag=0 because we will be using this to give pop up of not signed in at our Login Page
        return render_template("login.html",flag=0)

@app.route('/logout')
def logout():
    auth.current_user = None
    return render_template("land.html",suggest=suggest, most_rated = most_rated , most_popular = most_popular)

# CONTENT BASED RECOMMEND REQUEST
@app.route("/recommend" , methods = ['POST','GET'])
def rec():
    user = auth.current_user
    # IF USER TRY TO ENTER MANUALLY WITH GET REQUEST THEN WE WILL RETURN EITHER
    # LANDING PAGE OR INDEX PAGE BASED ON USER IS SIGNED IN OR NOT
    if request.method =='GET':
        if user == None:
            return render_template("land.html" ,suggest=suggest,  most_rated = most_rated , most_popular = most_popular)
        else:
            return render_template("index.html", suggest=suggest,  most_rated = most_rated , most_popular = most_popular) 
    
    # HTML -> .py
    if request.method== "POST":
        name = request.form["movie_name"]
        
        # When movie is not present in our dataset 
        if name not in tmdb_movies['title'].values:
            if user==None:
                return render_template("land.html",suggest=suggest,pop_up = 1,  most_rated = most_rated , most_popular = most_popular)
            else:
                return render_template("index.html", suggest=suggest,pop_up=1,  most_rated = most_rated , most_popular = most_popular)
        
        # When movie is present in dataset
        # GETTING CONTENT BASED RECOMMENDED MOVIE AND SEARCHED MOVIE DATA
        arr_cont , full_pospath_url,ap,mov_year_det,mov_time_det,mov_overview_det,genres_det,full_vid_path , cast_pic , cast_name = fun.content_based_rec(name)

        # GETTING KNN_BASED RECOMMENDED MOVIES DATA
        # IF GETTING DATA FROM API WILL NOT BE POSSIBLE WE WILL RETURN EMPTY ARRAYS
        # AND GIVE OUTPUT ON FRONT END ACCORDING TO THAT
        arr_KNN ,names = fun.KNN_based(name)
        
        size = len(cast_pic)
        arr_KNN_len = len(arr_KNN[0])
        name_len = len(names)
    #  .py -> HTML
    
    # WE ARE GIVING (n) AS A VARIABLE WHICH IS USED TO GIVE EITHER LOGOUT BUTTON OR
    # LOGIN AND REGISTER BUTTON BASED ON USER IS CURRENTLY SIGNED IN OR NOT
    if user==None:
        n="loggedout"
    else:
        n="loggedin"
    return render_template("recommend.html",name_len=name_len,names = names , suggest=suggest,n=n,arr_KNN_len=arr_KNN_len, size =size , arr_cont = arr_cont , pic = full_pospath_url, searched_movie = name , rel_year = mov_year_det , dur = mov_time_det , overview = mov_overview_det , genres = genres_det ,cast_pic = cast_pic , cast_name = cast_name ,arr_KNN = arr_KNN)

# COLLABORATIVE ITEM ITEM REQUEST
@app.route("/collab_rec")
def collab_rec():
    # GETTING USERS UNIQUE ID
    user_unique_id = auth.current_user['localId']
    
    # GETTING RATED MOVIES FROM DATABASE
    rated_mov = db.child(user_unique_id).get()
    
    # Here we have checked if user had rated any movie or not
    if rated_mov.val()==None:
        return render_template("index.html", suggest=suggest, no_rated_movie=1 ,most_rated = most_rated , most_popular = most_popular)
    
    rated_movies_array = rated_mov.val().values()
    rec_mov_a = fun.item_item(rated_movies_array)
    return render_template("collab_rec.html", suggest=suggest, itemArray = rec_mov_a)


if __name__ == "__main__":
    app.run(debug=True)
    