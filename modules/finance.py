def ChangeMoney(user, moa):
    userfinance = user.child("재산")
    userfinance.update({"money": userfinance.get()["money"] + int(moa)})