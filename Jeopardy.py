"""
 Created on Oct 13, 2019
 @author: mitos
 """
import requests
import PySimpleGUI as sg
import datetime as DT

default_num_entries = 15


"""
Helper function used to pull a random set of clues for the user to search from
Output:
        clues: List of questions for the user to search from
"""
def getClues():
    clues = []
    for i in range(0, default_num_entries):
        clue = requests.get('http://jservice.io/api/random')
        clues.append(clue.json()[0])
    return clues


"""
Returns the questions that meet the user's search criteria 
such as the category, difficulty.
Inputs:
    category: category of question user specified
    difficulty: difficulty of the question in terms of an int 0-1000
    category_ids = dictionary of category names as keys with their values being their category ids. Used to print 
                   the category of each question
Output:
    Array of questions that fit the user's criteria
"""
def search_difficulty_and_category(category, difficulty, category_ids):
    #Define two booleans indicating when the user inputted criteria.
    #If the value inputted is not 'Any', the user inputted a value
    search_category = category != 'Any'
    search_difficulty = difficulty != 'Any'
    questions = []

    #If a difficulty is specified, query the database and return questions of that difficulty value
    if search_difficulty:
        for key,query_id in category_ids.items():
            query = requests.get('http://jservice.io/api/category?id=' + str(query_id)).json()
            for entry in query["clues"]:
                if entry['value'] == int(difficulty):
                    entry['category'] = key
                    #If the user also entered a category, further define search by adding question
                    #only if it matches the difficulty and category entered
                    if search_category:
                        if category == key:
                            questions.append(entry)
                    else:
                        questions.append(entry)
        printResults(questions)
    #If only a category is specified, query the API and return questions of that category type
    elif search_category:
        category_id = category_ids[category]
        questions = requests.get('http://jservice.io/api/category?id=' + str(category_id)).json()
        printResults(questions["clues"], category)

"""
Returns the questions that meet the user's date criteria
Inputs:
    date: Array consisting of the date the user entered and booleans indicating
          whether the user wants to search by month, day, or week
Output:
    Array of questions that fit the user's criteria
"""
def search_date(date):
    #Replace the year stored in the DateTime object with the year entered by the user
    date_criteria = date[0].replace(year=int(date[4]))
    #Return the query depending on if the user selected the day, week, or month
    #Day
    if date[3] is True:
        min_date = convertDateFormat(date_criteria)
        max_date = convertDateFormat(date_criteria)
    #Week
    if date[2] is True:
        weekday = date_criteria.isoweekday()
        min_date = date_criteria - DT.timedelta(days=weekday)
        max_date = date_criteria + DT.timedelta(days=(6-weekday))

    #Month
    if date[1] is True:
        #Search from the beginning of the current month to the first of the next
        month = date_criteria.month
        next_month = month+1
        if next_month > 12:
            next_month = 1
        min_date = date_criteria.replace(day = 1)
        max_date = date_criteria.replace(day = 1, month = next_month)
    min_date = convertDateFormat(min_date)
    max_date = convertDateFormat(max_date)
    query = requests.get('http://jservice.io/api/clues?min_date='+ min_date+ '+&max_date='+max_date).json()
    printResults(query, 'Category')

"""
Helper function used to splice datetime objects into Year-Month-Day form.
Input:
    date: Datetime object
Output:
    string describing the date in Year-Month_Day form 
"""
def convertDateFormat(date):
    return str(date)[0:10]

"""
Function used to print the questions and their details that meet 
the user's criteria. Prints the category, question, answer, 
difficulty, and air date for every question.
Inputs:
    questions: Array of questions that will be printed
    category_provided = Category string utilized when the question array does not
                        specify a category 
"""
def printResults(questions, category_provided = None):
    for val in questions:
        if category_provided is None:
            print("Category: " + val['category'])
        print("Question: " + val['question'])
        print("Answer: " + val['answer'])
        print("Difficulty: " + str(val['value']))
        print("Air Date: " + val['airdate'][0:10])
        print('-------------------------------------------------------')

"""
Function that returns a dictionary of category names (strings) assigned to
their respective category ids 
input:
    data: List of question entries that categories will be pulled from
Output:
    final: A dictionary consisting of category names (strings) assigned to
           their respective category ids 
"""
def get_Categories(data):
    final = {}
    for question in data:
        final[question['category']['title']] = question['category_id']
    return final

def main():
    #Query the API for clues
    database = getClues()
    #Retrieve the ids of the categories from the clues
    category_ids = get_Categories(database)
    #Define a list titled categories to be displayed for the user to choose from
    #in the program. Add 'Any' to the front to allow the user to search for questions
    #of Any category
    categories = list(category_ids.keys())
    categories.insert(0,'Any')
    tab1_layout = [sg.T("Difficulty"),
                   sg.Listbox(values=("Any", "100", "200", "300", "400", "500", "600", "700", "800", "900", "1000"),
                              size=(10, 3)), sg.T("Category"), sg.Listbox(values=categories, size=(20, 3))],
    tab2_layout = [sg.T("Date"), sg.CalendarButton("Select date"), sg.T("Enter a year:"),
                   sg.InputText("2014", size=(12, 1))], [sg.Radio('Month', 'loss', size=(12, 1)),
                                                         sg.Radio('Week', 'loss', size=(12, 1)),
                                                         sg.Radio('Day', 'loss', default=True, size=(12, 1))]
    layout = [[sg.TabGroup(
        [[sg.Tab('Search by difficulty and category', tab1_layout), sg.Tab('Search by date', tab2_layout)]],
    )], [sg.Output(size=(50, 30), key='output')], [sg.Button('Search Difficulty or Category'),sg.Button('Search Date')]]
    window = sg.Window('Jeopardy Search Engine', layout)
    while True:
        event, values = window.Read()
        #Set default values for category and difficulty. This allows the search difficulty and category
        #function know what criteria to search under depending on which criteria has a non default value
        category = 'Any'
        difficulty = 'Any'
        #Place user criteria variables in try/except clause to allow
        #exit of program without error
        try:
            if len(values[1]) > 0:
                category = values[1][0]
            if len(values[0]) > 0:
                difficulty = values[0][0]
            #Place user specified date, and booleans defining if the user wants to search by
            #day, month, or week in a list
            date = [values['Select date'], values[3],values[4],values[5],values[2]]
            if event == 'Search Date':
                search_date(date)
            elif event == 'Search Difficulty or Category':
                search_difficulty_and_category(category, difficulty, category_ids)
        except:
            pass
        if event is None or event == 'Exit':
            break
    window.Close()


if __name__ == '__main__':
    main()
