def ChangeMoney(user, moa):
    userfinance = user.child("재산")

    fina=userfinance.get()

    if fina["money"] + int(moa) < 0:
        return -1,int(moa)-fina["money"]
    userfinance.update({"money": fina["money"] + int(moa)})
    return 1