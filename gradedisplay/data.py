def sortData(data):
    
    assignments = []
    
    data.pop(0)

    # We iterate through the amount of periods that the user has
    for col in data:
        if len(col) == 2: #this data holds the the categories and the assignments
            for assignment in col[1]:
                if assignment:
                    assignments.append(assignment)

    return assignments