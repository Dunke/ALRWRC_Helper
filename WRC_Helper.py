import csv
import glob
from itertools import zip_longest, chain
from pathlib import Path
import re

club_folders = {"Input": ["WRC1", "WRC2", "WREC"], "Output": ["WRC", "WREC"]}
valid_clubs = {"WRC": ["WRC1", "WRC2"], "WREC": ["WREC"]}#, "WRC1": ["WRC1"]}

class Driver:
    def __init__(self, name, car, club):
        self.name = name
        self.car = car
        self.platform = None
        self.club = club
        self.completed_stages = []
        self.did_not_finish = False # For drivers who completed less than 6 stages in WRC1/2 or retired correctly
        self.did_not_retire = False # For drivers who did not retire correctly and are missing from the results

    def __eq__(self, other):
        return self.name == other.name

class Stage:
    def __init__(self, number, result, club):
        self.number = number
        self.result = result
        self.club = club

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

    def import_drivers(self):
        file = f'WRC Drivers/Drivers {self.number}.csv'
        with open(file, newline='') as f:
            for row in list(csv.reader(f)):
                if row[0] not in self.drivers:
                    self.drivers[row[0]] = Driver(row[0], row[2], row[1])

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
                    for idy, row in enumerate(list(csv.reader(f))):

                        if idx == len(files[club]) -1:
                            new_row = {"position": row[0], 
                                    "name": row[1], 
                                    "car": row[2], 
                                    "time": row[3], 
                                    "delta": row[4], 
                                    "platform": row[5], 
                                    "club": club, 
                                    "status": ""}
                        else:
                            new_row = {"position": row[0], 
                                    "name": row[1], 
                                    "car": row[2], 
                                    "time": row[3], 
                                    "penalty": row[4], 
                                    "delta": row[5], 
                                    "platform": row[6], 
                                    "club": club, 
                                    "status": ""}

                        if new_row["name"] == "WRC Player":
                            if idy != 0 and len(wrc_players) == 1:
                                new_row["name"] = wrc_players[0]
                            else:    
                                new_row["name"] = input(f"Enter the name of the driver in position {new_row['position']} of stage {str(idx+1)}: ")
                                wrc_players.append(new_row["name"])
                        
                        if new_row["name"] not in self.drivers:
                            if self.club == "WREC":
                                self.drivers[new_row["name"]] = Driver(new_row["name"], new_row["car"], new_row["club"])
                            else:
                                self.drivers[new_row["name"]] = Driver(new_row["name"], None, None)

                        if idx < 2 and self.drivers[new_row["name"]].club != new_row["club"]:
                            if new_row["name"] not in self.duplicate_drivers:
                                self.duplicate_drivers.append(new_row["name"])

                        temp_file.append(new_row)

                if idx == len(files[club]) -1:
                    if len(files) == 1:
                        self.overall = Stage(self.number, temp_file, club)
                    else:
                        self.multiclass_overall.append(Stage(self.number, temp_file, club))
                else:
                    self.stages.append(Stage(f"{self.number} S{str(idx + 1)}", temp_file, club))
    
    def remove_duplicate_drivers(self):
        for duplicate_driver in self.duplicate_drivers:
            for stage in self.stages:
                if stage.club != self.drivers[duplicate_driver].club or self.drivers[duplicate_driver].club == None:
                    for row in stage.result:
                        if row.get("name") == duplicate_driver:
                            stage.result.remove(row)
                            continue
                    continue

            for stage in self.multiclass_overall:
                if stage.club != self.drivers[duplicate_driver].club or self.drivers[duplicate_driver].club == None:
                    for row in stage.result:
                        if row.get("name") == duplicate_driver:
                            stage.result.remove(row)
                            continue
                    continue
            
            if self.drivers[duplicate_driver].club == None:
                self.drivers.pop(duplicate_driver)
                print(f'-- {duplicate_driver} has not signed up and has been removed! --')

    def wrc_writerow(self, writer, row, overall_stage):
        position = row["position"] if row["status"] == "" else row["status"]
        
        if self.club == "WREC":
            if overall_stage:
                first_days_stages = [stage for stage in self.drivers[row["name"]].completed_stages[:self.wrec_last_day]]
                last_day_stages = [stage for stage in self.drivers[row["name"]].completed_stages[self.wrec_last_day:]]
                survived_first_days = "YES" if first_days_stages and first_days_stages[-1].split(" ")[-1] == f'S{self.wrec_last_day}' else "NO"
                survived_last_day = "YES" if last_day_stages and last_day_stages[-1].split(" ")[-1] == f'S{len(self.stages)}' else "NO"

                writer.writerow(["", position, row["name"], row["car"], "", survived_first_days, survived_last_day])
            else:
                writer.writerow(["", position, row["name"], row["car"]])
        else:
            writer.writerow(["", position, row["name"], row["club"]])

    def export_results(self):
        file = "Output/" + f"{self.club}/{self.number}" + ".csv"

        with open(file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for stage in self.stages:
                writer.writerow([stage.number])
                for row in stage.result:
                    self.wrc_writerow(writer, row, False)
                
            writer.writerow([self.overall.number])
            for row in self.overall.result:
                self.wrc_writerow(writer, row, True)

    def find_dnfs(self):
        for idx, stage in enumerate(self.stages):

            nominal_times = ["00:08:00", "00:16:00", "00:25:00", "00:35:00"]
            current_stage_drivers = []

            for pos, row in enumerate(stage.result):

                driver = self.drivers[row["name"]]

                if idx >= len(self.stages)-1 and len(driver.completed_stages) < len(self.stages)*0.75:
                    driver.did_not_finish = True

                if driver.did_not_finish and self.club != "WREC":
                    row["status"] = "DNF"  
                elif row["time"] in nominal_times:
                    row["status"] = "DNF" if self.club == "WREC" else "RET"
                else:
                    driver.completed_stages.append(stage.number)
                
                current_stage_drivers.append(row["name"])
                stage.result[pos] = row

            missing_drivers = [driver for driver in self.drivers.values() if driver.name not in current_stage_drivers]
            for driver in missing_drivers:
                stage.result.append({
                    "position": len(stage.result)+1, 
                    "name": driver.name, 
                    "car": driver.car, 
                    "time": "10:00:00", 
                    "penalty": "10:00:00", 
                    "delta": "10:00:00", 
                    "platform": driver.platform, 
                    "club": driver.club, 
                    "status": "DNF"})
                if idx == len(self.stages)-1:
                    driver.did_not_retire = True

            stage.result = sorted(stage.result, key=lambda x: (not x["status"], x["status"]), reverse=True)
            self.stages[idx] = stage
    
    def calculate_standings(self):
        if self.overall:
            final_drivers = []
            for pos, row in enumerate(self.overall.result):
                final_drivers.append(row["name"])
                row["status"] = "DNF" if self.drivers[row["name"]].did_not_retire or len(self.drivers[row["name"]].completed_stages) < len(self.stages)*0.75 else ""
                self.overall.result[pos] = row

            missing_drivers = [driver for driver in self.drivers.values() if driver.name not in final_drivers and driver.did_not_retire]
            for driver in missing_drivers:
                self.overall.result.append({
                    "position": len(self.overall.result)+1, 
                    "name": driver.name, 
                    "car": driver.car, 
                    "time": "10:00:00", 
                    "delta": "10:00:00", 
                    "platform": driver.platform, 
                    "club": driver.club, 
                    "status": "DNF"})

            self.overall.result = sorted(self.overall.result, key=lambda x: (not x["status"], x["status"]), reverse=True)

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

def challenge_yes_or_no(question="Continue?"):
    # Inspired by https://stackoverflow.com/a/3041990
    valid = {"y": True, "yes": True, "n": False, "no": False}

    while True:
        choice = input(f"{question} [y/n] ").lower()
        if choice in valid:
            return valid[choice]
        else:
            print("Please respond with y or n")

def main():    
    for category in club_folders: #Create the folder structure if it doesn't exist
        for folder in club_folders[category]:
            folder = folder if category == "Input" else f"{category}/{folder}"
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    while True:
        club = input("Enter the name of the club (WRC / WREC): ").upper()
        if club not in valid_clubs:
            if not challenge_yes_or_no(f"{club} is not a valid club. Try again?"):
                quit("No results have been exported")
        else:
            break
    
    looking_for_path = True
    while looking_for_path:
        round_number = input("Enter the season and round as 'S# R#': ").upper()
        paths = [f"{path}/{round_number}" for path in valid_clubs[club]]
        for path in paths:
            if not Path(path).is_dir():
                if not challenge_yes_or_no(f"No directory for {path} exists. Please make sure the Racenet files are in the correct place. Try again?"):
                    quit("No results have been exported")
            elif Path(f"Output/{club}/{round_number}.csv").is_file():
                if not challenge_yes_or_no(f"An output file for {club} {round_number} already exists. Overwrite?"):
                    quit("No results have been exported")
                else:
                    looking_for_path = False
                    break
            else:
                looking_for_path = False

    round_files = {}
    for path in paths:
        temp = (glob.glob(f"{path}/*.csv"))
        temp = sorted(temp, key= lambda x: re.split(r"/|\\", x)[-1])
        temp = sorted(temp, key=len)
        round_files[path.split("/")[0]] = temp
    
    if not any(round_files.values()):
        quit("No files were found")
    else:
        for club_file in round_files:
            stage_pattern = r"^((WRC[12]|WREC)\/S[\d] R[\d][\\\/])wrc2023_event_[a-zA-Z0-9]+_stage[0-9]+_leaderboard_results.csv$"
            overall_pattern = r"^((WRC[12]|WREC)\/S[\d] R[\d][\\\/])wrc2023_event_[a-zA-Z0-9]+_stage_overall_leaderboard_results.csv$"
            stage_count = 0
            overall_count = 0
            for path in round_files[club_file]:
                if re.match(stage_pattern, path):
                    stage_count += 1
                elif re.match(overall_pattern, path):
                    overall_count += 1
            print(f"Found {stage_count} stage file(s) in {club_file}.")
            print(f"Found {overall_count} overall file(s) in {club_file}.")

    if challenge_yes_or_no():
        round = Round(club, round_number)

        wrec_last_day = None
        if club == "WREC":
            while True:
                try:
                    wrec_last_day = int(input("Enter the stage number for the first stage of Day 4: "))
                    if int(wrec_last_day) > len(round_files["WREC"]) -1:
                        if not challenge_yes_or_no(f'{wrec_last_day} must be less than {len(round_files["WREC"]) -1}. Try again?'):
                            quit("No results have been exported")
                    else:
                        round.wrec_last_day = wrec_last_day
                        break
                except:
                    if not challenge_yes_or_no(f'You must enter a number less than {len(round_files["WREC"]) -1}. Try again?'):
                        quit("No results have been exported")

        if len(valid_clubs[club]) > 1:
            round.import_drivers()
            round.import_stages(round_files)
            round.remove_duplicate_drivers()
            round.merge_stages()
        else:
            round.import_stages(round_files)

        round.find_dnfs()
        round.calculate_standings()
        round.export_results()
        
        dnf_drivers = [driver for driver in round.drivers.values() if driver.did_not_retire]
        for driver in dnf_drivers:
            print(f'-- {driver.name} failed to retire properly! --')
        
        print("Results have been successfully exported!")
    else:
        print("No results have been exported!")

if __name__ == "__main__":
    main()