import csv
import glob
import math
import re
from datetime import timedelta
from itertools import zip_longest, chain
from pathlib import Path

club_folders = {"Input": ["WRC1", "WRC2", "WREC"], "Output": ["WRC", "WREC"]}
valid_clubs = {"WRC": ["WRC1", "WRC2"], "WREC": ["WREC"]}#, "WRC1": ["WRC1"]}
nominal_times = ["0:08:00", "0:16:00", "0:25:00", "0:35:00"]
car_penalty_times_overall = ["00:03:00", "00:05:00"]
car_penalty_times_ps = ["00:00:10", "00:00:30"]
points = [40,35,30,26,24,22,20,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]
power_stage_points = [5,4,3,2,1]
no_export_string = "\nNo results have been exported!"
initial_time = timedelta()

class Driver:
    def __init__(self, name, car, club, tier):
        self.name = name
        self.car = car
        self.platform = None
        self.club = club
        self.tier = tier
        self.completed_stages = []
        self.total_time = initial_time
        self.points = 0
        self.power_stage_points = 0
        self.total_points = 0
        self.used_wrong_car = None
        self.did_not_finish = False # For drivers who completed less than 6 stages in WRC1/2 or retired correctly
        self.did_not_retire = False # For drivers who did not retire correctly and are missing from the results

    def __eq__(self, other):
        return self.name == other.name

class Stage:
    def __init__(self, number, result, club):
        self.number = number
        self.result = result
        self.club = club
        self.fastest_time = initial_time
        self.slowest_time = initial_time

def challenge_yes_or_no(question="Continue?"):
    # Inspired by https://stackoverflow.com/a/3041990
    valid = {"y": True, "yes": True, "n": False, "no": False}

    while True:
        choice = input(f'{question} [y/n] ').lower()
        if choice in valid:
            print()
            return valid[choice]
        else:
            print("Please respond with y or n")

def convert_to_timedelta(time):
    stage_hours, stage_minutes, temp_stage_seconds = time.split(":")
    stage_seconds, stage_milliseconds = temp_stage_seconds.split(".") if "." in temp_stage_seconds else (temp_stage_seconds, "000000")
    return timedelta(hours=int(stage_hours), minutes=int(stage_minutes), seconds=int(stage_seconds), milliseconds=int(stage_milliseconds[:3]))

def sum_stage_times(total_time, stage_time):
    return total_time + stage_time

def get_gap_to_leader(leader_time, driver_time):
    return driver_time - leader_time

class Round:
    def __init__(self, club, number):
        self.club = club
        self.number = number
        self.drivers = {}
        self.duplicate_drivers = []
        self.stages = []
        self.overall = None
        self.multiclass_overall = []
        self.wrec_last_day = 0
        self.winner_time = initial_time

    def import_drivers(self):
        file = f'WRC Drivers/Drivers {self.number}.csv'
        while True:
            if Path(file).is_file():
                with open(file, newline='') as f:
                    for row in list(csv.reader(f)):
                        #EXAMPLE ROW:
                        #["Slokksi", "WRC1", "Master", "Volkswagen Polo 2017", "Round 9 - Croatia, Round 10 - Chile"]
                        if row[0] not in self.drivers:
                            drop_rounds = [x.split(" ")[1] for x in row[4].split(", ")]
                            if self.number[-1] in drop_rounds:
                                continue
                            else:
                                self.drivers[row[0]] = Driver(row[0], row[3], row[1], row[2])
                break
            else:
                if not challenge_yes_or_no(f'The file {file} does not exist. Make sure the list of drivers is in the correct location. Try again?'):
                    quit(no_export_string)

    def import_stages(self, files):
        wrc_players = []

        for club in files:
            for idx, file in enumerate(files[club]):

                temp_file = []
                with open(file, newline='') as f:
                    #EXAMPLE IN/OUT ROWS:
                    #['1', 'Slokksi', 'Volkswagen Polo 2017', '00:04:23.2610000', '00:00:00', '00:00:00', 'XBOX', '', '']            
                    #{"position": "1", "name": "Slokksi", "car": "Volkswagen Polo 2017", "time": "00:04:23.2610000", "penalty": "00:00:00", "delta": "00:00:00", "platform": "XBOX", "club": "", "status": ""}
                    next(f)
                    asked_for_wrc_player = False
                    for row in list(csv.reader(f)):

                        if idx == len(files[club]) -1:
                            new_row = {"position": row[0], 
                                    "name": row[1], 
                                    "car": row[2], 
                                    "time": convert_to_timedelta(row[3]), 
                                    "delta": convert_to_timedelta(row[4]), 
                                    "platform": row[5], 
                                    "club": club, 
                                    "status": ""}
                        else:
                            new_row = {"position": row[0], 
                                    "name": row[1], 
                                    "car": row[2], 
                                    "time": convert_to_timedelta(row[3]), 
                                    "penalty": convert_to_timedelta(row[4]), 
                                    "delta": convert_to_timedelta(row[5]), 
                                    "platform": row[6], 
                                    "club": club, 
                                    "status": ""}

                        if new_row["name"] == "WRC Player":
                            if idx != 0 and len(wrc_players) == 1:
                                new_row["name"] = wrc_players[0]
                            else:    
                                new_row["name"] = input(f'Enter the name of the driver in position {new_row["position"]} of stage {str(idx+1)}: ')
                                asked_for_wrc_player = True
                                wrc_players.append(new_row["name"])
                        
                        if new_row["name"] not in self.drivers:
                            if self.club == "WREC":
                                self.drivers[new_row["name"]] = Driver(new_row["name"], new_row["car"], new_row["club"], None)
                            else:
                                self.drivers[new_row["name"]] = Driver(new_row["name"], None, None, None)

                        if idx < 2 and self.drivers[new_row["name"]].club != new_row["club"]:
                            if new_row["name"] not in self.duplicate_drivers:
                                self.duplicate_drivers.append(new_row["name"])

                        temp_file.append(new_row)
                    
                    if asked_for_wrc_player:
                            print()

                if idx == len(files[club]) -1:
                    if len(files) == 1:
                        self.overall = Stage(self.number, temp_file, club)
                    else:
                        self.multiclass_overall.append(Stage(self.number, temp_file, club))
                else:
                    self.stages.append(Stage(f'{self.number} S{str(idx + 1)}', temp_file, club))
    
    def remove_duplicate_drivers(self):
        for duplicate_driver in self.duplicate_drivers:
            for stages in [self.stages, self.multiclass_overall]:
                for stage in stages:
                    if stage.club != self.drivers[duplicate_driver].club or self.drivers[duplicate_driver].club is None:
                        for row in stage.result:
                            if row.get("name") == duplicate_driver:
                                stage.result.remove(row)
                                continue
                        continue
            
            if self.drivers[duplicate_driver].club is None:
                self.drivers.pop(duplicate_driver)
                print(f'-- {duplicate_driver} has been removed from the round!')                

    def export_wrec_results(self):
        file = f'Output/WREC/{self.number}.csv'

        with open(file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for stage in self.stages:
                writer.writerow([stage.number])
                for idx, row in enumerate(stage.result):
                    writer.writerow(["", idx+1 if row["status"] == "" else row["status"], row["name"], row["car"]])
                
            writer.writerow([self.overall.number])
            for idx, row in enumerate(self.overall.result):
                last_day_length = len(self.stages) - self.wrec_last_day
                last_day_cutoff = len(self.drivers[row["name"]].completed_stages) - last_day_length
                first_days_stages = [stage for stage in self.drivers[row["name"]].completed_stages[:self.wrec_last_day]]
                last_day_stages = [stage for stage in self.drivers[row["name"]].completed_stages[last_day_cutoff:]]
                survived_first_days = "YES" if first_days_stages and first_days_stages[-1].split(" ")[-1] == f'S{self.wrec_last_day}' else "NO"
                survived_last_day = "YES" if last_day_stages and last_day_stages[0].split(" ")[-1] == f'S{self.wrec_last_day+1}' else "NO"
                
                writer.writerow(["", idx+1 if row["status"] == "" else row["status"], row["name"], row["car"], "", survived_first_days, survived_last_day])
    
    def export_wrc_results(self):
        files = [f'Output/WRC/{self.number}.csv', f'Output/WRC1/{self.number}.csv', f'Output/WRC2/{self.number}.csv']
        for file in files:
            with open(file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if file.split("/")[1] == "WRC":
                    writer.writerow(["", "Position", "Name", "Class", "Tier", "Car", "Time", "Diff", "Points", "PS Points", "Total Points"])
                    for idx, row in enumerate(self.overall.result):
                        driver = self.drivers[row["name"]]
                        writer.writerow([
                            "", 
                            idx+1 if row["status"] == "" else row["status"], 
                            row["name"], 
                            row["club"], 
                            driver.tier, 
                            row["car"], 
                            row["time"], 
                            row["delta"], 
                            driver.points, 
                            driver.power_stage_points, 
                            driver.total_points])
                else:
                    for stage in self.stages:
                        writer.writerow([stage.number])
                        position = 1
                        for row in stage.result:
                            if file.split("/")[1] == row["club"]:
                                writer.writerow(["", position if row["status"] == "" else row["status"], row["name"]])
                                position += 1
                        
                    writer.writerow([self.overall.number])
                    position = 1
                    for row in self.overall.result:
                        if file.split("/")[1] == row["club"]:
                            writer.writerow(["", position if row["status"] == "" else row["status"], row["name"]])
                            position += 1

    def get_round_cutoff(self):
        if self.club == "WREC":
            return math.ceil(len(self.stages)*0.67)
        else:
            return math.floor(len(self.stages)*0.67)

    def find_dnfs(self):
        for idx, stage in enumerate(self.stages):

            current_stage_drivers = []
            current_nominal_time = None
            current_nominal_delta = None
            stage_times = []

            for pos, row in enumerate(stage.result):

                driver = self.drivers[row["name"]]
                stage.fastest_time = row["time"] if pos == 0 else stage.fastest_time
                stage.slowest_time = row["time"] if pos == len(stage.result) -1 else stage.slowest_time

                if idx >= len(self.stages)-1 and len(driver.completed_stages) < self.get_round_cutoff():
                    driver.did_not_finish = True
                
                if str(row["time"]).split(".")[0] in nominal_times or (driver.did_not_finish and self.club != "WREC"): # Exclude WREC to not tank peoples ELO
                    row["status"] = "DNF"
                    if str(row["time"]).split(".")[0] in nominal_times and current_nominal_time is None:
                        current_nominal_time = row["time"]
                        current_nominal_delta = row["delta"]
                else:
                    driver.completed_stages.append(stage.number)
                
                driver.total_time = sum_stage_times(driver.total_time, row["time"])
                
                if idx >= len(self.stages)-1 and driver.car != row["car"] and not driver.did_not_finish:
                    print(f'-> {driver.name} has used the wrong car!')
                    while True:
                        try:
                            choice = int(input("Enter which number of offense this is [1 = First / 2 = Second / 3 = Third] "))
                        except ValueError:
                            print("Invalid choice. Try again!")
                            continue

                        match choice:
                            case 1 | 2:
                                driver.used_wrong_car = choice
                                row["time"] = sum_stage_times(row["time"], convert_to_timedelta(car_penalty_times_ps[choice-1]))
                                row["penalty"] = sum_stage_times(row["penalty"], convert_to_timedelta(car_penalty_times_ps[choice-1]))
                                break
                            case 3:
                                driver.did_not_finish = True
                                break
                            case _:
                                if not challenge_yes_or_no("You must choose a number between 1 and 3 Try again?"):
                                    quit(no_export_string)

                    print(f'-- Penalties have been applied to {driver.name}\n')

                row["delta"] = get_gap_to_leader(stage.fastest_time, row["time"]) if self.club != "WREC" else row["delta"]

                if str(row["time"]).split(".")[0] not in nominal_times:
                    stage_times.append(row["time"])

                current_stage_drivers.append(row["name"])
                stage.result[pos] = row

            missing_drivers = [driver for driver in self.drivers.values() if driver.name not in current_stage_drivers]
            if current_nominal_time is None and missing_drivers:
                average_time = sum(stage_times, timedelta()) / len(stage_times)
                for time in nominal_times:
                    cutoff = timedelta(minutes=4)
                    delta = convert_to_timedelta(time) - average_time
                    if delta > cutoff:
                        while True:
                            stage_number = re.findall(r'\d+', stage.number)[-1]
                            print(f'-> Slowest time on stage {stage_number} is {stage.slowest_time}')
                            if not challenge_yes_or_no(f'No nominal time found. Do you want to set {time} as nominal time for stage {stage_number}?'):
                                while True:
                                    nominal_time_choice = input("Select a new nominal time, or quit. [1 = 08min / 2 = 16min / 3 = 25min / 4 = 35min / q = quit] ").lower()
                                    if nominal_time_choice == "q":
                                        quit(no_export_string)
                                    elif int(nominal_time_choice) in range(1,5):
                                        current_nominal_time = convert_to_timedelta(nominal_times[int(nominal_time_choice)-1])
                                        current_nominal_delta = get_gap_to_leader(stage.fastest_time, current_nominal_time)
                                        break
                                break      
                            else:
                                current_nominal_time = convert_to_timedelta(time)
                                current_nominal_delta = get_gap_to_leader(stage.fastest_time, current_nominal_time)
                                break
                        break

            for driver in missing_drivers:
                stage.result.append({
                    "position": len(stage.result)+1, 
                    "name": driver.name, 
                    "car": driver.car, 
                    "time": current_nominal_time, 
                    "penalty": current_nominal_time, 
                    "delta": current_nominal_delta, 
                    "platform": driver.platform, 
                    "club": driver.club, 
                    "status": "DNF"})
                driver.total_time = sum_stage_times(driver.total_time, current_nominal_time)
                if idx == len(self.stages)-1:
                    driver.did_not_retire = True

            stage.result = sorted(stage.result, key=lambda x: x["time"])
            stage.result = sorted(stage.result, key=lambda x: (not x["status"], x["status"]), reverse=True)
            self.stages[idx] = stage
    
    def calculate_standings(self):
        if self.overall:
            final_drivers = []
            for pos, row in enumerate(self.overall.result):
                driver = self.drivers[row["name"]]
                final_drivers.append(driver.name)
                row["status"] = "DNF" if len(driver.completed_stages) < self.get_round_cutoff() else ""
                if driver.used_wrong_car is not None:
                    row["time"] = sum_stage_times(row["time"], convert_to_timedelta(car_penalty_times_overall[driver.used_wrong_car-1]))
                self.winner_time = sum_stage_times(self.winner_time, row["time"]) if pos == 0 else self.winner_time
                row["delta"] = get_gap_to_leader(self.winner_time, row["time"]) if self.club != "WREC" else row["delta"]
                self.overall.result[pos] = row

            missing_drivers = [driver for driver in self.drivers.values() if driver.name not in final_drivers]
            for driver in missing_drivers:
                self.overall.result.append({
                    "position": len(self.overall.result)+1, 
                    "name": driver.name, 
                    "car": driver.car, 
                    "time": driver.total_time, 
                    "delta": get_gap_to_leader(self.winner_time, driver.total_time),
                    "platform": driver.platform, 
                    "club": driver.club, 
                    "status": "DNF" if len(driver.completed_stages) < self.get_round_cutoff() else ""})

            self.overall.result = sorted(self.overall.result, key=lambda x: (not x["status"], x["status"]), reverse=True)
            self.overall.result = sorted(self.overall.result, key=lambda x: x["time"])

    def apply_points(self):
        for pos, row in enumerate(self.stages[-1].result[:5]):
            self.drivers[row["name"]].power_stage_points = power_stage_points[pos] if row["status"] == "" else 0

        for pos, row in enumerate(self.overall.result):
            driver = self.drivers[row["name"]]
            driver.points = points[pos] if row["status"] == "" else 0
            driver.total_points = driver.points + driver.power_stage_points if row["status"] == "" else 0

    def merge_stages(self):
        temp_stages = {}
        wrc1_stages = self.stages[:len(self.stages)//2]
        wrc2_stages = self.stages[len(self.stages)//2:]
        wrc1_stages.append(self.multiclass_overall[0])
        wrc2_stages.append(self.multiclass_overall[1])
        
        for idx, stage in enumerate(wrc1_stages):
            merged_stage = [x for x in chain.from_iterable(zip_longest(stage.result, wrc2_stages[idx].result, fillvalue=None))]
            merged_stage = list(filter(None, merged_stage))
            merged_stage = sorted(merged_stage, key= lambda x: x["time"])

            for idy, row in enumerate(merged_stage):
                row["position"] = str(idy+1)
        
            temp_stages[stage.number] = merged_stage
        
        self.overall = Stage(self.number, temp_stages.pop(self.number), None)
        self.stages = []

        for stage in temp_stages:
            self.stages.append(Stage(stage, temp_stages[stage], None))

def main():
    paths = []
    round_number = ""

    for category in club_folders: # Create the folder structure if it doesn't exist
        for folder in club_folders[category]:
            folder = folder if category == "Input" else f'{category}/{folder}'
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    while True: # Asks for a valid club. Will be used as the first level of the glob path
        club = input("Enter the name of the club (WRC / WREC): ").upper()
        if club not in valid_clubs:
            if not challenge_yes_or_no(f'{club} is not a valid club. Try again?'):
                quit(no_export_string)
        else:
            break
    
    looking_for_path = True
    while looking_for_path: # Asks for a valid seaons/round. Will be used as the second level of the glob path
        round_number = input("Enter the season and round as 'S# R#': ").upper()
        paths = [f'{path}/{round_number}' for path in valid_clubs[club]]
        for path in paths:
            if not Path(path).is_dir() or not any(Path(path).iterdir()): # Checks if the directory exists and contains files
                if not challenge_yes_or_no(f'The directory for {path} does not exist or is empty. Make sure the Racenet files are in the correct location. Try again?'):
                    quit(no_export_string)
                else:
                    break
            elif Path(f'Output/{club}/{round_number}.csv').is_file(): # Asks to overwrite the output file if one exists
                if not challenge_yes_or_no(f'An output file for {club} {round_number} already exists. Overwrite?'):
                    quit(no_export_string)
                else:
                    looking_for_path = False
                    break
            else:
                looking_for_path = False

    round_files = {}
    for path in paths: # Get all stage files for the round and sort them by name and length
        temp = (glob.glob(f'{path}/*.csv'))
        temp = sorted(temp, key= lambda x: re.split(r"[/\\]", x)[-1])
        temp = sorted(temp, key=len)
        round_files[path.split("/")[0]] = temp # Use the first level of the path as the dictionary key
    
    if not any(round_files.values()): # Quit if glob didn't find any files
        quit(f'No files were found. {no_export_string}')
    else:
        for club_file in round_files: # Count how many files were found
            stage_pattern = r"^((WRC[12]|WREC)\/S\d{1,2} R\d{1,2}[\\\/])wrc2023_event_[a-zA-Z0-9]+_stage[0-9]+_leaderboard_results.csv$"
            overall_pattern = r"^((WRC[12]|WREC)\/S\d{1,2} R\d{1,2}[\\\/])wrc2023_event_[a-zA-Z0-9]+_stage_overall_leaderboard_results.csv$"
            stage_count = 0
            overall_count = 0
            for path in round_files[club_file]:
                if re.match(stage_pattern, path):
                    stage_count += 1
                elif re.match(overall_pattern, path):
                    overall_count += 1
            print(f'Found {stage_count} stage file(s) in {club_file}.')
            print(f'Found {overall_count} overall file(s) in {club_file}.')

    if challenge_yes_or_no():
        alr_round = Round(club, round_number)

        if club == "WREC":
            while True:
                try: # Asks for the first stage of the last day. Needed for WREC survival check
                    wrec_last_day = int(input("Enter the stage number for the first stage of Day 4: "))
                    if int(wrec_last_day) > len(round_files["WREC"]) -1:
                        if not challenge_yes_or_no(f'Number must be less than {len(round_files["WREC"]) -1}. Try again?'):
                            quit(no_export_string)
                    else:
                        alr_round.wrec_last_day = wrec_last_day - 1
                        print()
                        break
                except ValueError:
                    print(f'You must enter a number less than {len(round_files["WREC"]) -1}.')

        if len(valid_clubs[club]) > 1:
            alr_round.import_drivers()
            alr_round.import_stages(round_files)
            alr_round.remove_duplicate_drivers()
            print()
            alr_round.merge_stages()
        else:
            alr_round.import_stages(round_files)

        alr_round.find_dnfs()
        alr_round.calculate_standings()
        if len(valid_clubs[club]) > 1:
            alr_round.apply_points()
            alr_round.export_wrc_results()
        else:
            alr_round.export_wrec_results()
        
        dnf_drivers = [driver for driver in alr_round.drivers.values() if driver.did_not_retire]
        for driver in dnf_drivers:
            print(f'-- {driver.name} failed to retire properly!')
        
        print("\nResults have been successfully exported!")
    else:
        print(no_export_string)

if __name__ == "__main__":
    main()