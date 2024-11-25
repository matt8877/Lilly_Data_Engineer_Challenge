import sqlite3
import csv
from tabulate import tabulate

'''
Open each csv file and add them to a table in new created database
 '''


def add_to_database(file,database_name,file_name):
    string_path = fr"C:\Users\Matth\OneDrive\Documents\GitHub\Lilly_Challenge\DataEngineer-Challenge-master\{file}"
     
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    with open(string_path, newline='',encoding='utf-8-sig') as file:  #iterates through each csv file


        read = csv.reader(file)
        headers = next(read)
        columns = ", ".join(f"{header} TEXT" for header in headers)
        column_names = ", ".join(f"{header}" for header in headers)

        if file_name == 'results':

            cursor.execute(f"CREATE TABLE IF NOT EXISTS {file_name} ({columns}, PRIMARY KEY (date, home_team, away_team));")
            '''
            Create the results table with the primary key being composite the date, home team and away team 
            '''

        else:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {file_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns},"+
                            "FOREIGN KEY (date,home_team,away_team) REFERENCES results(date, home_team, away_team));")   #foreign Keys created to allow communication between tables
        
        for row in read:
           
            placeholders =", ".join("?" for x in row)
            cursor.execute(f"INSERT OR REPLACE INTO {file_name} ({column_names}) VALUES ({placeholders});",row)
        conn.commit()
        conn.close()



csv_file_list  = [('results.csv','results'),('goalscorers.csv','goalscorers'),('shootouts.csv','shootouts')]

for file,file_name in csv_file_list:
    add_to_database(file,'football_database',file_name)

conn = sqlite3.connect('football_database')
cursor = conn.cursor()

'''
Extra
Multiple checks to see if data in tables is solid or in the right form
If not new quality issue column goes from 0 to 1
'''

cursor.execute("ALTER TABLE goalscorers ADD COLUMN quality_issue INTEGER DEFAULT 0;")
cursor.execute("ALTER TABLE results ADD COLUMN quality_issue INTEGER DEFAULT 0;")
cursor.execute("ALTER TABLE shootouts ADD COLUMN quality_issue INTEGER DEFAULT 0;")


cursor.execute('''UPDATE goalscorers SET quality_issue = 1 
               WHERE scorer IS NULL OR
                home_team IS NULL OR away_team IS NULL OR 
               minute < 0 OR minute > 120 
               OR date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
               OR date > DATE('now');''')


cursor.execute('''UPDATE results SET quality_issue = 1 
               WHERE 
                home_team IS NULL OR away_team IS NULL OR 
               home_score < 0 OR away_score < 0 OR
               tournament IS NULL OR city IS NULL OR country IS NULL
               OR neutral NOT IN (FALSE,TRUE) OR
                date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
               OR date > DATE('now');
              ''')


cursor.execute('''UPDATE shootouts SET quality_issue = 1 
               WHERE
                home_team IS NULL OR away_team IS NULL OR
               winner IS NULL or first_shooter IS NULL
               OR date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
               OR date > DATE('now');
               ''')





'''
Question 1

SQL request to retrieve scores for all games between 1900 and 2000
add up all all the scores into 1 total 
and then divide by the number of games played
'''

cursor.execute("SELECT home_score,away_score FROM results WHERE date >= 1900-01-01 AND date <= 2000-12-31") 

tuple_scores = cursor.fetchall()
tuple_scores = [(int(x[0]),int(x[1])) for x in tuple_scores]
total_goals  = sum(map(sum,tuple_scores))
average_goals = total_goals/len(tuple_scores)

print(f"Average number of goals per game 1900-2000: {average_goals}")




'''

Question2

SQL query that counts the number of times a country's name
appears in the winners column. it then orders them alphabetically
with the number of shootout wins along side

'''

cursor.execute(f"SELECT winner, COUNT(winner) AS count FROM shootouts GROUP BY winner ORDER BY winner")


'''
Question 3

Implemented when creating the table as you cannot ALTER TABLE
and add a foreign key to an already existing table

'''




'''
Question 4

Join results and shootouts table with composite key of home_team, away_team and date. 
Makes sure home_team has only scored 1 and away_team has onyl scored 1 
Then returns the winner from the shotout table
'''

cursor.execute('''SELECT results.home_score, results.away_score, shootouts.winner 
               FROM results
                INNER JOIN shootouts
                ON (results.date = shootouts.date AND results.home_team = shootouts.home_team AND results.away_team = shootouts.away_team) 
               WHERE results.home_score = '1' AND results.away_score = '1' ;''')



'''
Question 5

Query 1:
Firstly get list of footballers in tournament who have scored and how mnay goals 
they have scored in that tournament

Query 2:
Secondly get the total number of goals scored in each tournament

Function to return the top scorer from eahc tournament
Function to return the percentage fi the goals scored by the player in that tournament
'''

def top_scorer_for_tourn(number_of_goals_tourn):
    max_values = {}
    for tuple_goal in number_of_goals_tourn:
        identifier, _, value = tuple_goal
        if identifier not in max_values or value > max_values[identifier]:
            max_values[identifier] = value

    result = [tuple_goal for tuple_goal in number_of_goals_tourn if tuple_goal[2] == max_values[tuple_goal[0]]]
    return result


cursor.execute('''SELECT results.tournament, goalscorers.scorer, COUNT(*) AS number_of_goals
               FROM results
               INNER JOIN goalscorers
               ON (results.date = goalscorers.date AND results.home_team = goalscorers.home_team AND results.away_team = goalscorers.away_team)
               GROUP BY goalscorers.scorer, results.tournament ORDER BY results.tournament, number_of_goals DESC;
                ''')
number_of_goals_tourn = [(x[0].encode('utf-8'),x[1].encode('utf-8'),x[2]) for x in cursor.fetchall()] #have to encode the data due to accents in languages

cursor.execute('''SELECT tournament, MAX(number_of_goals) AS max_goals
               FROM ( SELECT results.tournament, goalscorers.scorer, COUNT(*) AS number_of_goals 
                    FROM goalscorers 
                    INNER JOIN results
                    ON (results.date = goalscorers.date AND results.home_team = goalscorers.home_team AND results.away_team = goalscorers.away_team)
                    GROUP BY tournament, scorer)
               AS TournamentGoals
               GROUP BY tournament;''')

max_goals_tourn = [(x[0].encode('utf-8'),x[1]) for x in cursor.fetchall()]
top_scorer = top_scorer_for_tourn(number_of_goals_tourn)


def percentage_goals(max_goals_tourn,number_of_goals_tourn):
    tourn_list = []
    for tourn,player in zip(max_goals_tourn,number_of_goals_tourn):
        tourn_list.append((tourn[0],(player[2]/tourn[1])*100,player[1]))

    return tourn_list

print(percentage_goals(max_goals_tourn,top_scorer))




