import json,pymysql,mysecrets
import pandas as pd
from flask import Flask
from flask import request,redirect
conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)
app = Flask(__name__)

query1 = 'SELECT * FROM Current_Year WHERE `Player` = %s'
query2 = 'SELECT * FROM Three_Year_AVG WHERE `Player` = %s'
query3 = 'SELECT * FROM Roster WHERE `Player` = %s'

@app.route("/", methods=['GET','POST'])
def root():
    res = {} 
    res['code'] = 2
    res['msg'] = 'No endpoint specified'
    res['req'] = '/'
    return json.dumps(res,indent=4)
@app.route("/report", methods=['GET','POST'])
def report():
    res = {} 
    player =  request.args.get('player')
    goals =  float(request.args.get('goals'))
    assists =  float(request.args.get('assists'))
    hits =  float(request.args.get('hits'))
    shots =  float(request.args.get('shots'))
    with conn.cursor() as cursor:
        cursor.execute(query1, player)
    results = cursor.fetchall()
    dfcur = pd.DataFrame.from_records(results)
    with conn.cursor() as cursor:
        cursor.execute(query2, player)
    results2 = cursor.fetchall()
    dfpast = pd.DataFrame.from_records(results2)
    with conn.cursor() as cursor:
        cursor.execute(query3, player)
    results3 = cursor.fetchall()
    dfroster = pd.DataFrame.from_records(results3)
    cur_fppg = round((float(dfcur[2])*assists + float(dfcur[3])*goals + float(dfcur[4])*hits + float(dfcur[5])*shots),4)
    cur_shper = float(dfcur[6])*100
    past_fppg = round(float(dfpast[2])*assists + float(dfpast[3])*goals + float(dfpast[4])*hits + float(dfpast[5])*shots)
    past_shper = float(dfpast[6]*100)
    cur_toi = float(dfcur[7])
    past_toi = float(dfpast[7])
    position = str(dfroster[1][0])
    team = str(dfroster[2][0])
    res['Player Name'] = str(player)
    res['2019-2022 Fantasy Points Per Game'] = str(past_fppg)
    res['2022-2023 Fantasy Points Per Game'] = str(cur_fppg)
    res['Change In FPPG'] = str(round((cur_fppg/past_fppg)*100,4)) +'%'
    res['Change In Shooting Percentage'] = str(round((cur_shper/past_shper),4))
    res['Change In Ice Time'] = str(round((cur_toi/past_toi),4))
    res['Place In Depth Chart'] = str(position) 
    res['Current Team'] = str(team)
    return json.dumps(res, indent=4)
    
if __name__ == "__main__":
    app.run(host='127.0.0.1',debug=True)
