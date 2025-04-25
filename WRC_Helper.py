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

    def __eq__(self, other):
        return self.name == other.name

class Stage:
    def __init__(self, number, results):
        self.number = number
        self.results = results

class Round:
    def __init__(self, club, number):
        self.club = club
        self.number = number
        self.drivers = []
        self.stages = []
        self.results = {}
    
    def import_results(self, files, roundnum):

        wrcplayers = []

        for idx, file in enumerate(files):
            with open(file, newline='') as f:
                next(f)
                stage_file = list(csv.reader(f))

            #EXAMPLE ROWS:
            #['1', 'Slokksi', 'Volkswagen Polo 2017', '00:04:23.2610000', '00:00:00', '00:00:00', 'XBOX', '']
            #['2', 'TheMightyIggy', 'Ford Fiesta WRC', '00:04:24.1590000', '00:00:00', '00:00:00.8980000', 'PSN', '']

            for idy, row in enumerate(stage_file):
                if row[1] == "WRC Player":
                    if idy != 0 and len(wrcplayers) == 1:
                        row[1] = wrcplayers[0]
                    else:    
                        row[1] = input(f"Enter the name of the driver in position {row[0]} of stage {str(idx+1)}: ")
                        stage_file[idy] = row
                        wrcplayers.append(driver.name)

                driver = Driver(row[1], row[2], row[6], self.club)

                if idx == len(files) -1:
                    row[6] = driver.club
                else:
                    row[7] = driver.club

                if not driver in self.drivers:
                    self.drivers.append(driver)

            if idx == len(files) -1:
                self.stages.append(Stage(roundnum, stage_file))
            else:
                self.stages.append(Stage(f"{roundnum} S{str(idx + 1)}", stage_file))
        
    def export_results(self, files):
        self.import_results(files, self.number)
        self.find_dnfs()
        file = "Output/" + f"{self.club}/{self.number}" + ".csv"

        with open(file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for stage in self.results:
                writer.writerow([stage])
                for row in self.results[stage]:
                    if self.club == "WREC":
                        writer.writerow(["", row[0], row[1], row[2]])
                    else:
                        writer.writerow(["", row[0], row[1]])

    def find_dnfs(self):                

        previous_stage_drivers = []

        for stage in self.stages:

            nominal_times = ["00:08:00", "00:16:00", "00:25:00", "00:35:00"]
            current_stage_drivers = []

            for idx, row in enumerate(stage.results):

                if row[3] in nominal_times:
                    row[0] = "DNF"
                
                current_stage_drivers.append(row[1])
                stage.results[idx] = row

            if previous_stage_drivers:
                tmp_drivers = []
                for name in previous_stage_drivers:
                    if name not in current_stage_drivers:
                        for d in self.drivers:
                            if d.name == name:
                                driver = d
                        if len(stage.number) == 5:
                            stage.results.append(['DNF', driver.name, driver.car, '10:00:00', '10:00:00', driver.platform, driver.club])
                        else:
                            stage.results.append(['DNF', driver.name, driver.car, '10:00:00', '10:00:00', '10:00:00', driver.platform, driver.club])
                        tmp_drivers.append(name)
                
                current_stage_drivers = current_stage_drivers + tmp_drivers
            
            previous_stage_drivers = current_stage_drivers

            self.results[stage.number] = stage.results

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
            print(f)
            if re.match(stagep, f):
                stagenum += 1
            elif re.match(overallp, f):
                overallnum += 1
        print("Found the following number of stages")
        print(f"Stage files: {stagenum}")
        print(f"Overall: {overallnum}")

    if challenge_yes_or_no():
        round = Round(club, roundnum)
        round.export_results(files)
        print("ELO results exported")
    else:
        print("No results have been exported")

if __name__ == "__main__":
    main()