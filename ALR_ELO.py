import csv
import glob
from pathlib import Path
import re

def challengeYesOrNo(question="Continue?"):
    # Inspired by https://stackoverflow.com/a/3041990
    valid = {"y": True, "yes": True, "n": False, "no": False}

    while True:
        choice = input(f"{question} [y/n] ").lower()
        if choice in valid:
            return valid[choice]
        else:
            print("Please respond with y or n")

def importResults(file):
    file = file
    with open(file, newline='') as f:
        next(f)
        return list(csv.reader(f))
    
def exportResults(outData, path):
    file = "Output/" + path + ".csv"
    with open(file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for stage in outData:
            writer.writerow([stage])
            for row in outData[stage]:
                writer.writerow(["", row["Position"], row["Display Name"]])

def sortStages(files, round):
    stages = {}
    results = {} # KEY = title, VALUE = sorted stage results
    wrcPlayers = []

    for idx, file in enumerate(files):
        stageFile = importResults(file)
        if idx == len(files) -1:
            stages[round] = stageFile
        else:
            stages[round + " S"+ str(idx + 1)] = stageFile

    previousStageDrivers = []

    for idy, stage in enumerate(stages):
        
        nominalTimes = ["00:08:00", "00:16:00", "00:25:00", "00:35:00"]
        currentStageDrivers = []
        stageResult = []

        for driver in stages[stage]:
            position = driver[0]
            displayName = driver[1]
            stageTime = driver[4]

            if displayName == "WRC Player":
                if idy != 0 and len(wrcPlayers) == 1:
                    displayName = wrcPlayers[0]
                else:    
                    displayName = input(f"Enter the name of the driver in position {position} of stage {str(idy+1)}: ")
                    wrcPlayers.append(displayName)

            if stageTime in nominalTimes:
                position = "DNF"
            
            currentStageDrivers.append(displayName)
            
            stageResult.append({"Position": position, "Display Name" : displayName})

        if previousStageDrivers:
            tmpDrivers = []
            for driver in previousStageDrivers:
                if driver not in currentStageDrivers:
                    stageResult.append({"Position": "DNF", "Display Name" : driver})
                    tmpDrivers.append(driver)
            
            currentStageDrivers = currentStageDrivers + tmpDrivers
        
        previousStageDrivers = currentStageDrivers

        results[stage] = stageResult
    return results

def main():
    clubs = ("WRC1", "WRC2", "WREC")
    
    for c in clubs: #Create the folder structure if it doesn't exist
        Path(c).mkdir(exist_ok=True)
        Path("Output/" + c).mkdir(parents=True, exist_ok=True)
    
    while True:
        club = input("Enter the name of the club (WRC1 / WRC2 / WREC): ").upper()
        if club not in clubs:
            if not challengeYesOrNo(f"{club} is not a valid club. Try again?"):
                quit("No results have been exported")
        else:
            break
    
    while True:
        round = input("Enter the season and round as 'S# R#': ").upper()
        path = f"{club}/{round}"
        if not Path(path).is_dir():
            if not challengeYesOrNo(f"No directory for {club}/{round} exists. Try again?"):
                quit("No results have been exported")
        elif Path(f"Output/{club}/{round}.csv").is_file():
            if not challengeYesOrNo(f"An output for {club} {round} already exists. Overwrite?"):
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
        print("Found the following number of stages")
        print(f"Stage files: {stagenum}")
        print(f"Overall: {overallnum}")
    
    if challengeYesOrNo():
        exportResults(sortStages(files, round), path)
        print("ELO results exported")
    else:
        print("No results have been exported")

if __name__ == "__main__":
    main()