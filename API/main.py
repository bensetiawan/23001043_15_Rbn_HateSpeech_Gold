import pandas as pd
import re
import sqlite3

from flask import Flask, request, jsonify
from flasgger import Swagger,LazyJSONEncoder
from flasgger import swag_from


from flask import request
app = Flask(__name__)

#db_connection
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect('cleansing.sqlite')
    except sqlite3.error as e:
        print(e)
    return conn

app.json_encoder = LazyJSONEncoder

#swagger template
swagger_template = dict(
info = {
    'title': 'API Documentation',
    'version': '2.0.0',
    'description': 'Dokumentasi API untuk Text dan Tweet Cleansing'
    }
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,config=swagger_config)

connection1 = db_connection()
#run_query1 = connection.cursor()

# read file abusive 
abusive_df = pd.read_csv('dataset/abusive.csv')
# store to database
abusive_df.to_sql("abusive", connection1, if_exists='append', index=False)
# get data abusive from database
temp_abusive_df = pd.read_sql_query("SELECT ABUSIVE FROM abusive",connection1)

# read file kamusalay
kamusalay_df = pd.read_csv('dataset/new_kamusalay.csv', names = ['ALAY', 'TIDAK_ALAY'], encoding = 'latin1')
# store to database
kamusalay_df.to_sql("replace_alay",  connection1, if_exists='append', index=False)
# Get data kamusalay from database
temp_kamusalay_df = pd.read_sql_query("SELECT ALAY,TIDAK_ALAY FROM replace_alay", connection1)

#Change Dataframe to Dictionary
dict_alay = {
    'ALAY':[],
    'TIDAK_ALAY':[]
}
for i in temp_kamusalay_df.itertuples():
  dict_alay['ALAY'].append(i.ALAY)
  dict_alay['TIDAK_ALAY'].append(i.TIDAK_ALAY)


# 1. remove USER,RT,URL
def remove_user_rt_url (str):
    string = re.sub(r'USER|\bRT\b|URL',' ',str)
    return string

#2 buat lower case
def lower_case (str):
    string = str.lower()
    return string

#3 remove /n
def remove_n (str):
    string =  re.sub(r'\\n',' ',str)
    return string

#4 remove emoji
def remove_emo2 (str):
    pattern = re.compile(r'[\\x]+[a-z0-9]{2}')
    string = re.sub(pattern,'',str)
    return string

#5 Remove Link
# remove link (http|https)
def remove_link (str):
    pattern = re.compile(r'www\S+|http\S+')
    string =  re.sub(pattern,' ',str)
    return string

#6 Hapus sisa karakter
# hapus special character dan pertahankan angka dan number
def remove_character(str):
    string = re.sub(r'[^a-zA-Z0-9 ]+',' ',str)
    return string

#7 remove Abusive
def remove_abusive (str):
    for x in temp_abusive_df.itertuples():
        temp = x.ABUSIVE
        if ''.join(temp) in str:
            str = re.sub (r'\w*({})\w*'.format(temp),' ',str)
    return str

#8 repalce alay
def replace_alay(str):
    for i in range(0,len(temp_kamusalay_df)-1): 
        alay = dict_alay['ALAY'][i]
        if (' ' + alay + ' ') in (' ' + str + ' '):
            replace = dict_alay['TIDAK_ALAY'][i]
            str = re.sub(r'\b{}\b'.format(alay),replace,str)
    return str
    # for i in temp_kamusalay_df.itertuples():
    #     alay = i.ALAY
    #     if (' ' + alay + ' ') in (' ' + str + ' '):
    #         replace = i.TIDAK_ALAY
    #         str = re.sub(r'\b{}\b'.format(alay),replace,str)
    # return str

#9 remove extra space
def remove_extra_space (str):
    str = re.sub('  +', ' ', str)
    str = str.strip()
    return str

#10 remove alay_abusive
def alay_abusive2 (str):
    str = replace_alay(str)
    str = remove_extra_space (str)
    str = remove_abusive(str)
    str = remove_extra_space (str)
    return str

def tweet_cleansing(str):
    str = remove_user_rt_url (str)
    str = lower_case (str)
    str = remove_n (str)
    str = remove_emo2 (str)
    str = remove_link (str)
    str = remove_character(str)
    str = remove_extra_space (str)
    str = alay_abusive2 (str)
    return str

@app.route('/', methods=['GET'])
@swag_from("../API/docs/ruben_get.yml", methods=['GET'])
def hello_world():
    json_response = {
        'Name': "Ruben Setiawan",
        'Tugas': "API for Cleansing Input Text and File Tweet",
        'Github': "https://github.com/bensetiawan",
        'Challange': "GOLD - CHALLANGE"
    }
    response_data = jsonify(json_response)
    return response_data

#Route Text Cleansing
@app.route('/text_cleansing', methods=['GET','POST'])
@swag_from('../API/docs/text_post.yml', methods=['POST'])
@swag_from('../API/docs/text_get.yml', methods=['GET'])
def text_processing():
    conn = db_connection()
    run_query = conn.cursor()
    if request.method ==  'GET':
        run_query = conn.execute("SELECT * FROM text_cleansing")
        text_cleansing  =  [
            dict(Id=row[0], Text=row[1],Text_After_Cleansing=row[2])
            for row in run_query.fetchall()
        ]
        if text_cleansing is not None:
            return jsonify(text_cleansing)
    
    elif request.method  == 'POST':
        text = request.form.get('text')
        temp =  text
        text_clean  =  tweet_cleansing(temp)

        query  =  """INSERT INTO text_cleansing (input_text,text_cleansing)
                    VALUES (?,?)"""
        run_query = conn.execute(query,(temp,text_clean))
        conn.commit()
        json_response = {
            'Description':'Teks Cleansing',
            'Text':temp,
            'Text_After_Cleansing' : text_clean
        }
        response_data  =  jsonify(json_response)
        return response_data

#Route File Tweet Cleansing
@app.route('/tweet_file', methods = ['POST'])
@swag_from('../API/docs/tweet_post.yml', methods=['POST'])
def  tweet_file_cleansing():
    file = request.files.getlist('file')[0]

    tweet_df = pd.read_csv(file, encoding = 'windows-1250')

    tweet_df.drop_duplicates()

    Tweet_Cleansing = [
        dict(Tweet = tweet_df['Tweet'].loc[i], Tweet_Cleansing = tweet_cleansing(tweet_df['Tweet'].loc[i]))
        for i in tweet_df['Tweet'].index.values
    ]
    
    if Tweet_Cleansing is not None:
        return jsonify(Tweet_Cleansing)
      
if __name__ == "__main__":
    app.run(debug=True)