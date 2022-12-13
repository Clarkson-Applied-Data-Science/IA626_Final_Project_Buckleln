from bs4 import BeautifulSoup
import requests, pymysql, mysecrets, csv
import pandas as pd

#SQL table is truncated so it can be repopulated
conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)

cur = conn.cursor(pymysql.cursors.DictCursor)

cur.execute('truncate table Roster')

conn.commit
#web scraping for the player positions on teams depth charts
#Website that data is being scraped from
url = 'https://www.dailyfaceoff.com/teams/'
#needed to make requests to the website
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.3'}
r = requests.get(url, headers=headers,)
#load the home page into BS
soup = BeautifulSoup(r.text, 'html.parser')
#create dataframe to store the information
roster = pd.DataFrame(columns=['Player_Name','Position','Team'])
#iterate through the links for each team to scrape the current rosters
for a in soup.find_all('a', class_= 'team-detail-link'):
    team = a.text
    link_end = a.get("href")
    team_link = url + link_end + '/'
    link_response = requests.get(team_link, headers=headers, allow_redirects=False)
    link_soup = BeautifulSoup(link_response.text, "html.parser")
    n=0
    for td in link_soup.find_all('td'):
        if td.get('id') is not None:
            #n is capped at 18 becuase after 18 players they begin to repeat for special team rosters (powerplay and penalty kill)
            if n<18:
                position = td.get('id')
                spans = td.find("span", class_="player-name")
                playername = spans.text.replace(" ", "-")
                roster.loc[n] = [playername, position, team]
                n+=1
    #after each team has their roster scraped, the data is snet ot a csv
    roster.to_csv('roster.csv', index=False)
    conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)

    cur = conn.cursor(pymysql.cursors.DictCursor)
    conn.commit
    #the CSV is then uploaded into the SQL database
    fn = 'roster.csv'
    f = open(fn, 'r')
    reader = csv.reader(f)
    next(reader)
    for row in reader:
    # Use the `execute()` method to execute an `INSERT` statement for each row
        cur.execute('''
            INSERT INTO Roster (Player, Postion, Team)
            VALUES (%s, %s, %s)
        ''', (row[0], row[1], row[2]))
conn.close

#create functions for tranfsorming data to f0r desired format
def transform1(x):
    return x.replace(" ", "-")
def transform2(x):
    return str(x)
def transform3(x):
    return float(x)

#load in the data for the previous three years into a pandas dataframe
df = pd.read_csv('Player Season Totals - Natural Stat Trick (1).csv')
#select only the columns we are going to use
df2 = pd.DataFrame(df, columns=['Player','Team','GP','Goals','Total Assists','Hits','Shots','SH%','TOI'])
#apply transromations
df2['Player'] = df2['Player'].apply(transform1)
df2['Player'] = df2['Player'].apply(transform2)
#convert the data from total counts to per game rates
dfapg = df2.assign(AperG=round(df2['Total Assists'] / df2['GP'],3))
dfgpg = dfapg.assign(GperG=round(df2['Goals'] / df2['GP'],3))
dfhpg = dfgpg.assign(HperG=round(df2['Hits'] / df2['GP'],3))
dfspg = dfhpg.assign(SperG=round(df2['Shots'] / df2['GP'],3))
dfshper = dfspg.assign(SHper=round(df2['Goals'] / df2['Shots'],3))
CurrentStats1 = dfshper.assign(TOIperG=round(df2['TOI'] / df2['GP'],3))
#create new data frame with only per game rates
CurrentStats = pd.DataFrame(CurrentStats1, columns=('Player','GP','AperG','GperG','HperG','SperG','SHper','TOIperG'))
#this is to prevent an error from occuring, not sure why it was happening
CurrentStats.drop(CurrentStats[CurrentStats['SHper'] > 100].index, inplace=True)
CurrentStats = CurrentStats.drop_duplicates(subset='Player', keep='first')
#write a CSV for this dataframe so it can be inserted into the SQL database
CurrentStats.to_csv('CurrentStats.csv', index=False)


#establish connection to the SQL database
conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)

cur = conn.cursor(pymysql.cursors.DictCursor)
#make sure the table is empty
cur.execute('truncate table Current_Year')
conn.commit
#read in the csv file we just created
fn = 'CurrentStats.csv'
f = open(fn, 'r')
reader = csv.reader(f)
#go row by row and insert the data into a database
for row in reader:
    cur.execute('''
        INSERT INTO Current_Year (Player, GP, AperG, GperG, HperG, SperG, SHper, TOIperG)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

conn.close
#Current data has been entered into the database adn all the tabels have been created