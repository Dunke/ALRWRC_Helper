import csv
import glob
from pathlib import Path
import re

class Driver:
    def __init__(self, name, car, platform, club):
        self.name = name
        self.car = car
        self.platform = platform
        self.club = club
        self.stages_completed = []
        self.retired = False
        self.dnf = False

    def __eq__(self, other):
        return self.name == other.name

class Stage:
    def __init__(self, number, result):
        self.number = number
        self.result = result

class Round:
    def __init__(self, club, number):
        self.club = club
        self.number = number
        self.drivers = {}
        self.stages = []
        self.overall = None
    
    def import_results(self, files):

        wrcplayers = []

        for idx, file in enumerate(files):
            with open(file, newline='') as f:
                next(f)
                stage_file = list(csv.reader(f))

            #EXAMPLE IN/OUT ROWS:
            #['1', 'Slokksi', 'Volkswagen Polo 2017', '00:04:23.2610000', '00:00:00', '00:00:00', 'XBOX', '', '']            
            #{"position": "1", "name": "Slokksi", "car": "Volkswagen Polo 2017", "time": "00:04:23.2610000", "penalty": "00:00:00", "delta": "00:00:00", "platform": "XBOX", "club": "", "status": ""}

            tmp_file = []
            for idy, row in enumerate(stage_file):

                if idx == len(files) -1:
                    new_row = {"position": row[0], 
                               "name": row[1], 
                               "car": row[2], 
                               "time": row[3], 
                               "delta": row[4], 
                               "platform": row[5], 
                               "club": self.club, 
                               "status": ""}
                else:
                    new_row = {"position": row[0], 
                               "name": row[1], 
                               "car": row[2], 
                               "time": row[3], 
                               "penalty": row[4], 
                               "delta": row[5], 
                               "platform": row[6], 
                               "club": self.club, 
                               "status": ""}

                if new_row["name"] == "WRC Player":
                    if idy != 0 and len(wrcplayers) == 1:
                        new_row["name"] = wrcplayers[0]
                    else:    
                        new_row["name"] = input(f"Enter the name of the driver in position {new_row["position"]} of stage {str(idx+1)}: ")
                        wrcplayers.append(driver.name)

                driver = Driver(new_row["name"], new_row["car"], new_row["platform"], new_row["club"])

                if new_row["name"] not in self.drivers:
                    self.drivers[new_row["name"]] = driver

                tmp_file.append(new_row)

            if idx == len(files) -1:
                self.overall = Stage(self.number, tmp_file)
            else:
                self.stages.append(Stage(f"{self.number} S{str(idx + 1)}", tmp_file))

    def wrc_writerow(self, writer, row):
        position = row["position"]
        if row["status"] != "":
            position = row["status"]

        if self.club == "WREC":
            writer.writerow(["", position, row["name"], row["car"]])
        else:
            writer.writerow(["", position, row["name"]])

    def export_results(self):
        file = "Output/" + f"{self.club}/{self.number}" + ".csv"

        with open(file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for stage in self.stages:
                writer.writerow([stage.number])
                for row in stage.result:
                    self.wrc_writerow(writer, row)
                
            writer.writerow([self.overall.number])
            for row in self.overall.result:
                self.wrc_writerow(writer, row)

    def find_dnfs(self):                

        previous_stage_drivers = []

        for idx, stage in enumerate(self.stages):

            nominal_times = ["00:08:00", "00:16:00", "00:25:00", "00:35:00"]
            current_stage_drivers = []

            for pos, row in enumerate(stage.result):

                driver = self.drivers[row["name"]]

                if idx >= len(self.stages)*0.75 and len(driver.stages_completed) < len(self.stages)*0.75:
                    driver.dnf = True

                if driver.dnf:
                    row["status"] = "DNF"  
                elif row["time"] in nominal_times:
                    row["status"] = "RET"
                else:
                    driver.stages_completed.append(stage.number)

                self.drivers[row["name"]] = driver
                
                current_stage_drivers.append(row["name"])
                stage.result[pos] = row

            if previous_stage_drivers:
                tmp_drivers = []
                for name in previous_stage_drivers:
                    if name not in current_stage_drivers:
                        stage.result.append({
                            "position": len(stage.result)+1, 
                            "name": self.drivers[name].name, 
                            "car": self.drivers[name].car, 
                            "time": "10:00:00", 
                            "penalty": "10:00:00", 
                            "delta": "10:00:00", 
                            "platform": self.drivers[name].platform, 
                            "club": self.drivers[name].club, 
                            "status": "DNF"})
                        if idx == len(self.stages)-1:
                            self.drivers[name].dnf = True
                        tmp_drivers.append(name)
                
                current_stage_drivers = current_stage_drivers + tmp_drivers
            
            previous_stage_drivers = current_stage_drivers

            stage.result = sorted(stage.result, key=lambda x: (not x["status"], x["status"]), reverse=True)
            self.stages[idx] = stage
    
    def calculate_standings(self):
        if self.overall:
            final_drivers = []
            for pos, row in enumerate(self.overall.result):
                final_drivers.append(row["name"])
                if self.drivers[row["name"]].dnf:
                    row["status"] = "DNF"
                self.overall.result[pos] = row

            if self.drivers[row["name"]].name not in final_drivers and self.drivers[row["name"]].dnf:
                self.overall.result.append({
                    "position": len(self.overall.result)+1, 
                    "name": self.drivers[row["name"]].name, 
                    "car": self.drivers[row["name"]].car, 
                    "time": "10:00:00", 
                    "delta": "10:00:00", 
                    "platform": self.drivers[row["name"]].platform, 
                    "club": self.drivers[row["name"]].club, 
                    "status": "DNF"})

            self.overall.result = sorted(self.overall.result, key=lambda x: (not x["status"], x["status"]), reverse=True)

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
    clubs = ("WRC1", "WRC2", "WREC")
    
    for c in clubs: #Create the folder structure if it doesn't exist
        Path(c).mkdir(exist_ok=True)
        Path("Output/" + c).mkdir(parents=True, exist_ok=True)
    
    while True:
        club = input("Enter the name of the club (WRC1 / WRC2 / WREC): ").upper()
        if club not in clubs:
            if not challenge_yes_or_no(f"{club} is not a valid club. Try again?"):
                quit("No results have been exported")
        else:
            break
    
    while True:
        roundnum = input("Enter the season and round as 'S# R#': ").upper()
        path = f"{club}/{roundnum}"
        if not Path(path).is_dir():
            if not challenge_yes_or_no(f"No directory for {path} exists. Try again?"):
                quit("No results have been exported")
        elif Path(f"Output/{path}.csv").is_file():
            if not challenge_yes_or_no(f"An output for {club} {roundnum} already exists. Overwrite?"):
                quit("No results have been exported")
            else:
                break
        else:
            break
    
    files = glob.glob(path + "/" + "*.csv")
    files = sorted(files, key= lambda x: re.split(r"/|\\", x)[-1])
    files = sorted(files, key=len)

    if not files:
        quit("No files were found")
    else:
        stagep = r"^((WRC[12]|WREC)\/S[\d] R[\d][\\\/])wrc2023_event_[a-zA-Z0-9]+_stage[0-9]+_leaderboard_results.csv$"
        overallp = r"^((WRC[12]|WREC)\/S[\d] R[\d][\\\/])wrc2023_event_[a-zA-Z0-9]+_stage_overall_leaderboard_results.csv$"
        stagenum = 0
        overallnum = 0
        for f in files:
            if re.match(stagep, f):
                stagenum += 1
            elif re.match(overallp, f):
                overallnum += 1
        print(f"Found {stagenum} stage file(s).")
        print(f"Found {overallnum} overall file(s).")

    if challenge_yes_or_no():
        round = Round(club, roundnum)
        round.import_results(files)
        round.find_dnfs()
        round.calculate_standings()
        round.export_results()
        print("ELO results exported")
    else:
        print("No results have been exported")

if __name__ == "__main__":
    main()