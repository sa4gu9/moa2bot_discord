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

from modules import finance, betting, reinforce, result_bet

from bs4 import BeautifulSoup
import requests


version = "V2.21.03.21"

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

    direct = GetUserInfo(ctx)

    if direct.get() == None:

        firstData = {
            "nickname": f"[첫 시작]{nickname}#{code}",
            "titles": [0],
            "password": password,
        }

        direct.set(firstData)

        direct = direct.child("재산")
        direct.set({"money": 200000})

        await ctx.send(f"가입 완료 '[첫 시작]{nickname}#{code}'")
        await ctx.author.send(f"가입 완료, 당신의 비밀번호는 {password}입니다.")
    else:
        await ctx.send(f"이미 가입하였습니다.")
        return


@bot.command()
async def 베팅(ctx, mode=None, moa=10000):
    refer = GetUserInfo(ctx)

    if refer.get() == None:
        await ctx.send(f"가입이 필요합니다.")
    else:

        money, nickname = ReturnInfo(ctx)

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

        if CheckToday() == 0:
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

        ChangeMoney(ctx, money, change)


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


@commands.cooldown(1, 30, commands.BucketType.user)
@bot.command()
async def 구걸(ctx):
    doc_ref = GetUserInfo(ctx)

    doc = doc_ref.get()
    if doc != None:
        getmoa = GetBeggingMoa()

        if CheckToday() == 6:
            getmoa *= 10

        money, nickname = ReturnInfo(ctx)

        if money > 0:
            await ctx.send("0모아를 가지고 있어야 구걸할수 있습니다.")
            구걸.reset_cooldown(ctx)
            return

        ChangeMoney(ctx, money, getmoa)

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
    direct = GetUserInfo(ctx)

    doc = direct.get()
    if doc != None:
        money = doc["재산"]["money"]
        nickname = doc["nickname"]

        await ctx.send(f"{nickname}의 자산은 {money}모아")
    else:
        await ctx.send(f"가입이 필요합니다.")


@bot.command()
async def 비밀번호(ctx):
    direct = GetUserInfo(ctx)

    doc = direct.get()
    if doc != None:
        password = doc["password"]

        await ctx.author.send(f"당신의 비밀번호는 {password}")
    else:
        await ctx.send(f"가입이 필요합니다.")


@bot.command()
async def 상자열기(ctx, boxName, amount=1):
    if int(amount) > 10:
        await ctx.send("10개를 넘겨서 열수 없습니다.")
        return
    direct = None
    realLuck = None

    userdir = GetUserInfo(ctx)
    direct = userdir.child("inventory").get()

    if userdir.get() == None:
        await ctx.send("가입을 해주세요.")
        return

    if not boxName in direct.keys():
        await ctx.send("가지고 있지 않거나 잘못된 이름입니다.")
        return
    else:
        if direct[boxName] - int(amount) >= 0:
            if direct[boxName] - int(amount) == 0:
                userdir.child("inventory").update({boxName: None})
            else:
                userdir.child("inventory").update(
                    {boxName: direct[boxName] - int(amount)}
                )
        else:
            await ctx.send("부족")
            return

    for i in range(int(amount)):

        money, nickname = ReturnInfo(ctx)

        if str(boxName).startswith("의문의 물건 상자"):
            cluck = [60, 30, 10]
            bluck = [0, 80, 20]
            aluck = [0, 0, 100]

            if str(boxName).endswith("A"):
                realLuck = aluck
            elif str(boxName).endswith("B"):
                realLuck = bluck
            elif str(boxName).endswith("C"):
                realLuck = cluck

            percent = []

            itemgrade = 0
            itemlevel = 0

            minlevel = [1, 10, 20]
            maxlevel = [10, 20, 30]

            percent.clear()
            result = random.random() * 100

            cut = 0
            itemgrade = 0
            currentGrade = 0

            for currentCut in realLuck:
                cut += currentCut
                itemgrade += 1

                if result < cut:
                    currentGrade = itemgrade
                    percent.append(currentCut / 100)
                    break

            result = random.random() * 100

            levelcut = [40, 23, 17, 11, 5, 3]
            cut = 0
            levelp = 0

            for i in levelcut:
                cut += i
                if result < cut:
                    percent.append(i / 100)
                    itemlevel = minlevel[itemgrade - 1] + levelp
                    break
                else:
                    levelp += 1

            if levelp == 6:
                percent.append(0.01)
                percent.append(
                    maxlevel[itemgrade - 1] - (minlevel[itemgrade - 1] + levelp) + 1
                )
                itemlevel = random.randint(
                    minlevel[itemgrade - 1] + levelp, maxlevel[itemgrade - 1]
                )

            percentcalc = 0

            if len(percent) == 2:
                percentcalc = percent[0] * percent[1] * 100
            elif len(percent) == 3:
                percentcalc = percent[0] * percent[1] / percent[2] * 100

            if itemlevel == 30 and itemgrade == 6:
                userdir.child("titles").update(
                    {str(len(userdir.child("titles").get())): 1}
                )
                await ctx.send(f"{nickname} [완벽을 뽑은 자] 칭호 획득!")

            await ctx.send(
                f"의문의 물건 등급{itemgrade} {itemlevel}강({(format(percentcalc,'''.3f''')).rstrip('0')}%) 획득!"
            )

            GetUnknown(userdir, itemgrade, itemlevel)


def CheckToday():
    print(datetime.datetime.now().weekday())
    return datetime.datetime.now().weekday()


@bot.command()
async def 강화(ctx, grade=None, level=None):
    try:
        user_ref = GetUserInfo(ctx)
        minlevel = [1, 10, 20]
        maxlevel = [10, 20, 30]

        if grade == "destroy":
            unknown_have = reinforce.GetUnknown(user_ref, "/destroy")
            unknown_dict = unknown_have.get()

            if await checkunknown(unknown_have, ctx) == -1:
                return

            embed = discord.Embed(title=f"보유중인 파괴 된 의문의 물건")

            for i in unknown_dict.keys():
                embed.add_field(name=f"{i}", value=unknown_dict[i])
            await ctx.send(embed=embed)
            return

        grade = int(grade)

        if grade < 1 or grade > 3:
            await ctx.send("의문의 물건은 1~3등급입니다.")

        unknown_have = reinforce.GetUnknown(user_ref, f"/등급{grade}")
        destroy_have = reinforce.GetUnknown(user_ref, "/destroy")

        unknown_dict = unknown_have.get()
        destroy_dict = destroy_have.get()

        if await checkunknown(unknown_dict, ctx) == -1:
            return

        if level == None:
            # 보유중인 의문의 물건을 보여줌
            embed = discord.Embed(title=f"보유중인 의문의 물건 등급{grade}")

            for i in unknown_have.keys():
                embed.add_field(name=f"{i}", value=unknown_have[i])
            await ctx.send(embed=embed)

        else:
            level = int(level)

            if level < minlevel[grade - 1] and grade >= 2 and grade <= 3:
                await ctx.send(
                    f"등급{grade}는 최소레벨이 {minlevel[grade - 1]}이므로 {level}이 {minlevel[grade - 1]}이 되었습니다."
                )
                unknown_have.update({f"레벨{level}": unknown_dict[f"레벨{level}"] - 1})

                if f"레벨{minlevel[grade - 1]}" in unknown_dict.keys():
                    unknown_have.update(
                        {
                            f"레벨{minlevel[grade - 1]}": unknown_dict[
                                f"레벨{minlevel[grade - 1]}"
                            ]
                            + 1
                        }
                    )
                else:
                    unknown_have.update({f"레벨{minlevel[grade - 1]}": 1})

                return

            if level > maxlevel[grade - 1] or level < minlevel[grade - 1]:
                await ctx.send(
                    f"등급{grade}는 {minlevel[grade-1]}강이상 +{maxlevel[grade-1]}강이하 입니다."
                )

                return

            if f"레벨{level}" in unknown_have.keys():
                if level == maxlevel[grade - 1]:
                    if grade < 3:
                        await ctx.send("현재 레벨은 현재 등급의 최고 레벨입니다. 등급업을 해주세요.")
                        return
                    elif grade == 3:
                        await ctx.send("최고 등급의 최고 레벨은 강화를 할 수 없습니다.")
                        return

                money, nickname = ReturnInfo(ctx)

                # 강화 비용을 구한다.
                price = math.floor(1000 * ((50 * level) ** (0.05 * level)))

                if CheckToday() == 2:
                    price = math.floor(price * 0.8)
                    print(price)

                # 가지고 있는 돈보다 강화 비용이 많으면 강화 불가
                if price > money:
                    await ctx.send(f"{price-money}모아가 부족합니다. 강화 비용 : {price}모아")
                    return

                # 강화를 한다.
                change = reinforce.DoReinfoce(level)

                reinforceInfo = {0: "아무 변화가 없었다...", 1: "성공!", -1: "실패", -10: "파괴..."}

                await ctx.send(reinforceInfo[change])

                if change == 1:
                    await asyncio.sleep(3)
                    result = random.random() * 100
                    if result < 20:
                        result = random.random() * 100
                        change = 2
                        await ctx.send(f"크리티컬 강화 성공!!")

                if change == -10:
                    des_dict = destroy_have.get()
                    if des_dict == None:
                        destroy_have.set({f"등급{grade}": 1})
                    else:
                        if grade != 1:
                            if f"등급{grade}" in des_dict.keys():
                                des_dict[f"등급{grade}"] += 1
                            else:
                                des_dict[f"등급{grade}"] = 1

                            destroy_have.set(des_dict)

                # change값에 따라 dictionary를 바꾼다. 단, change가 0이면 바꾸지 않는다.
                print(unknown_have)

                unknown_have[f"레벨{level}"] -= 1

                if unknown_have[f"레벨{level}"] == 0:
                    del unknown_have[f"레벨{level}"]

                if change != 0 and change != -10:
                    if f"레벨{level+change}" in unknown_have.keys():
                        unknown_have[f"레벨{level+change}"] += 1
                    else:
                        unknown_have[f"레벨{level+change}"] = 1

                print(unknown_have)

                # 현재 가지고 있는 돈에서 강화비용을 빼고 firebase에 올린다.
                ChangeMoney(ctx, money, -price)

                # 바꾼 dictionary를 firebase에 올린다. 단, change가 0이면 바꾸지 않는다.
                if change != 0:
                    user_ref.child("inventory").child("의문의 물건").child(f"등급{grade}").set(
                        unknown_have
                    )

            else:
                await ctx.send("입력한 레벨의 의문의 물건을 가지고 있지 않습니다.")

    except Exception as e:
        await ctx.send("의문의 물건 등급 또는 레벨을 숫자로 입력해주세요.")
        print(e)


@bot.command()
async def 코인(ctx, coinnName=None, mode=None, amount=None):
    try:
        # await ctx.send("현재 이용할 수 없습니다.")
        # return
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

        money, nickname = ReturnInfo(ctx)

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


def ReturnInfo(ctx):
    refer = GetUserInfo(ctx)

    userinfo = refer.get()

    money = userinfo["재산"]["money"]
    nickname = userinfo["nickname"]

    return money, nickname


def ChangeMoney(ctx, money, change):
    userinfo = GetUserInfo(ctx).child("재산")

    if change < 0:
        if abs(change) > money:
            return -1

    userinfo.update({"money": money + change})


@bot.command()
async def 상점(ctx, itemName=None, amount=1):
    store_ref = db.reference(f"servers/server{ctx.guild.id}/store")

    storeInfo = store_ref.get()

    curVersion = db.reference("version").get()["store"]

    if storeInfo == None:
        StoreReset(store_ref, curVersion, ctx)

    if "version" in storeInfo.keys():
        version = storeInfo["version"]

        if version < curVersion:
            StoreReset(store_ref, curVersion, ctx)
            await ctx.send("상점이 갱신되었습니다.")
            return
    else:
        StoreReset(store_ref, curVersion, ctx)
        await ctx.send("상점이 갱신되었습니다.")
        return

    if itemName == None:
        storeInfo = store_ref.get()
        for key in storeInfo.keys():
            if key == "version":
                continue
            await ctx.send(
                f"{key}:{storeInfo[key]['price']}모아 {storeInfo[key]['amount']}개 남음"
            )
        return
    else:
        if store_ref.child(itemName).get() == None:
            await ctx.send("상점에 없는 아이템입니다.")
        else:
            userInfo = GetUserInfo(ctx)
            money, nickname = ReturnInfo(ctx)

            if int(amount) > storeInfo[itemName]["amount"]:
                await ctx.send("매진이거나 남은수량보다 많이 살 수 없습니다.")
                return

            totalPrice = storeInfo[itemName]["price"] * amount
            have = 0
            if money >= totalPrice:
                # 아이템 보유 정보
                userInfo = GetUserInfo(ctx)
                userInfo.child("재산").update({"money": money - totalPrice})
                inventoryInfo = userInfo.child("inventory").get()
                store_ref.child(itemName).update(
                    {"amount": storeInfo[itemName]["amount"] - amount}
                )
                if inventoryInfo == None:
                    userInfo.child("inventory").update({itemName: amount})
                else:

                    if itemName in userInfo.child("inventory").get().keys():
                        have = userInfo.child("inventory").get()[itemName]
                        userInfo.child("inventory").update({itemName: have + amount})
                    else:
                        userInfo.child("inventory").update({itemName: amount})

                await ctx.send(f"{nickname} {itemName} 구매 완료, {have+amount}개 보유중")
            else:
                await ctx.send(f"{totalPrice-money}모아가 부족합니다.")


def Additem(itemName):
    return


@bot.command()
async def 등급업(ctx, grade=None, level=None):

    user_ref = GetUserInfo(ctx)
    minlevel = [1, 10, 20]

    if grade == "3":
        await ctx.send("최고등급입니다.")
        return

    unknown_have = reinforce.GetUnknown(user_ref, f"/등급{grade}")
    unknown_dict = unknown_have.get()
    if await checkunknown(unknown_dict, ctx) == -1:
        return

    # 레벨의 물건을 가지고 있는지, 그것의 레벨이 다음단계의 최소 단계를 이상인지 체크한다
    if f"레벨{level}" in unknown_dict.keys():
        price = 7000
        if int(level) >= minlevel[int(grade)]:
            result, need = finance.ChangeMoney(user_ref, -price)

            if result == -1:
                await ctx.send(f"{need}모아가 부족합니다.")
                return

            up_percent = [4, 0.5]
            dice = random.random() * 100

            upgradeCut = up_percent[int(grade) - 1]

            if CheckToday() == 3:
                upgradeCut *= 2

            if dice < upgradeCut:

                # 의문의 물건 보유 정보 수정
                unknown_dict[f"레벨{level}"] -= 1
                if unknown_dict[f"레벨{level}"] == 0:
                    user_ref.child(f"inventory/의문의 물건/등급{grade}").update(
                        {f"레벨{level}": None}
                    )

                # 등급업한 의문의 물건 데이터 반영
                upgrade_have = user_ref.child(
                    f"inventory/의문의 물건/등급{int(grade)+1}"
                ).get()

                if upgrade_have == None:
                    user_ref.child(f"inventory/의문의 물건/등급{int(grade)+1}").update(
                        {f"레벨{level}": 1}
                    )
                else:
                    if f"레벨{level}" in upgrade_have.keys():
                        user_ref.child(f"inventory/의문의 물건/등급{int(grade)+1}").update(
                            {f"레벨{level}": upgrade_have[f"레벨{level}"] + 1}
                        )
                    else:
                        user_ref.child(f"inventory/의문의 물건/등급{int(grade)+1}").update(
                            {f"레벨{level}": 1}
                        )

                giveItemName = "의문의 물건 판매가격 30% 증가권"
                inventory = user_ref.child("inventory").get()

                if giveItemName in inventory.keys():
                    user_ref.child("inventory").update(
                        {giveItemName: inventory[giveItemName] + 1}
                    )
                else:
                    user_ref.child("inventory").update({giveItemName: 1})

                await ctx.send(f"success! {giveItemName} 지급!")

                giveMoney = price * (200 // up_percent[int(grade) - 1])

                user_ref.child("재산").update(
                    {"money": user_ref.child("재산").get()["money"] + giveMoney}
                )

                await ctx.send(f"등급업 성공 보상으로 {giveMoney}모아 지급")

            else:
                await ctx.send("fail")
        else:
            await ctx.send(
                f"등급업이 가능한 레벨이 아닙니다. 등급{grade} 레벨{minlevel[int(grade)]}이상 가능"
            )
            return
    else:
        await ctx.send("해당 레벨의 의문의 물건을 가지고 있지 않습니다.")
        return


def GetUserInfo(ctx):
    return db.reference(f"servers/server{ctx.guild.id}/users/user{ctx.author.id}")


def StoreReset(ref, curVersion, ctx):
    ref.child("의문의 물건 등급업 주문서").set({"price": 3000, "amount": 300})
    ref.child("의문의 물건 상자 C").set({"price": 35000, "amount": 1000})
    ref.child("의문의 물건 상자 B").set({"price": 300000, "amount": 500})
    ref.child("의문의 물건 상자 A").set({"price": 6000000, "amount": 250})
    ref.child("LAByteCoin 1개 교환권(상장가 10만모아)").set({"price": 70000, "amount": 200})
    ref.child("시즌 종료 티켓").set({"price": 10000000000, "amount": 1})
    ref.update({"version": curVersion})


@bot.command()
async def 건의(ctx):
    user = GetUserInfo(ctx)

    if user.get() == None:
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
    user = GetUserInfo(ctx)
    userTitles = user.child("titles").get()

    if setn == None:
        for title in userTitles:
            await ctx.send(allTitles[title])
    else:
        change = re.sub(
            r"\[.+\]", f"[{allTitles[userTitles[int(setn)]]}]", user.get()["nickname"]
        )
        db.reference(f"servers/server{ctx.guild.id}/users/user{ctx.author.id}").update(
            {"nickname": change}
        )

        await ctx.send(f"{change}로 변경 완료")


@bot.command()
async def 의문의물건구매(ctx, grade=None, level=None):
    unknown_trade = db.reference("unknown_trade")

    unknown_trade_dict = unknown_trade.get()

    mainkeyname = f"{grade}_{level}"

    if grade == None:
        for key in unknown_trade_dict.keys():
            await ctx.send(
                f"grade : {key.split('_')[0]} level : {key.split('_')[1]} amount : {unknown_trade_dict[key]}"
            )
    else:
        if level == None:
            for key in unknown_trade_dict.keys():
                if key[0] == grade:
                    await ctx.send(
                        f"level : {key.split('_')[1]} amount : {unknown_trade_dict[key]}"
                    )
        else:
            if f"{grade}_{level}" in unknown_trade_dict.keys():
                if unknown_trade_dict[mainkeyname] > 0:
                    gc1 = gc.open("모아2봇 확률표").worksheet("의문의 물건 기댓값")
                    buyPrice = int(
                        gc1.cell(int(level) + 1, int(grade) + 1).value.replace(",", "")
                    )

                    if CheckToday() == 1:
                        buyPrice = math.floor(buyPrice * 0.6)

                    realPrice = math.floor(buyPrice * 0.8)

                    user = GetUserInfo(ctx)

                    userfinance = user.child("재산").get()

                    if ChangeMoney(ctx, userfinance["money"], -realPrice) == -1:
                        await ctx.send("모아가 부족합니다.")
                    else:
                        GetUnknown(user, grade, level)
                        unknown_trade.update(
                            {mainkeyname: unknown_trade_dict[mainkeyname] - 1}
                        )
                        await ctx.send("구매완료")
                else:
                    await ctx.send("재고 없음")


async def checkunknown(unknown_have, ctx):
    if unknown_have == None:
        await ctx.send("의문의 물건을 가지고 있지 않습니다.")
        return -1


def GetUnknown(userdir, itemgrade, itemlevel):
    haveInfo = userdir.child(f"inventory/의문의 물건/등급{itemgrade}")

    if haveInfo.get() == None:
        haveInfo.update({f"레벨{itemlevel}": 1})
    else:
        if f"레벨{itemlevel}" in haveInfo.get().keys():
            haveInfo.update({f"레벨{itemlevel}": haveInfo.get()[f"레벨{itemlevel}"] + 1})
        else:
            haveInfo.update({f"레벨{itemlevel}": 1})


@bot.command()
async def 의문의물건판매(ctx, grade=None, level=None, plus30=None):
    if ctx.guild.id == 712186772846542889:
        await ctx.send("여기서 판매 허용하면 경제 망가진다 ㄹㅇ ㅋㅋ")
        return
    if plus30 == None:
        await ctx.send("사용할 의문의 물건 판매가격 30% 증가권의 개수를 입력해주세요.")
        return

    gc1 = gc.open("모아2봇 확률표").worksheet("의문의 물건 기댓값")
    sellPrice = int(gc1.cell(int(level) + 1, int(grade) + 1).value.replace(",", ""))

    user_ref = GetUserInfo(ctx)

    unknown_have = reinforce.GetUnknown(user_ref, f"/등급{grade}")
    unknown_dict = unknown_have.get()
    if await checkunknown(unknown_have, ctx) == -1:
        return
    else:
        if int(plus30) >= int(grade) or int(plus30) < 0:
            await ctx.send(f"등급{grade}은 0~{int(grade)-1}장 이하까지 적용 가능합니다.")
            return
        else:
            inventory = user_ref.child(f"inventory").get()
            itemname = "의문의 물건 판매가격 30% 증가권"
            if itemname in inventory.keys():
                if inventory[itemname] - int(plus30) >= 0:
                    user_ref.child(f"inventory").update(
                        {itemname: inventory[itemname] - int(plus30)}
                    )
                else:
                    await ctx.send(f"{itemname}이 부족합니다.")
                    return
        if f"레벨{level}" in unknown_dict.keys():
            user_ref.child(f"inventory/의문의 물건/등급{grade}").update(
                {f"레벨{level}": unknown_dict[f"레벨{level}"] - 1}
            )

            if unknown_dict[f"레벨{level}"] - 1 == 0:
                user_ref.child(f"inventory/의문의 물건/등급{grade}").update(
                    {unknown_dict[f"레벨{level}"]: None}
                )
            else:
                user_ref.child(f"inventory/의문의 물건/등급{grade}").update(
                    {f"레벨{level}": unknown_dict[f"레벨{level}"] - 1}
                )

            if CheckToday() == 4:
                todayUp = 1.2
            else:
                todayUp = 1

            givePrice = math.floor(sellPrice * todayUp * 0.6 * (1.3 ** (int(plus30))))

            user_ref.child("재산").update(
                {"money": user_ref.child("재산").get()["money"] + givePrice}
            )

            if int(level) == 30 and int(grade) == 6:
                await ctx.send(f"더이상 강화 또는 등급업을 할 수 없어 거래시장에 올려지지 않고 모아만 지급됩니다.")
                return

            unknown_trade = db.reference("unknown_trade")

            unknown_trade_dict = unknown_trade.get()

            if unknown_trade_dict == None:
                unknown_trade.update({f"{grade}_{level}": 1})
            else:
                if f"{grade}_{level}" in unknown_trade_dict.keys():
                    unknown_trade.update(
                        {f"{grade}_{level}": unknown_trade_dict[f"{grade}_{level}"] + 1}
                    )
                else:
                    unknown_trade.update({f"{grade}_{level}": 1})

            await ctx.send("판매 완료")
        else:
            await ctx.send("해당 레벨의 의문의 물건을 가지고 있지 않습니다.")
            return


@bot.command()
async def 보유현황(ctx):
    user = GetUserInfo(ctx)

    inventory = user.child("inventory").get()
    sendText = "```"

    for key in inventory.keys():
        sendText += f"{key} : {inventory[key]}\n"
    sendText += "```"
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

    sendText = "```"

    userInfo = users.get()

    for user in userInfo.keys():
        sendText += (
            f"{userInfo[user]['nickname']} : {userInfo[user]['재산']['money']}모아\n"
        )

    sendText += "```"

    await ctx.send(sendText)


@bot.command()
async def 주사위(ctx, mode=None, money=None):
    now = datetime.datetime.now()
    result = random.randint(1, 100)
    if mode == None:
        await ctx.send(result)
    elif int(mode) == 1:
        users = GetUserInfo(ctx)
        today = users.child("today").get()

        if CheckToday() == 5:
            multiple = 12
        else:
            multiple = 1

        if today == None:
            await UpdateDice(ctx, users, result, multiple)
        else:
            if "dice" in today.keys():
                if (
                    users.child("today").get()["dice"]
                    == f"{now.year}-{now.month}-{now.day}"
                ):
                    await ctx.send("하루 1회만 가능합니다.")
                    return
                else:
                    await UpdateDice(ctx, users, result, multiple)
            else:
                await UpdateDice(ctx, users, result, multiple)


async def UpdateDice(ctx, users, result, multiple):
    now = datetime.datetime.now()
    users.child("today").update({"dice": f"{now.year}-{now.month}-{now.day}"})
    users.child("재산").update(
        {"money": users.child("재산").get()["money"] + result * 10000 * multiple}
    )
    await ctx.send(f"결과 : {result}, {result*10000*multiple}모아 획득!")


@bot.command()
async def 오늘의모아봇(ctx):
    todayBenefit = {
        0: "배팅 성공률 5%p 증가",
        1: "의문의 물건 구매비용 40% 할인",
        2: "강화 비용 20% 할인",
        3: "등급업 확률 2배",
        4: "의문의 물건 판매비용 20% 증가",
        5: "오늘의 주사위 지급 모아 12배",
        6: "구걸 10배",
    }

    await ctx.send(todayBenefit[CheckToday()])


@bot.command()
async def 의문의물건(ctx):
    minlevel = [1, 10, 20]
    maxlevel = [10, 20, 30]

    sendtext = "```"

    for i in range(6):
        sendtext += f"등급{i+1} : {minlevel[i]}~{maxlevel[i]}\n"
    sendtext += "```"

    await ctx.send(sendtext)


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

    user = GetUserInfo(ctx).get()

    if Info == "순위":
        forNickname = db.reference(f"servers/server{ctx.guild.id}/users")
        forRank = db.reference(f"free_reinforce/server{ctx.guild.id}").get()

        reinInfo = {}
        print(forRank.keys())
        for user in forRank.keys():
            userInfo = forNickname.child(user).get()
            if userInfo == None:
                continue
            nickname = userInfo["nickname"]
            nickname = re.sub(r"\[.+\]", r"", nickname)
            reinInfo[nickname] = forRank[user]["level"]
            print(reinInfo)
        sortedDict = sorted(reinInfo, reverse=True)

        print(sortedDict)

        sendtext = "```"

        for key in sortedDict:
            sendtext += f"{key} : {reinInfo[key]}\n"

        sendtext += "```"

        await ctx.send(sendtext)
        return

    if user == None:
        await ctx.send("가입을 해주세요.")
        return

    resultInfo = {1: "success", 0: "fail", -10: "destroy"}

    maxlevel = 45
    freereinDB = db.reference(
        f"free_reinforce/server{ctx.guild.id}/user{ctx.author.id}"
    )
    reinData = freereinDB.get()
    if reinData == None:
        freereinDB.update({f"level": 1, "fail": 0})
        await ctx.send("강화 0>1 성공!")
    else:
        level = reinData[f"level"]
        if level == maxlevel:
            await ctx.send("최고레벨입니다.")
            return
        change, success = reinforce.DoReinfoce(level, 2, reinData["fail"])
        if change != -10:
            if change == 1:
                freereinDB.update({f"level": level + change, "fail": 0})

            else:
                freereinDB.update({f"fail": reinData["fail"] + 1})
        else:
            freereinDB.update({f"level": None, "fail": None})
        await ctx.send(
            f"{level} >> {int(level)+1}   {reinData['fail']+1}트의 결과 : **{resultInfo[change]}** (성공확률 : {'{0:.2f}'.format(success)}%)"
        )
        freeReinCooldown.append(ctx.author.id)
        await ctx.send(f"쿨타임 {'{0:.2f}'.format(level*0.2)}초 걸림")

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
            elif level + change == 45:
                finance.ChangeMoney(userdb, 500000000)
                await ctx.send("5억 모아")

        await asyncio.sleep(level * 0.2)
        freeReinCooldown.remove(ctx.author.id)


@bot.command()
async def 오늘의베팅(ctx, myteam=None, moa=None):
    if testMode:
        playList = []
        scoreList = []
        url = "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EB%A1%A4%EC%B1%94%EC%8A%A4+%EC%9D%BC%EC%A0%95"
        webpage = requests.get(url)
        soup = BeautifulSoup(webpage.content, "html.parser")
        for content in soup.find_all("a", class_="team_name"):
            text = str(content)
            print(text)
            playList.append(
                re.sub(
                    r"<.+?>",
                    "",
                    text,
                    0,
                )
            )

        for score in soup.find_all("span", class_="team_score"):

            text = str(score)
            score = re.sub(
                r"<.+?>",
                "",
                text,
                0,
            )
            scoreList.append(int(score))

        index = 0
        teams = []

        while index < len(scoreList):
            print(
                f"{playList[index]} {scoreList[index]} : {scoreList[index+1]} {playList[index+1]}"
            )
            if scoreList[index] + scoreList[index + 1] != 0:
                index += 2
            else:
                sendText = f"{playList[index]} {scoreList[index]} : {scoreList[index+1]} {playList[index+1]}"
                teams.append(playList[index])
                teams.append(playList[index + 1])
                break

        print(myteam)
        if myteam == None:
            await ctx.send(sendText)
            bettingInfo = db.reference(f"result_bet/server{ctx.guild.id}")
            betData = bettingInfo.get()
            if betData == None:
                await ctx.send(sendText)
                sendText = "```"
                for t in teams:
                    sendText += t + "\n"

                sendText += "```"
                await ctx.send(sendText)
            else:
                totalBet = {}
                for key in betData.keys():
                    if betData[key]["team"] in totalBet.keys():
                        totalBet[betData[key]["team"]] += betData[key]["moa"]
                    else:
                        totalBet[betData[key]["team"]] = betData[key]["moa"]
                await ctx.send(totalBet)

                betList = totalBet.keys()
                url = "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query="
                for team in betList:
                    url += team + " "
                webpage = requests.get(url)
                soup = BeautifulSoup(webpage.content, "html.parser")

                realteam = []
                realScore = []
                winscore = 2
                if len(betList) == 1:
                    findResult = soup.find_all("a", class_="team_name")
                    print(findResult)
                    for result in findResult:
                        team = re.sub(
                            r"<.+?>",
                            "",
                            str(result),
                            0,
                        )
                        realteam.append(team)
                    findResult = soup.find_all("span", class_="team_score")
                    for result in findResult:
                        score = re.sub(
                            r"<.+?>",
                            "",
                            str(result),
                            0,
                        )
                        realScore.append(int(score))

                    if winscore in realScore:
                        winIndex = realScore.index(winscore)
                        winTeam = realteam[winIndex]

                        betSum = sum(betData.values())
                        winSUm = totalBet[winTeam]

                        returnResult = betSum / winSUm

                        for key in betData.keys():
                            user = db.reference(
                                f"servers/server{ctx.guild.id}/users/{key}"
                            )

                            result, getMoney = result_bet.CheckResult(
                                user, betData, key, returnResult, winTeam, finance
                            )
                            user = bot.get_user(int(str(key).replace("user", "")))
                            if result == 1:
                                user.send(
                                    f"{betData[key]['team']}의 승리를 맞춰서 {betData[key]['moa']}모아를 걸고 {getMoney}모아를 얻었습니다."
                                )
                            else:
                                user.send(
                                    f"{betData[key]['team']}이 패배해서 {betData[key]['moa']}모아를 잃었습니다."
                                )

                            bettingInfo.child(key).set(None)

                else:
                    findResult = soup.find("span", class_="state_label")
                    result = re.sub(
                        r"<.+?>",
                        "",
                        str(findResult),
                        0,
                    )

                    if result == "종료":
                        findResult = soup.find("div", class_="table_area").find_all(
                            "strong"
                        )
                        for result in findResult:
                            score = re.sub(
                                r"<.+?>",
                                "",
                                str(result),
                                0,
                            )
                            realScore.append(int(score))

                        winIndex = realScore.index(winscore)
                        winTeam = realteam[winIndex]

                        betSum = sum(betData.values())
                        winSUm = totalBet[winTeam]

                        returnResult = betSum / winSUm

                        for key in betData.keys():
                            user = db.reference(
                                f"servers/server{ctx.guild.id}/users/{key}"
                            )

                            result, getMoney = result_bet.CheckResult(
                                user, betData, key, returnResult, winTeam, finance
                            )
                            user = bot.get_user(int(str(key).replace("user", "")))
                            if result == 1:
                                user.send(
                                    f"{betData[key]['team']}의 승리를 맞춰서 {betData[key]['moa']}모아를 걸고 {getMoney}모아를 얻었습니다."
                                )
                            else:
                                user.send(
                                    f"{betData[key]['team']}이 패배해서 {betData[key]['moa']}모아를 잃었습니다."
                                )

                            bettingInfo.child(key).set(None)

                    else:
                        pass

        else:
            if myteam in teams:
                userdb = db.reference(
                    f"result_bet/server{ctx.guild.id}/user{ctx.author.id}"
                )
                financedb = db.reference(
                    f"servers/server{ctx.guild.id}/users/user{ctx.author.id}"
                )
                if moa == None:
                    await ctx.send("베팅할 모아를 입력해주세요.")
                else:

                    data = userdb.get()
                    if data == None:

                        result = finance.ChangeMoney(financedb, -int(moa))
                        if result == -1:
                            await ctx.send("베팅할 모아가 부족합니다.")
                            return
                        else:
                            await ctx.send(f"{myteam}에 {moa}모아 베팅")
                            userdb.update({"team": myteam, "moa": int(moa)})
                    else:
                        if data["team"] == myteam:
                            result = finance.ChangeMoney(financedb, -int(moa))
                            if result == -1:
                                await ctx.send("베팅할 모아가 부족합니다.")
                                return
                            else:
                                await ctx.send(f"{myteam}에 {moa}모아 베팅")
                            userdb.update({"moa": data["moa"] + int(moa)})
                        else:
                            await ctx.send("2개의 팀에 베팅을 할 수 없습니다.")
            else:
                await ctx.send("팀을 잘못 입력했습니다.")
    else:
        await ctx.send("테스트 중입니다.")


bot.run(token)
