from datetime import datetime
from gradedisplay.models import Assignment, Period
def getDBAssignments(data, databaseID):
    
    databaseAssignments = []
    periodDBI = None

    # We iterate through the amount of periods that the user has
    for col in data:
        if len(col) == 7:
            #Its time to set the class.        the user id for the class is given.
            periodDBI = Period.query.filter_by(userDBI=databaseID, name=col[0]).first().id
        if len(col) == 2: #this data holds the the categories and the assignments
            for a in col[1]:
                if a:
                    done = bool(a['Missing']=='0')
                    dba = Assignment(name=a['Description'], dueDate=datetime.strptime(a['DueDate'], "%Y-%m-%d %H:%M:%S.%f"),
                                    completed=done, missing = a['Missing']=='1', userDBI=databaseID, periodDBI=periodDBI);
                    if a['Missing']=='1': #if that bad boy is missing you better slap him in the beginning.
                        databaseAssignments.insert(0, dba)
                    else: 
                        databaseAssignments.append(dba)
    return databaseAssignments

def getDBPeriods(data, databaseID):

    databasePeriods = []
    data.pop(0)

    for col in data:
        if len(col) == 7:
            periodName = col[0]
            teacherLN = col[3].split(",")[0]
            dbc = Period(name=col[0], teacher=teacherLN, userDBI=databaseID)
            databasePeriods.append(dbc)

    return databasePeriods