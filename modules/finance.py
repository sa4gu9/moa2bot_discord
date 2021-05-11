import random


def ChangeMoney(user, moa):
    userfinance = user.child("재산")

    fina = userfinance.get()

    if fina["money"] + int(moa) < 0:
        return -1, int(moa) - fina["money"]
    userfinance.update({"money": fina["money"] + int(moa)})
    return 1, 0


def GetBeggingMoa():
    i = 1
    cut = 0
    getmoa = 0
    result = random.random() * 100
    while i <= 12:
        cut += i
        if result < cut:
            getmoa = 32000 - 1000 * (i - 1)
            break
        else:
            i += 1
    if i == 1:
        result = random.random() * 100
        if result < 10:
            getmoa *= 2
    if i == 13:
        getmoa = 2500

    return getmoa