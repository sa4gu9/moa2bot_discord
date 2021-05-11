def GetUserInfo(ctx, db):
    return db.reference(f"servers/server{ctx.guild.id}/users/user{ctx.author.id}")


def AddNewUser(direct, nickname, code, password):
    if direct.get() == None:
        firstData = {
            "nickname": f"[첫 시작]{nickname}#{code}",
            "titles": [0],
            "password": password,
        }

        direct.set(firstData)

        direct = direct.child("재산")
        direct.set({"money": 200000})

        return 1
    else:

        return -1


def GetAllServerUser(users):

    sendText = "```"

    userInfo = users.get()

    for user in userInfo.keys():
        sendText += (
            f"{userInfo[user]['nickname']} : {userInfo[user]['재산']['money']}모아\n"
        )

    sendText += "```"

    return sendText


def ReturnInfo(ctx,db):
    refer = GetUserInfo(ctx, db)

    userinfo = refer.get()

    money = userinfo["재산"]["money"]
    nickname = userinfo["nickname"]

    return money, nickname