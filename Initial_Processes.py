import pymysql,csv,time,mysecrets
import pandas as pd


#establish connection to SQL database
conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)

cur = conn.cursor(pymysql.cursors.DictCursor)

#drop and then create the tables in the SQL database
cur.execute('DROP TABLE IF EXISTS Roster')

cur.execute("CREATE TABLE Roster (Player VARCHAR(40) NOT NULL PRIMARY KEY, Postion VARCHAR(3), Team VARCHAR(30))")

cur.execute('DROP TABLE IF EXISTS Current_Year')

cur.execute("CREATE TABLE Current_Year (Player VARCHAR(40) NOT NULL PRIMARY KEY, GP INT, AperG DECIMAL(3,2), GperG DECIMAL(3,2), HperG DECIMAL(3,2), SperG DECIMAL(3,2), SHper DECIMAL(3,2), TOIperG DECIMAL(5,3))")

cur.execute('DROP TABLE IF EXISTS Three_Year_AVG')

cur.execute("CREATE TABLE Three_Year_AVG (Player VARCHAR(40) NOT NULL PRIMARY KEY, GP INT, AperG DECIMAL(3,2), GperG DECIMAL(3,2), HperG DECIMAL(3,2), SperG DECIMAL(3,2), SHper DECIMAL(3,2), TOIperG DECIMAL(5,3))")

conn.commit

conn.close

#create functions for tranfsorming data to f0r desired format
def transform1(x):
    return x.replace(" ", "-")
def transform2(x):
    return str(x)
def transform3(x):
    return float(x)

#load in the data for the previous three years into a pandas dataframe using pandas read_html function
url = 'https://www.naturalstattrick.com/playerteams.php?fromseason=20192020&thruseason=20212022&stype=2&sit=all&score=all&stdoi=std&rate=n&team=ALL&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'


df = pd.read_html(url, header=0, index_col = 0, na_values=['-'])[0]
#select only the columns we are going to use
df2 = pd.DataFrame(df, columns=['Index','Player','Team','GP','Goals','Total Assists','Hits','Shots','SH%','TOI'])
df2['Player'] = df2['Player'].apply(transform1)
#convert the data from total counts to per game rates
dfapg = df2.assign(AperG=round(df2['Total Assists'] / df2['GP'],3))
dfgpg = dfapg.assign(GperG=round(df2['Goals'] / df2['GP'],3))
dfhpg = dfgpg.assign(HperG=round(df2['Hits'] / df2['GP'],3))
dfspg = dfhpg.assign(SperG=round(df2['Shots'] / df2['GP'],3))
dfshper = dfspg.assign(SHper=round(df2['Goals'] / df2['Shots'],3))
ThreeYrAVG = dfshper.assign(TOIperG=round(df2['TOI'] / df2['GP'],3))
#create new data frame with only per game rates
ThreeYearAverage = pd.DataFrame(ThreeYrAVG, columns=('Player','GP','AperG','GperG','HperG','SperG','SHper','TOIperG'))
#this is to prevent an error from occuring, not sure why it was happening
ThreeYearAverage.drop(ThreeYearAverage[ThreeYearAverage['SHper'] > 100].index, inplace=True)
ThreeYearAverage = ThreeYearAverage.drop_duplicates(subset='Player', keep='first')
#write a CSV for this dataframe so it can be inserted into the SQL database
ThreeYearAverage.to_csv('ThreeYearAverage.csv', index=False)

#establish connection to the SQL database
conn = pymysql.connect(host=mysecrets.host, port=3306, user=mysecrets.user,
                       passwd=mysecrets.passwd, db='buckleln', autocommit=True)

cur = conn.cursor(pymysql.cursors.DictCursor)
#make sure the table is empty
cur.execute('truncate table Three_Year_AVG')
conn.commit
#read in the csv file we just created
fn = 'ThreeYearAverage.csv'
f = open(fn, 'r')
reader = csv.reader(f)
#go row by row and insert the data into a database
for row in reader:
    cur.execute('''
        INSERT INTO Three_Year_AVG (Player, GP, AperG, GperG, HperG, SperG, SHper, TOIperG)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

conn.close
#previous 3 years data has been entered into the database adn all the tabels have been created