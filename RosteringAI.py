from ortools.sat.python import cp_model
from datetime import datetime,timedelta

last_month_roster = {'Sunil':{'Deployment':2,'Weekend':1},'Bhagya':{'Deployment':4,'Weekend':2},'Naga':{'Deployment':1,'Weekend':1},'Vijay':{'Deployment':3,'Weekend':1},'Kunal':{'Deployment':0,'Weekend':1},'Lokesh':{'Deployment':0,'Weekend':1},'Pam':{'Deployment':0,'Weekend':2},'Ankit':{'Deployment':0,'Weekend':2}}

def generate_shift_roster(last_month_roster):
    #Define members and shifts
    members = ['Sunil','Bhagya','Naga','Vijay','Kunal','Lokesh','Pam','Ankit','Abhijeet']
    shifts = ['First','General','Second','Deployment','Weekend','Weekoff']

    # Define the start and end dates of April 2024
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 4, 30)

    first_monday_weekoff = 'Sunil'

    dates_of_april_2024 = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    days_of_week = {}

    # Iterate through the dates and organize them into weeks
    for date in dates_of_april_2024:
        week_number = date.isocalendar()[1]
        day_of_week = date.strftime("%a")
    
        if week_number not in days_of_week:
            days_of_week[week_number] = []
    
        days_of_week[week_number].append(day_of_week)

    # Print the dictionary
    for week, days in days_of_week.items():
        print(f"{week}: {days}")

    #Create model
    model = cp_model.CpModel()

    #Define decision variables
    shift_assignments = {}

    # Iterate through each week, day, shift, and member to assign constraints
    for week, days in days_of_week.items():
        for day in days:
            for shift in shifts:
                for member in members:
                    var_name = f'{day}_{week}_{shift}_{member}'  # Concatenate the week number to the variable name
                    shift_assignments[(day, week, shift, member)] = model.NewBoolVar(var_name)

    #Constraints

    #A member atmost one shift
    for member in members:
        for week, days in days_of_week.items():
                for day in days:
                    model.add_exactly_one(shift_assignments[(day,week,shift,member)] for shift in shifts)

    for member in members:
        # Iterate through the week_to_days_map dictionary
        for index, (week, days) in enumerate(days_of_week.items()):
        # Check if there is a next week
            model.Add(sum(shift_assignments[(day, week, 'Weekend', member)] for day in days) <= 1)
            model.Add(sum(shift_assignments[(day, week, 'Deployment', member)] for day in days) <= 1)
            if index + 1 < len(days_of_week):
                current_week = list(days_of_week.keys())[index]
                for day_idx in range(len(days)):  # Loop through all days except the last one
                    current_day = days[day_idx]
                    if index == 0 and current_day == 'Mon':
                        model.AddBoolOr(shift_assignments[(current_day,week,'Weekoff',first_monday_weekoff)])
                    if current_day in ['Mon', 'Tue', 'Thu']:  # Only apply constraint for Mon, Tue, and Thu
            # If a member is assigned Deployment on Mon, Tue, or Thu, they must have the Second shift the next day
                        if day_idx < len(days)-1:
                            model.AddImplication(shift_assignments[(current_day,current_week,'Deployment', member)], shift_assignments[(days[day_idx+1],current_week, 'Second', member)])
                    if current_day == 'Sat':
                        if day_idx < len(days)-1:
                            model.AddBoolOr(shift_assignments[(current_day,current_week,'Weekend', member)].Not(),shift_assignments[(days[day_idx+1],current_week,'Weekend', member)].Not())
                        if day_idx <= len(days) - 2 and index < len(list(days_of_week.keys())) - 1:
                            model.AddImplication(shift_assignments[(current_day,current_week, 'Weekend', member)], shift_assignments[('Mon',current_week+1, 'Weekoff', member)])
                    if current_day == 'Sun':
                        if day_idx > 0:
                            model.AddBoolOr(shift_assignments[(current_day,current_week, 'Weekend', member)].Not(),shift_assignments[('Sat',current_week, 'Weekend', member)].Not())
                        if day_idx > 2:
                            model.AddImplication(shift_assignments[(current_day,current_week, 'Weekend', member)], shift_assignments[('Fri',current_week, 'Weekoff', member)])

                    if current_day in ['Sat','Sun'] and index < len(days_of_week) - 1:
                        if 'Sat' in days_of_week[current_week+1]:
                            model.AddBoolOr(shift_assignments[(current_day,current_week,'Weekend', member)].Not(),shift_assignments[('Sat',current_week+1,'Weekend', member)].Not())
                        if 'Sun' in days_of_week[current_week+1]:
                            model.AddBoolOr(shift_assignments[(current_day,current_week,'Weekend', member)].Not(),shift_assignments[('Sun',current_week+1,'Weekend', member)].Not())
                    if current_day in ['Sat','Sun'] and index < len(days_of_week) - 2:
                        if 'Sat' in days_of_week[current_week+2]:
                            model.AddBoolOr(shift_assignments[(current_day,current_week,'Weekend', member)].Not(),shift_assignments[('Sat',current_week+2,'Weekend', member)].Not())
                        if 'Sun' in days_of_week[current_week+2]:
                            model.AddBoolOr(shift_assignments[(current_day,current_week,'Weekend', member)].Not(),shift_assignments[('Sun',current_week+2,'Weekend', member)].Not())
            # If a member is assigned the weekend shift on Sunday, they must have a weekoff on Friday
            

    #Members per shift
    for week, days in days_of_week.items():
            for day in days:
                for shift in shifts:
                    for member in ['Abhijeet','Pam','Bhagya']:
                        if shift != 'General' and shift != 'Weekoff' and day not in ['Sat','Sun']:
                            model.AddBoolOr(shift_assignments[(day,week,shift, member)].Not())
                    for member in ['Naga']:
                        if shift != 'General' and shift != 'First' and shift != 'Weekoff' and day not in ['Sat','Sun']:
                            model.AddBoolOr(shift_assignments[(day,week,shift, member)].Not())
                    for member in ['Ankit','Lokesh']:
                        if shift == 'First':
                            model.AddBoolOr(shift_assignments[(day,week,shift, member)].Not())
                    if day in ['Wed','Fri']:
                        model.Add(sum(shift_assignments[(day,week,'Second',member)] for member in members) == 1)
                        model.Add(sum(shift_assignments[(day,week,'Deployment',member)] for member in members) == 0)
                        model.Add(sum(shift_assignments[(day,week,'Weekend',member)] for member in members) == 0)
                        model.Add(sum(shift_assignments[(day,week,'First',member)] for member in members) == 1)
                    if day in ['Mon','Tue','Thu']:
                        model.Add(sum(shift_assignments[(day,week,'Deployment',member)] for member in members) == 1)
                        model.Add(sum(shift_assignments[(day,week,'Weekend',member)] for member in members) == 0)
                        model.Add(sum(shift_assignments[(day,week,'First',member)] for member in members) == 1)
                    if day in ['Tue','Wed','Thu']: 
                        model.Add(sum(shift_assignments[(day,week,'Weekoff',member)] for member in members) == 0)
                    if day in ['Mon','Fri']:
                        model.Add(sum(shift_assignments[(day,week,'Weekoff',member)] for member in members) == 1)
                    if day in ['Sat','Sun']:
                        model.AddBoolOr(shift_assignments[(day,week,'Weekend','Abhijeet')].Not())
                        if shift == 'Weekend':
                            model.Add(sum(shift_assignments[(day,week,'Weekend',member)] for member in members) == 1)
                        elif shift != 'Weekoff' and shift != 'Weekend':
                            model.Add(sum(shift_assignments[(day,week,shift,member)] for member in members) == 0)

    # Define target number of deployment shifts per month
    target_deployments_per_month = 3
    target_weekends_per_month = 2

    total_shifts = 0

    for member, shifts_data in last_month_roster.items():
        total_shifts = 0
        for shift, count in shifts_data.items():
            for week,days in days_of_week.items():
            # Sum the shift assignments for the specific days and week for the given member and shift
                total_shifts += sum(shift_assignments[(day, week, shift, member)] for day in days)
            # Calculate the difference from the target number of shifts
                if shift == 'Deployment':
                    difference = count - target_deployments_per_month
                if shift == 'Weekend':
                    difference = count - target_weekends_per_month
            # Add constraint: the difference should be balanced over time
            # If the difference is positive, compensate by reducing shifts this month
            # If the difference is negative, compensate by increasing shifts this month
            
            if shift == 'Deployment':
                print(member,shift,target_deployments_per_month - difference)
                model.Add(total_shifts <= target_deployments_per_month - difference)
            if shift == 'Weekend':
                print(member,shift,target_weekends_per_month - difference)
                if difference >= 0:
                    model.Add(total_shifts == 1)

    #Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    roster = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for week, days in days_of_week.items():
            for day_index, day in enumerate(days, start=1):
                day_number = (week - 14) * 7 + day_index
                date_str = f'{day_number}/{start_date.month}/{start_date.year}'
                for shift in shifts:
                    for member in members:
                        if solver.Value(shift_assignments[(day, week, shift, member)]) == 1:
                            roster.append((member,week,date_str,shift))
    else:
        print("No feasible solution found.")
 
    return roster
roster = generate_shift_roster(last_month_roster)

# Open a text file for writing
with open("C:/Users/Manikandan PV/roster.txt", "w") as file:
    # Iterate over each entry in roster
    for entry in roster:
        # Write the entry to the file
        file.write(str(entry) + "\n")

        
