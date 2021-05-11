def ChangeUnknown(userdir, mode, itemlevel=None):
    haveInfo = userdir.child(f"inventory/의문의 물건")
    if mode == 1:
        haveInfo.update({"level": itemlevel})
    elif mode == 2:
        haveInfo.update({"level": None})


def GetInventory(user):
    inventory = user.child("inventory").get()
    sendText = "```"

    for key in inventory.keys():
        sendText += f"{key} : {inventory[key]}\n"
    sendText += "```"

    return sendText