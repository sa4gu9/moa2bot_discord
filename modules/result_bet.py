import math


def CheckResult(user, betData, key, returnResult, winTeam, finance):
    if betData[key]["team"] == winTeam:
        getMoney = math.floor(betData[key]["moa"] * returnResult)
        finance.ChangeMoney(user, getMoney)
        result=1
    else:
        result=-1
        getMoney=0
    return result,getMoney
