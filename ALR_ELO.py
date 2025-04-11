import csv
import glob

def importResult(file):
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
        stageFile = importResult(file)
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
                if wrcPlayers and len(wrcPlayers) == 1: #NEEDS TO BE FIXED
                    displayName = wrcPlayers[0]
                else:    
                    displayName = input("Enter the name of the driver in position " + position + " of stage " + str(idy+1) + ": ")
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

if __name__ == "__main__":
    club = input("Enter the name of the club (WRC1 / WRC2 / WREC / SC): ").upper()
    round = input("Enter the season and round as 'S* R*': ").upper()
    path = club + "/" + round
    files = sorted(glob.glob(path + "/" + "*stage*"), key=len)
    if not files:
        print("No files found")
    else:    
        exportResults(sortStages(files, round), path)
        print("ELO results exported")