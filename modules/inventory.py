def GetUnknown(userdir, itemgrade, itemlevel):
    haveInfo = userdir.child(f"inventory/의문의 물건/등급{itemgrade}")

    if haveInfo.get() == None:
        haveInfo.update({f"레벨{itemlevel}": 1})
    else:
        if f"레벨{itemlevel}" in haveInfo.get().keys():
            haveInfo.update({f"레벨{itemlevel}": haveInfo.get()[f"레벨{itemlevel}"] + 1})
        else:
            haveInfo.update({f"레벨{itemlevel}": 1})


def LostUnknown(userdir, itemgrade, itemlevel):
    haveInfo = userdir.child(f"inventory/의문의 물건/등급{itemgrade}")

    haveDict = haveInfo.get()

    if f"레벨{itemlevel}" in haveDict.keys():
        if haveDict[f"레벨{itemlevel}"] - 1 == 0:
            haveInfo.update({f"레벨{itemlevel}": None})
        else:
            haveInfo.update({f"레벨{itemlevel}": haveDict[f"레벨{itemlevel}"] - 1})
    else:
        return