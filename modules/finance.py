def ChangeMoney(user, moa):
    userfinance = user.child("재산")

    if userfinance.get()["money"] + int(moa) < 0:
        return -1
    userfinance.update({"money": userfinance.get()["money"] + int(moa)})
    return 1