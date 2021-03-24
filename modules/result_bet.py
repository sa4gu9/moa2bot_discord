import math


def CheckResult(user, betData, key, returnResult, winTeam, finance):
    if betData[key]["team"] == winTeam:
        getMoney = math.floor(betData[key]["moa"] * returnResult)
        finance.ChangeMoney(user, getMoney)
        return 1
    else:
        return -1