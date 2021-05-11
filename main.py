# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
import random
import datetime
import string
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
import math
import traceback
from discord.ext import tasks
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import json
import asyncio
import datetime

from modules import (
    finance,
    betting,
    reinforce,
    result_bet,
    store,
    user,
    todaymoa,
    inventory,
)

from bs4 import BeautifulSoup
import requests


version = "V2.21.05.01"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)
token = ""

testMode = None
cred = None
dbfs = None

currentOpen = input("현재 열고있는 창이 gcp면 gcp를 입력, vscode면 vscode를 입력해주세요.")

if currentOpen == "gcp":
    testMode = False
elif currentOpen == "vscode":
    testMode = True
else:
    exit()

tokenfile = open("token.json")
important = json.load(tokenfile)


if not testMode:  # 정식 모드
    jsoncon = important["gcp"]

    project_id = jsoncon["project_id"]
    token = jsoncon["token"]

    cred = credentials.Certificate(jsoncon["filepath"])
    print("gcp")
    firebase_admin.initialize_app(cred, {"databaseURL": jsoncon["databaseurl"]})

else:  # 테스트 모드
    jsoncon = important["vscode"]

    project_id = jsoncon["project_id"]
    token = jsoncon["token"]

    version = f"TEST {version}"
    cred = credentials.Certificate(jsoncon["filepath"])
    print("vscode")
    firebase_admin.initialize_app(cred, {"databaseURL": jsoncon["databaseurl"]})


dbfs = firestore.client()


scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
json_file_name = important["spreadsheetjson"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
gc = gspread.authorize(credentials)
spreadsheet_url = important["spreadsheeturl"]


@bot.event
async def on_message(message):
    for mention in message.mentions:
        if mention.id == 768372057414565908:
            await message.channel.send("답장받음")

    await bot.process_commands(message)


@bot.event
async def on_ready():
    if testMode == 1:
        channel = bot.get_channel(805826344842952775)
        await channel.send("moa2bot test")
    test.start()
    await bot.change_presence(
        status=discord.Status.online, activity=discord.Game(f"{version} $도움말")
    )


@bot.command()
async def 통계(ctx):
    stat = db.reference(f"servers/server{ctx.guild.id}/users")
    statInfo = stat.get()

    betDict = {}

    for user in statInfo.keys():
        if not "stats" in statInfo[user].keys():
            print(user)
        else:
            if "betting" in statInfo[user]["stats"].keys():
                betStat = statInfo[user]["stats"]["betting"]

                for bet in betStat.keys():
                    realBet = betStat[bet]
                    print(f"{user} {bet} : {realBet}")
                    if f"{bet}_fail" in betDict.keys():
                        betDict[f"{bet}_fail"] += realBet["fail"]
                    else:
                        betDict[f"{bet}_fail"] = realBet["fail"]

                    if f"{bet}_success" in betDict.keys():
                        betDict[f"{bet}_success"] += realBet["success"]
                    else:
                        betDict[f"{bet}_success"] = realBet["success"]

                    print(betDict)

    sendData = "```"
    for key in betDict.keys():
        sendData += f"{key} : {betDict[key]}\n"
    sendData += "```"

    await ctx.send(sendData)


@bot.command()
async def 가입(ctx, nickname):
    random_pool = string.ascii_lowercase + string.digits
    password_pool = random_pool + string.ascii_uppercase
    code = ""
    password = ""

    for i in random.sample(random_pool, 5):
        code += i

    for i in random.sample(password_pool, 15):
        password += i

    direct = user.GetUserInfo(ctx, db)

    result = user.AddNewUser(direct, nickname, code, password)

    if result == 1:
        await ctx.send(f"가입 완료 '[첫 시작]{nickname}#{code}'")
        await ctx.author.send(f"가입 완료, 당신의 비밀번호는 {password}입니다.")
    else:
        await ctx.send(f"이미 가입하였습니다.")


@bot.command()
async def 베팅(ctx, mode=None, moa=10000):
    refer = user.GetUserInfo(ctx, db)

    if refer.get() == None:
        await ctx.send(f"가입이 필요합니다.")
    else:

        money, nickname = user.ReturnInfo(ctx, db)

        if money <= 0:
            await ctx.send("베팅할 모아가 없습니다.")
            return
        if mode == None:
            await ctx.send("모드를 입력해주세요.")
            return

        if int(mode) > 4 or int(mode) < 1:
            await ctx.send("모드를 잘못 입력했습니다.")
            return

        if int(mode) == 4:
            if moa == 10000:
                moa = money
            else:
                await ctx.send("베팅 4는 금액 입력을 할 수 없습니다. 올인만 가능합니다.")
                return

        if money < int(moa) or int(moa) < 0:
            await ctx.send("보유량보다 많거나 0원 이하로 베팅하실 수 없습니다.")
            return

        if todaymoa.CheckToday() == 0:
            bonus = 5
        else:
            bonus = 0

        success, change = betting.DoBet(mode, moa, bonus)

        resultText = {True: f"{nickname} 베팅 성공!", False: f"{nickname} 베팅 실패!"}

        await ctx.send(resultText[success])

        if not success:
            save2 = random.randrange(0, 100)
            if save2 < 10:
                change += math.floor(moa * 0.3)
                await ctx.send("건 돈의 30% 지급")

        betinfo = refer.child("stats").child(f"betting/mode{mode}")
        betdict = betinfo.get()

        if betdict == None:
            if success:
                betinfo.set(
                    {
                        "try": 1,
                        "total": int(moa),
                        "success": 1,
                        "fail": 0,
                        "win": int(moa),
                        "lose": 0,
                    }
                )
            else:
                betinfo.set(
                    {
                        "try": 1,
                        "total": int(moa),
                        "success": 0,
                        "fail": 1,
                        "win": 0,
                        "lose": int(moa),
                    }
                )

            if int(moa) >= 1000000:
                refer.child("titles").update(
                    {str(len(refer.child("titles").get())): 2 + int(mode)}
                )
                await ctx.send(f"{nickname} [누적 100만 베팅 - 모드{mode}] 칭호 획득!")

        else:
            if success:
                betinfo.update(
                    {
                        "try": betdict["try"] + 1,
                        "total": betdict["total"] + int(moa),
                        "success": betdict["success"] + 1,
                        "win": betdict["win"] + int(moa),
                    }
                )
            else:
                betinfo.update(
                    {
                        "try": betdict["try"] + 1,
                        "total": betdict["total"] + int(moa),
                        "fail": betdict["fail"] + 1,
                        "lose": betdict["lose"] + int(moa),
                    }
                )

            if betdict["total"] + int(moa) >= 1000000:
                await GetTitle(ctx, refer.child("titles"), 2 + int(mode), nickname)

        finance.ChangeMoney(refer, change)


@commands.cooldown(1, 30, commands.BucketType.user)
@bot.command()
async def 구걸(ctx):
    doc_ref = user.GetUserInfo(ctx, db)

    doc = doc_ref.get()
    if doc != None:
        getmoa = finance.GetBeggingMoa()

        if todaymoa.CheckToday() == 6:
            getmoa *= 10

        money, nickname = user.ReturnInfo(ctx, db)

        if money > 0:
            await ctx.send("0모아를 가지고 있어야 구걸할수 있습니다.")
            구걸.reset_cooldown(ctx)
            return

        finance.ChangeMoney(user.GetUserInfo(ctx, db), getmoa)

        await ctx.send(f"{nickname} {getmoa}모아 획득!")

    else:
        await ctx.send(f"가입이 필요합니다.")


@구걸.error
async def mine_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = "This command is ratelimited, please try again in {:.2f}s".format(
            error.retry_after
        )
        await ctx.send(msg)
    else:
        raise error


@bot.command()
async def 자산(ctx):
    direct = user.GetUserInfo(ctx, db)

    doc = direct.get()
    if doc != None:
        money = doc["재산"]["money"]
        nickname = doc["nickname"]

        await ctx.send(f"{nickname}의 자산은 {money}모아")
    else:
        await ctx.send(f"가입이 필요합니다.")


@bot.command()
async def 비밀번호(ctx):
    direct = user.GetUserInfo(ctx, db)

    doc = direct.get()
    if doc != None:
        password = doc["password"]

        await ctx.author.send(f"당신의 비밀번호는 {password}")
    else:
        await ctx.send(f"가입이 필요합니다.")


@bot.command()
async def 상자열기(ctx, boxName):
    direct = None
    realLuck = None

    userdir = user.GetUserInfo(ctx, db)
    direct = userdir.child("inventory")

    if userdir.get() == None:
        await ctx.send("가입을 해주세요.")
        return

    if not boxName in direct.get().keys():
        await ctx.send("가지고 있지 않거나 잘못된 이름입니다.")
        return

    money, nickname = user.ReturnInfo(ctx, db)

    if str(boxName).startswith("의문의 물건 상자"):
        unknowndict = direct.child("의문의 물건").get()
        if unknowndict != None:
            await ctx.send("의문의 물건을 가지고 있습니다.")
            return
        cluck = [70, 27, 3]
        bluck = [0, 70, 30]
        aluck = [0, 0, 100]

        if str(boxName).endswith("A"):
            realLuck = aluck
        elif str(boxName).endswith("B"):
            realLuck = bluck
        elif str(boxName).endswith("C"):
            realLuck = cluck

        percent = []

        itemlevel = 0

        percent.clear()
        result = random.random() * 100

        cut = 0

        result = random.random() * 100

        levelcut = [38, 28, 18, 8, 3, 1, 1, 1, 1, 1]
        cut = 0
        levelp = 1

        level10 = 0

        for i in realLuck:
            cut += i
            print(cut)
            print(result)
            if result < cut:
                percent.append(i / 100)
                break
            level10 += 1

        cut = 0

        result = random.random() * 100

        for i in levelcut:
            cut += i
            if result < cut:
                percent.append(i / 100)
                itemlevel = level10 * 10 + levelp
                break
            else:
                levelp += 1

        percentcalc = 0

        percentcalc = percent[0] * percent[1] * 100

        if itemlevel == 30:
            userdir.child("titles").update({str(len(userdir.child("titles").get())): 1})
            await ctx.send(f"{nickname} [완벽을 뽑은 자] 칭호 획득!")

        await ctx.send(
            f"의문의 물건 {itemlevel}강({(format(percentcalc,'''.3f''')).rstrip('0')}%) 획득!"
        )

        inventory.ChangeUnknown(userdir, 1, itemlevel)


@commands.cooldown(1, 4, commands.BucketType.user)
@bot.command()
async def 강화(ctx, level=None):
    maxlevel = 37
    user_ref = user.GetUserInfo(ctx, db)

    unknown_have = reinforce.GetUnknownHave(user_ref)
    unknown_dict = unknown_have.get()

    if level != None:
        level = int(level)
        if level >= maxlevel:
            await ctx.send("강화를 할 수 없는 레벨입니다.")
            return
        prolist = []
        proba = reinforce.GetProbability(int(level))
        prolist.append("성공" + format(proba[0], ".2f"))
        prolist.append("변화없음" + format(proba[1], ".2f"))
        prolist.append("실패" + format(proba[2], ".2f"))
        prolist.append("파괴" + format(proba[3], ".2f"))
        prolist.append("강화 비용" + str(reinforce.GetCost(int(level))))
        await ctx.send(prolist)
        return

    if unknown_have == None:
        await ctx.send("의문의 물건을 가지고 있지 않습니다.")
        return

    level = unknown_dict["level"]

    if level == maxlevel:
        await ctx.send("현재 레벨은 최고 레벨입니다.")
        return

    money, nickname = user.ReturnInfo(ctx, db)

    # 강화 비용을 구한다.
    price = reinforce.GetCost(level)

    if todaymoa.CheckToday() == 2:
        price = math.floor(price * 0.8)

    # 가지고 있는 돈보다 강화 비용이 많으면 강화 불가
    if price > money:
        await ctx.send(f"{price-money}모아가 부족합니다. 강화 비용 : {price}모아")
        return

    # 강화를 한다.
    change = reinforce.DoReinfoce(level)[0]

    reinforceInfo = {0: "아무 변화가 없었다...", 1: "성공!", -1: "실패", -10: "파괴..."}

    if change != -10:
        afterLevel = level + change
    else:
        afterLevel = "destroy"
    await ctx.send(f"{nickname} {reinforceInfo[change]} {level} >> {afterLevel}")

    if change == 1:
        if todaymoa.CheckToday() == 3:
            if level <= 20:
                change += 1
                await ctx.send(f"오늘의 모아봇 적용 {afterLevel} >> {afterLevel+1}")
        await asyncio.sleep(2)
        result = random.random() * 100
        if result < 20:
            plus = 0
            if todaymoa.CheckToday() == 1:
                change = 3
                plus = 2
            else:
                change = 2
                plus = 1
            await ctx.send(f"크리티컬 강화 성공!! {afterLevel} >> {afterLevel+plus}")

    # change값에 따라 db를 바꾼다. 단, change가 0이면 바꾸지 않는다.

    if change != -10:
        inventory.ChangeUnknown(user_ref, 1, level + change)
    else:
        inventory.ChangeUnknown(user_ref, 2)

    # 현재 가지고 있는 돈에서 강화비용을 빼고 firebase에 올린다.
    finance.ChangeMoney(user_ref, -price)


@강화.error
async def rein_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = "This command is ratelimited, please try again in {:.2f}s".format(
            error.retry_after
        )
        await ctx.send(msg)
    else:
        raise error


@bot.command()
async def 코인(ctx, coinnName=None, mode=None, amount=None):
    try:
        await ctx.send("현재 이용할 수 없습니다.")
        return
        coin_ref = db.reference("coins")

        selectCoin_ref = None
        user_info = None
        money = None
        turn = None
        user_turn = None

        coindata = None

        if coinnName != None:
            selectCoin_ref = coin_ref.child(coinnName)
            coindata = selectCoin_ref.get()
        else:
            docs = coin_ref.get()
            embed = discord.Embed(title=f"코인 현황")

            for doc in docs.keys():
                embed.add_field(
                    name=doc, value=f"{docs[doc]['price']}\n{docs[doc]['last']}"
                )
            await ctx.send(embed=embed)
            return

        cantrade = coindata["cantrade"]

        price = coindata["price"]

        user_ref = db.reference(
            f"servers/server{ctx.guild.id}/users/user{ctx.author.id}"
        )
        fin_ref = user_ref.child("재산")
        coin_ref = fin_ref.child("coins")
        coinDict = coin_ref.get()

        money, nickname = user.ReturnInfo(ctx, db)

        if coinDict == None:
            have = 0
        else:
            have = coinDict[f"{coinnName}"]

            print(coinDict)

            if f"{coinnName}_turn" in coinDict.keys():
                user_turn = coinDict[f"{coinnName}_turn"]
            else:
                user_turn = 1

        if mode == None:
            strike = coindata["strike"]
            last = coindata["last"]

            if price <= 0:
                await ctx.send(f"상장폐지로 인해 가격을 확인할수 없습니다.")
            else:
                await ctx.send(f"현재 가격 : {price} 연속 상승 횟수 : {strike} 가격 변화 : {last}")
            return

        if not cantrade:
            await ctx.send("거래를 할수없는 시간입니다.(거래 가능 시간 : 오전 10시 ~ 오후 10시)")
            return

        turn = coindata["turn"]
        user_turn = coindata["turn"]

        if turn > user_turn and have > 0:
            await ctx.send(f"가지고 있던 {turn}번째 {coinnName}이 상장폐지가 되었습니다.")
            coin_ref.set(
                {
                    f"{coinnName}": 0,
                    f"{coinnName}_turn": turn,
                },
                merge=True,
            )
            return

        amount = int(amount)

        if mode == "buy":
            if not cantrade:
                return
            if money >= amount * price:
                # 구매한다
                coin_ref.update(
                    {
                        f"{coinnName}": have + amount,
                        f"{coinnName}_turn": turn,
                    }
                )

                # 모아를 깎게 바꿈
                fin_ref.update({"money": money - price * amount})

                await ctx.send(f"moacoin {amount}개 구입 완료 {have+amount}개 보유중")
            else:
                await ctx.send(f"{amount*price-money}모아가 부족합니다.")

        elif mode == "sell":
            if coinDict == None:
                have = 0
            else:
                have = coinDict["moacoin"]

            if amount > have:
                await ctx.send(f"코인이 {amount-have}개 부족합니다. {have}개 보유중")
                return

            coin_ref.update(
                {
                    f"{coinnName}": have - amount,
                    f"{coinnName}_turn": turn,
                }
            )

            fin_ref.update({"money": money + price * amount})

            await ctx.send(f"moacoin {amount}개 판매 완료 {have-amount}개 보유중")

        else:
            await ctx.send("모드를 buy 또는 sell로 입력해주세요.")
            return
    except:
        await ctx.send(f"$코인 (코인 이름) (buy or sell) (수량)")


async def GetTitle(ctx, refer, num, nickname):
    usertitle = refer.get()
    usertitlenum = len(usertitle)
    if not int(num) in usertitle:
        refer.update({str(usertitlenum): num})
        await ctx.send(f"{nickname}  {db.reference('titles').get()[num]} 칭호 획득!")


@tasks.loop(seconds=10)
async def test():
    date = datetime.datetime.now()

    # 오전 10시~오후 10시 59분 인지 체크
    if date.hour >= 10 and date.hour <= 22:
        if date.hour == 20 and date.minute != 0:
            return

        coin_ref = db.reference("coins/moacoin")

        coin_info = coin_ref.get()

        price = 0
        turn = 0

        if not coin_info == None:
            cantrade = coin_info["cantrade"]
            price = coin_info["price"]
            strike = coin_info["strike"]
            maxprice = coin_info["maxprice"]
            minprice = coin_info["minprice"]
            turn = coin_info["turn"]
        else:
            turn = 0

        if (
            date.hour == 10
            and date.minute == 0
            and date.second >= 0
            and date.second < 10
        ):
            if coin_info == None or price <= 0:
                coin_ref.update(
                    {
                        "price": 20000,
                        "minprice": 20000,
                        "maxprice": 20000,
                        "strike": 0,
                        "last": 0,
                        "cantrade": True,
                        "turn": turn + 1,
                    }
                )
            else:
                coin_ref.update({"cantrade": True})
            return
        elif coin_ref.get() == None:
            return

        if (
            date.hour == 22
            and date.minute == 0
            and date.second >= 0
            and date.second < 10
        ):
            coin_ref.update({"cantrade": False})
            return

        if (
            date.hour >= 12
            and date.hour <= 20
            and date.minute % 20 == 0
            and strike != 30
            and date.second >= 0
            and date.second < 10
        ) and cantrade:

            udnum = 37
            udchan = 1.8

            up = udnum - strike * udchan
            down = udnum + strike * udchan
            destroy = abs(strike) * 1.03 + 0.8
            notchange = 100 - up - down - destroy

            result = None

            amount = 0
            cut = 0

            for i in range(10):
                result = random.random() * 100
                cut += 19 - i * 2

                if result < cut:
                    jump = random.random() * 4.9 + 0.1
                    amount = math.floor((i + 1) * 100 * jump)
                    print(amount)
                    break

            result = random.random() * 100
            print(result)

            if result < up:
                print(f"{amount}모아 상승 현재 가격 : {price+amount}")
                if strike <= 0:
                    strike = 1
                else:
                    strike += 1
                price += amount
            elif result < up + notchange:
                print(f"변화 없음")
                amount = 0
                strike = 0
            elif result < up + notchange + down:
                print(f"{amount}모아 하락 현재 가격 : {price-amount}")
                price -= amount
                amount = -amount
                if strike >= 0:
                    strike = -1
                else:
                    strike -= 1
            else:
                price = -50000

            if price <= 0:
                strike = -30
                cantrade = False
                print(f"상장 폐지")

            if price > maxprice:
                maxprice = price

            if price < minprice:
                minprice = price

            coin_ref.update(
                {
                    "strike": strike,
                    "price": price,
                    "last": amount,
                    "minprice": minprice,
                    "maxprice": maxprice,
                    "cantrade": cantrade,
                }
            )


@bot.command()
async def 상점(ctx, itemName=None, amount=1):
    store_ref = db.reference(f"servers/server{ctx.guild.id}/store")

    storeInfo = store_ref.get()

    curVersion = db.reference("version").get()["store"]

    await store.UseStore(
        store_ref, storeInfo, curVersion, ctx, itemName, db, user, amount
    )


def Additem(itemName):
    return


@bot.command()
async def 건의(ctx):
    user1 = user.GetUserInfo(ctx, db)

    if user1.get() == None:
        await ctx.send("가입을 해야 건의를 할 수 있습니다.")
        return

    channel = bot.get_channel(809830797082624020)
    feedback = str(ctx.message.content).replace("$건의 ", "")

    if len(feedback) > 40:
        await ctx.send("40글자 미만으로 보내주세요.")
        return
    await channel.send(
        f"```{feedback}\nserver : {ctx.guild.id}\nuser : {ctx.author.id}```"
    )


@bot.command()
async def 기부(ctx, userid=None, moa=None):
    if userid == None:
        await ctx.send("기부할 유저의 id")
        return

    if moa == None:
        await ctx.send("기부할 모아")
        return

    server = db.reference(f"servers/server{ctx.guild.id}")

    givedir = server.child(f"users/user{ctx.author.id}")

    giveuser = givedir.get()

    receivedir = server.child(f"users/user{userid}")

    receiveUser = receivedir.get()

    if receiveUser == None:
        await ctx.send("가입을 하지 않은 유저의 id입니다.")
        return

    if ctx.author.id == int(userid):
        await ctx.send("자기 자신한테 기부 할 수 없습니다.")
        return

    if int(moa) > giveuser["재산"]["money"]:
        await ctx.send("모아가 부족합니다.")
        return

    # 기부 통계 작성 코드
    receiveData = receivedir.child("stats/donation").get()
    giveData = givedir.child("stats/donation").get()

    if receiveData == None:
        receivedir.child("stats/donation").set({"receive": 1, "totalreceive": int(moa)})
    else:
        if "receive" in receiveData.keys():
            receivedir.child("stats/donation").update(
                {
                    "receive": receiveData["receive"] + 1,
                    "totalreceive": receiveData["totalreceive"] + int(moa),
                }
            )
        else:
            receivedir.child("stats/donation").update(
                {
                    "receive": 1,
                    "totalreceive": int(moa),
                }
            )

    if giveData == None:
        givedir.child("stats/donation").set({"give": 1, "totalgive": int(moa)})
    else:
        if "give" in receiveData.keys():
            givedir.child("stats/donation").update(
                {
                    "give": giveData["give"] + 1,
                    "totalgive": giveData["totalgive"] + int(moa),
                }
            )
        else:
            receivedir.child("stats/donation").update(
                {
                    "give": 1,
                    "totalgive": int(moa),
                }
            )

    server.child(f"users/user{ctx.author.id}/재산").update(
        {"money": giveuser["재산"]["money"] - int(moa)}
    )
    server.child(f"users/user{userid}/재산").update(
        {"money": receiveUser["재산"]["money"] + int(moa)}
    )

    giveinfo = f"{giveuser['nickname']}, {receiveUser['nickname']}에게 {moa}모아 기부완료"

    await ctx.send(giveinfo)


@bot.command()
async def 칭호(ctx, setn=None):
    allTitles = db.reference("titles").get()
    user1 = user.GetUserInfo(ctx, db)
    userTitles = user1.child("titles").get()

    if setn == None:
        for title in userTitles:
            await ctx.send(allTitles[title])
    else:
        change = re.sub(
            r"\[.+\]",
            f"[{allTitles[userTitles[int(setn)]]}]",
            user1.get()["nickname"],
        )
        db.reference(f"servers/server{ctx.guild.id}/users/user{ctx.author.id}").update(
            {"nickname": change}
        )

        await ctx.send(f"{change}로 변경 완료")


@bot.command()
async def 의문의물건구매(ctx, level=None):
    user1 = user.GetUserInfo(ctx, db)
    unknown_have = reinforce.GetUnknownHave(user1).get()
    realPrice = 0
    wantString = None

    priceDict = {}
    unknown_trade = db.reference("unknown_trade")

    unknown_trade_dict = unknown_trade.get()

    for key in unknown_trade_dict.keys():
        templevel = unknown_trade_dict[key].split("_")[0]
        tempprice = int(unknown_trade_dict[key].split("_")[1])
        if templevel in priceDict.keys():
            if priceDict[f"level{templevel}"] > tempprice:
                priceDict[f"level{templevel}"] = tempprice

                if level != None:
                    if templevel == level:
                        realPrice = tempprice
                        wantString = key
                        print(wantString)
        else:
            priceDict[f"level{templevel}"] = tempprice

            if level != None:
                if templevel == level:
                    realPrice = tempprice
                    wantString = key
                    print(wantString)

    if level == None:
        for level in priceDict.keys():
            await ctx.send(f"{level}의 최저가 : {priceDict[level]}")

        return

    if unknown_have != None:
        await ctx.send("의문의 물건을 가지고 있습니다.")
        return

    if f"level{level}" in priceDict.keys():

        result, need = finance.ChangeMoney(user1, -realPrice)

        if result == -1:
            await ctx.send(f"{need} 모아가 부족합니다.")
        else:

            sellUser = wantString.split("_")
            userRef = db.reference(
                f"servers/server{sellUser[1]}/users/user{sellUser[2]}"
            ).child("재산")
            userRef.update({"money": userRef.get()["money"] + realPrice})
            await ctx.send(f"level{level}의 최저가 {realPrice} 모아에 구매완료")
            unknown_trade.update({wantString: None})
            inventory.ChangeUnknown(user1, 1, int(level))
            servername = bot.get_guild(int(sellUser[1])).name
            await bot.get_user(int(sellUser[2])).send(
                f"{servername}에서 올린 의문의 물건 {level}강이 팔려 {realPrice}모아가 지급되었습니다."
            )
    else:
        await ctx.send("재고 없음")


@commands.cooldown(1, 10, commands.BucketType.user)
@bot.command()
async def 의문의물건판매(ctx, price=None):
    now = datetime.datetime.now()
    if ctx.guild.id == 712186772846542889:
        await ctx.send("여기서 판매 허용하면 경제 망가진다 ㄹㅇ ㅋㅋ")
        return

    if price == None:
        await ctx.send("판매할 가격을 입력해주세요.")
        return

    year = now.year
    month = "%02d" % now.month
    day = "%02d" % now.day

    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    second = "%02d" % now.second

    user_ref = user.GetUserInfo(ctx, db)

    unknown_have = reinforce.GetUnknownHave(user_ref)
    unknown_dict = unknown_have.get()

    level = unknown_dict["level"]

    if level == 30:
        await ctx.send(f"더이상 강화를 할 수 없어 거래시장에 올릴 수 없습니다. 추후 방안에 대해 고민하겠습니다.")
        return

    inventory.ChangeUnknown(user_ref, 2)

    unknown_trade = db.reference("unknown_trade")

    unknown_trade.update(
        {
            f"{year}{month}{day}{hour}{minute}{second}_{ctx.guild.id}_{ctx.author.id}": f"{level}_{price}"
        }
    )

    await ctx.send("판매 완료, 다른사람이 구매시 모아가 들어옵니다.")


@bot.command()
async def 보유현황(ctx):
    user1 = user.GetUserInfo(ctx, db)

    sendText = inventory.GetInventory(user1)

    await ctx.send(sendText)


@bot.command()
async def 투표(ctx, subject, *select):
    print(select)
    if subject == None:
        await ctx.send("투표 주제를 입력해주세요.")
        return

    if len(select) == 0:
        message = await ctx.send(ctx.message.content.replace("$투표 ", ""))
        await message.add_reaction("👍")
        await message.add_reaction("👎")
    else:
        if len(select) > 6:
            await ctx.send("최대 6개까지 설정가능합니다.")
            return
        count = 0
        sendmsg = f"{subject}\n"
        emojis = ["👍", "✌️", "👩‍👦‍👦", "🍀", "🖐️", "🎲"]
        for sel in select:
            sendmsg += f"{emojis[count]} {sel}\n"
            count += 1
        message = await ctx.send(sendmsg)
        for i in range(count):
            await message.add_reaction(emojis[i])


@bot.command()
async def 도움말(ctx):
    helptext = "```"
    for command in bot.commands:
        helptext += f"${command}\n"
    helptext += "```"
    await ctx.send(helptext)


@bot.command()
async def 모두(ctx):
    users = db.reference(f"servers/server{ctx.guild.id}/users")

    sendText = user.GetAllServerUser(users)

    await ctx.send(sendText)


@bot.command()
async def 주사위(ctx, mode=None, money=None):
    now = datetime.datetime.now()
    result = random.randint(1, 100)
    if mode == None:
        await ctx.send(result)
    elif int(mode) == 1:
        users = user.GetUserInfo(ctx, db)
        if users.get() == None:
            await ctx.send("가입을 해주세요.")
            return

        today = users.child("today").get()

        if todaymoa.CheckToday() == 5:
            multiple = 12
        else:
            multiple = 1

        if today == None:
            await UpdateDice(ctx, users, result, multiple, now)
        else:
            if "dice" in today.keys():
                if (
                    users.child("today").get()["dice"]
                    == f"{now.year}-{now.month}-{now.day}"
                ):
                    await ctx.send("하루 1회만 가능합니다.")
                    return
                else:
                    await UpdateDice(ctx, users, result, multiple, now)
            else:
                await UpdateDice(ctx, users, result, multiple, now)


async def UpdateDice(ctx, users, result, multiple, now):
    users.child("today").update({"dice": f"{now.year}-{now.month}-{now.day}"})
    finance.ChangeMoney(users, result * 10000 * multiple)
    await ctx.send(f"결과 : {result}, {result*10000*multiple}모아 획득!")


@bot.command()
async def 오늘의모아봇(ctx):
    await ctx.send(todaymoa.GetToday())


@bot.command()
async def 버전(ctx):
    await ctx.send(version)


@bot.command()
async def 운영자지급(ctx, server, user, moa):
    if ctx.author.id == 382938103435886592:
        user = db.reference(f"servers/server{server}/users/user{user}")

        finance.ChangeMoney(user, moa)

        discordServer = bot.get_guild(int(server))

        await ctx.send(f"{discordServer.name}의 {user.get()['nickname']}에게 {moa}모아 지급")
    else:
        await ctx.send("운영자가 아닙니다.")


freeReinCooldown = []


@bot.command()
async def 무료강화(ctx, Info=None):
    if ctx.author.id in freeReinCooldown:
        await ctx.message.delete()
        return

    user1 = user.GetUserInfo(ctx, db).get()

    if Info == "순위":
        forNickname = db.reference(f"servers/server{ctx.guild.id}/users")
        forRank = db.reference(f"free_reinforce/server{ctx.guild.id}").get()

        reinInfo = {}

        for user2 in forRank.keys():
            userInfo = forNickname.child(user2).get()
            if userInfo == None:
                continue
            nickname = userInfo["nickname"]
            nickname = re.sub(r"\[.+\]", r"", nickname)
            reinInfo[nickname] = forRank[user2]["level"]

        sortedDict = sorted(reinInfo.items(), reverse=True, key=lambda item: item[1])

        sendtext = "```"

        for key, value in sortedDict:
            sendtext += f"{key} : {value}\n"

        sendtext += "```"

        await ctx.send(sendtext)
        return

    if user1 == None:
        await ctx.send("가입을 해주세요.")
        return

    resultInfo = {1: "success", 0: "fail"}

    maxlevel = 50
    freereinDB = db.reference(
        f"free_reinforce/server{ctx.guild.id}/user{ctx.author.id}"
    )
    reinData = freereinDB.get()
    if reinData == None:
        if todaymoa.CheckToday() == 4:
            freereinDB.update({f"level": 2, "fail": 0})
        else:
            freereinDB.update({f"level": 1, "fail": 0})
        await ctx.send("강화 0>1 성공!")
    else:
        level = reinData[f"level"]
        if level == maxlevel:
            await ctx.send("최고레벨입니다.")
            return
        change, success, bonus = reinforce.DoReinfoce(level, 2, reinData["fail"])
        if change != -10:
            if change == 1:
                if todaymoa.CheckToday() == 4:
                    freereinDB.update({f"level": level + 2, "fail": 0})
                else:
                    freereinDB.update({f"level": level + 1, "fail": 0})

            else:
                freereinDB.update({f"fail": reinData["fail"] + 1})
        else:
            freereinDB.update({f"level": None, "fail": None})
        await ctx.send(
            f"{level} >> {int(level)+1}   {reinData['fail']+1}트의 결과 : **{resultInfo[change]}** (성공확률 : {'{0:.2f}'.format(success)}%  강화의 기운 : {'{0:.2f}'.format(bonus)}%)"
        )
        freeReinCooldown.append(ctx.author.id)
        msg = await ctx.send(f"쿨타임 {'{0:.2f}'.format(level*0.2)}초 걸림")

        if change == 1:
            userdb = db.reference(
                f"servers/server{ctx.guild.id}/users/user{ctx.author.id}"
            )
            if level + change == 15:
                finance.ChangeMoney(userdb, 3000000)
                await ctx.send("300만 모아")
            elif level + change == 30:
                finance.ChangeMoney(userdb, 15000000)
                await ctx.send("1500만 모아")
            elif level + change == 50:
                finance.ChangeMoney(userdb, 500000000)
                await ctx.send("5억 모아")

        await asyncio.sleep(level * 0.2)
        freeReinCooldown.remove(ctx.author.id)
        await msg.delete()


bot.run(token)
