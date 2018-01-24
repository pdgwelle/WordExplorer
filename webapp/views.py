import pandas as pd
import psycopg2

from flask import request
from flask import render_template

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

import database_scripts as db
from webapp import app

@app.route('/')
@app.route('/', methods=['POST'])
def index():
    if request.method != "POST":
        return render_template("index.html")
    
    else:
        if request.form['mode'] == 'first_query':
            query = request.form['query']
            tone = request.form['tone']
            objectivity = request.form['objectivity']
            complexity = request.form['complexity']
            source = request.form['source']
            passage_list = db.retrieve_examples(query, source, 
              ranks=[int(tone), -1*int(objectivity), -1*int(complexity)]) # actual terms are subjectivity and readability, so flip
            return render_template("index.html", passage_list=passage_list, word=query, source=source)
        
        elif request.form['mode'] == 'get_similar':
            word = request.form['word']
            embedding = request.form['embedding']
            source = request.form['source']
            passage_list = db.get_similar_passages(word, embedding, source)
            return render_template("index.html", passage_list=passage_list, word=word, source=source)        

@app.route('/test')
@app.route('/test', methods=['POST'])
def test():
    if request.method == "POST":
      text = request.form['text']
      return render_template("test_submit.html", data=text)
    else:
      return render_template("test_submit.html")

@app.route('/db')
def birth_page():
    sql_query = """                                                             
                SELECT * FROM birth_data_table WHERE delivery_method='Cesarean'\
;                                                                               
                """
    query_results = pd.read_sql_query(sql_query,con)
    births = ""
    print query_results[:10]
    for i in range(0,10):
        births += query_results.iloc[i]['birth_month']
        births += "<br>"
    return births

@app.route('/db_fancy')
def cesareans_page_fancy():
    sql_query = """
               SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean';
                """
    query_results=pd.read_sql_query(sql_query,con)
    births = []
    for i in range(0,query_results.shape[0]):
        births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
    return render_template('cesareans.html',births=births)

@app.route('/input')
def cesareans_input():
    return render_template("input.html")

@app.route('/output')
def cesareans_output():
  #pull 'birth_month' from input field and store it
  patient = request.args.get('birth_month')
    #just select the Cesareans  from the birth dtabase for the month that the user inputs
  query = "SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean' AND birth_month='%s'" % patient
  print query
  query_results=pd.read_sql_query(query,con)
  print query_results
  births = []
  for i in range(0,query_results.shape[0]):
      births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
      the_result = ModelIt(patient,births)
  return render_template("output.html", births = births, the_result = the_result)

  return render_template("output.html", births = births, the_result = the_result)

