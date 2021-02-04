# -*- coding: utf-8 -*- 

import discord
from discord.ext import commands
import random
import datetime
import string
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import math
import traceback
from discord.ext import tasks


version="V2.21.02.04"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$',intents=intents)
token=""

testint=0
cred=None
db=None

print("현재 열고있는 창이 gcp면 gcp를 입력, vscode면 vscode를 입력해주세요.")
currentOpen=input()

if currentOpen=="gcp":
    testint=0
elif currentOpen=="vscode":
    testint=1
else:
    exit()

if testint==0: #정식 모드
    token = "NzY4MjgzMjcyOTQ5Mzk5NjEy.X4-Njg.NfyDMPVlLmgLAf8LkX9p0s04QDY"
    project_id="moabot-475bc"
    cred = credentials.Certificate('./moabot-475bc-firebase-adminsdk-dlp6a-e629cf966b.json')
    print('gcp')
if testint==1: #테스트 모드
    token="NzY4MzcyMDU3NDE0NTY1OTA4.X4_gPg.fg2sLq5F1ZJr9EwIgA_hiVHtfjQ"
    project_id="moa2bot-test"
    cred = credentials.Certificate('./moa2bot-test-firebase-adminsdk-mog9b-41fe3e4992.json')
    print('vscode')



firebase_admin.initialize_app(cred)
db = firestore.client()



@bot.event
async def on_ready():
    if testint==1:
        channel=bot.get_channel(709647685417697372)
        await channel.send("moa2bot test")
    test.start()
    await bot.change_presence(status=discord.Status.online,activity=discord.Game(version))

@bot.command()
async def 가입(ctx,nickname) :
    random_pool=string.ascii_lowercase+string.digits
    password_pool=random_pool+string.ascii_uppercase
    code=""
    password=""

    for i in random.sample(random_pool,5):
        code+=i
    
    for i in random.sample(password_pool,15):
        password+=i

    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        await ctx.send(f"이미 가입하였습니다.")
    else:
        fin_ref=doc_ref.collection(u'자산')

        doc_ref.set({
            u'nickname':f"[첫 시작]{nickname}#{code}",
            u'titles': {0},
            u'password': password,
        })

        fin_ref.document('moa').set({
            'money':20000
        })

        await ctx.send(f"가입 완료 '[첫 시작]{nickname}#{code}'")
        await ctx.author.send(f"가입 완료, 당신의 비밀번호는 {password}입니다.")


def get_chance_multiple(mode) :
    chance=0
    multiple=0
    if mode==1 : 
        chance=40
        multiple=2
    elif mode==2 : 
        chance=30
        multiple=3
    elif mode==3 : 
        chance=20
        multiple=4
    elif mode==4 : 
        chance=30
        multiple=5
           
    return chance,multiple

@bot.command()
async def 베팅(ctx,mode=None,moa=10000) :
    bonusback=0
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        money, nickname=ReturnInfo(ctx)

        if money<=0:
            await ctx.send("베팅할 모아가 없습니다.")

        if mode==None:
            await ctx.send("모드를 입력해주세요.")
            return

        if int(mode)==4:
            if moa==10000:
                moa=money
            else :
                await ctx.send("베팅 4는 금액 입력을 할 수 없습니다. 올인만 가능합니다.")
                return

        if int(mode)>4 or int(mode)<1 : 
            await ctx.send('모드를 잘못 입력했습니다.')
            return


        if money<int(moa) or int(moa)<0 : 
            await ctx.send("보유량보다 많거나 0원 이하로 베팅하실 수 없습니다.")
            return
        

        chance,multiple=get_chance_multiple(int(mode))
        result=random.randrange(0,100)
        lose=int(moa)
        profit=0
        if result<chance : 
            profit=math.floor(multiple*int(moa))
            await ctx.send(f"{nickname} 베팅 성공!")
            success=True
        else :
            await ctx.send(f"{nickname} 베팅 실패!")
            save2=random.randrange(0,100)
            success=False
            if save2<10 :
                bonusback=math.floor(lose*0.3)
                await ctx.send("건 돈의 30% 지급")
    
        ChangeMoney(ctx,money,profit-lose+bonusback)
    else:
        await ctx.send(f"가입이 필요합니다.")


def GetBeggingMoa():
    i=1
    cut=0
    getmoa=0
    result=random.random()*100
    while i<=12:
        cut+=i
        if result<cut:
            getmoa=32000-1000*(i-1)
            break
        else :
            i+=1
    if i==1:
        result=random.random()*100
        if result<10:
            getmoa*=2
    if i==13 :
        getmoa=2500

    return getmoa

@bot.command()
async def 구걸(ctx) :
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        getmoa=GetBeggingMoa()
        money,nickname=ReturnInfo(ctx)

        if money>0:
            await ctx.send("0모아를 가지고 있어야 구걸할수 있습니다.")
            return

        ChangeMoney(ctx,money,getmoa)

        await ctx.send(f"{nickname} {getmoa}모아 획득!")


    else:
        await ctx.send(f"가입이 필요합니다.")

@bot.command()
async def 자산(ctx):
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        money,nickname=ReturnInfo(ctx)

        await ctx.send(f"{nickname}의 자산은 {money}모아")
    else:
        await ctx.send(f"가입이 필요합니다.")


@bot.command()
async def 비밀번호(ctx) :
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
    
    doc = doc_ref.get()
    if doc.exists:
        password=doc.to_dict()['password']

        await ctx.auhor.send(f"당신의 비밀번호는 {password}")
    else:
        await ctx.send(f"가입이 필요합니다.")

@bot.command()
async def 상자구매(ctx):
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    money,nickname = ReturnInfo(ctx)
    percent=[]

    itemgrade=0
    itemlevel=0

    minlevel=[1,5,10,15,20,25]
    maxlevel=[5,10,20,30,30,30]  

    if money>=20000:
        ChangeMoney(ctx,money,-20000)

        result=random.random()*100
        if result<51:
            itemgrade=1
            percent.append(0.51)
        elif result<82:
            itemgrade=2
            percent.append(0.31)
        elif result<93:
            itemgrade=3
            percent.append(0.11)
        elif result<97:
            itemgrade=4
            percent.append(0.04)
        elif result<99:
            itemgrade=5
            percent.append(0.02)
        else:
            itemgrade=6
            percent.append(0.01)

        result=random.random()*100

        if result<40:
            itemlevel=minlevel[itemgrade-1]
            percent.append(0.4)
        elif result<70:
            itemlevel=minlevel[itemgrade-1]+1
            percent.append(0.3)
        elif result<90:
            itemlevel=minlevel[itemgrade-1]+2
            percent.append(0.2)
        else:
            itemlevel=random.randint(minlevel[itemgrade-1]+3,maxlevel[itemgrade-1])
            percent.append(0.1)
            percent.append(maxlevel[itemgrade-1]-(minlevel[itemgrade-1]+3)+1)

        unknown_ref=doc_ref.collection(u'의문의 물건')

        unknown_dict=unknown_ref.document(f'등급{itemgrade}').get().to_dict()
        print(unknown_dict)

        percentcalc=0

        

        if len(percent)==2:
            percentcalc=percent[0]*percent[1]*100
        elif len(percent)==3:
            percentcalc=percent[0]*percent[1]/percent[2]*100



        if unknown_dict == None:
            unknown_dict={}
            unknown_dict[str(itemlevel)]=1
        else:
            if str(itemlevel) in dict(unknown_dict).keys():
                unknown_dict[str(itemlevel)]+=1
            else:
                unknown_dict[str(itemlevel)]=1

        print(unknown_dict)

        unknown_ref.document(f'등급{itemgrade}').set(unknown_dict,merge=True)
      

        if itemlevel==30 and itemgrade==6 :
            doc_ref.update({u'titles': firestore.ArrayUnion([1])})
            await ctx.send(f"{nickname} 칭호 [완벽을 뽑은 자] 획득")


        await ctx.send(f"의문의 물건 등급{itemgrade} {itemlevel}강({(format(percentcalc,'''.3f''')).rstrip('0')}%) 획득!")
    else:
        await ctx.send(f"상자를 구매할수 없습니다. {20000-money}모아가 부족합니다.")
    

@bot.command()
async def 강화(ctx,grade=None,level=None):
    try:
        user_ref= db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
        minlevel=[1,5,10,15,20,25]
        maxlevel=[5,10,20,30,30,30]

        if grade=="destroy":
            unknown_have = user_ref.collection(u'의문의 물건').document(f'destroy').get().to_dict()

            if unknown_have==None:
                await ctx.send("입력한 등급의 의문의 물건을 가지고 있지 않습니다.")
                return

            embed=discord.Embed(title=f"보유중인 파괴 된 의문의 물건")      

            for i in unknown_have.keys():
                embed.add_field(name=f"{i}",value=unknown_have[i]) 
            await ctx.send(embed=embed)
            return



        grade=int(grade)

        if grade<1 or grade>6:
            await ctx.send("의문의 물건은 1~6등급입니다.")

        

        unknown_have = user_ref.collection(u'의문의 물건').document(f'등급{grade}').get().to_dict()
        destroy_have = user_ref.collection(u'의문의 물건').document(u'destroy')
        des_dict=destroy_have.get().to_dict()

        fin_ref=user_ref.collection(u'자산')

        print("check")
        check(user_ref,fin_ref)

        if unknown_have==None:
            await ctx.send("입력한 등급의 의문의 물건을 가지고 있지 않습니다.")
            return

        if level==None:
            #보유중인 의문의 물건을 보여줌
            embed=discord.Embed(title=f"보유중인 의문의 물건 등급{grade}")      

            for i in unknown_have.keys():
                embed.add_field(name=f"+{i}",value=unknown_have[i]) 
            await ctx.send(embed=embed)

        else:
            level=int(level)

            if level>maxlevel[grade-1] or level<minlevel[grade-1]:
                await ctx.send(f"등급{grade}는 {minlevel[grade-1]}강이상 +{maxlevel[grade-1]}강이하 입니다.")
                return

            if level==maxlevel[grade-1] :
                if grade<6:
                    await ctx.send("현재 레벨은 현재 등급의 최고 레벨입니다. 등급업을 해주세요.")
                    return
                elif grade==6 :
                    await ctx.send("최고 등급의 최고 레벨은 강화를 할 수 없습니다.")
                    return
            

            if str(level) in unknown_have.keys():
                money,nickname=ReturnInfo(ctx)

                #강화 비용을 구한다.
                price=math.floor(1000*((50*level)**(0.05*level)))


                #가지고 있는 돈보다 강화 비용이 많으면 강화 불가
                if price>money:
                    await ctx.send(f"{price-money}모아가 부족합니다. 강화 비용 : {price}모아")
                    return

                sucnum=2.77
                failnum=1.53
                desnum=0.56

                #강화 확률을 구한다.
                success=100-sucnum*level
                
                if level%5==0:
                    fail=0
                else:
                    fail=(level-1)*failnum

                destroy=(level-1)*desnum
                notchange=100-success-fail-destroy


                #강화를 한다.
                result=random.random()*100
                change=0

                if result<success:
                    change=1
                elif result<success+notchange:
                    change=0
                elif result<success+notchange+fail:
                    change=-1
                else:
                    change=-10
                    if des_dict == None:
                        destroy_have.set({
                            f'등급{grade}':1
                        })
                    else:
                        if grade!=1:
                            if f'등급{grade}' in des_dict.keys():
                                des_dict[f'등급{grade}']+=1
                            else:
                                des_dict[f'등급{grade}']=1
                            
                            destroy_have.set(des_dict)


                #change값에 따라 dictionary를 바꾼다. 단, change가 0이면 바꾸지 않는다.
                print(unknown_have)

                unknown_have[str(level)]-=1
                
                if unknown_have[str(level)]==0:
                    del unknown_have[str(level)]
                
                if change!=0 and change!=-10:
                    if str(level+change) in unknown_have.keys():
                        unknown_have[str(level+change)]+=1
                    else:
                        unknown_have[str(level+change)]=1


                #현재 가지고 있는 돈에서 강화비용을 빼고 firebase에 올린다.
                ChangeMoney(ctx,money,-price)

                
                #바꾼 dictionary를 firebase에 올린다. 단, change가 0이면 바꾸지 않는다.
                if change!=0:
                    user_ref.collection(u'의문의 물건').document(f'등급{grade}').set(unknown_have)
                

                await ctx.send(f"change : {change}")

            else:
                await ctx.send("입력한 레벨의 의문의 물건을 가지고 있지 않습니다.")

    except Exception as e :
        traceback.print_exc()
        await ctx.send("의문의 물건 등급 또는 레벨을 숫자로 입력해주세요.")

def check(user_ref,fin_ref):

    user_info=user_ref.get().to_dict()

    if fin_ref.document('moa').get().to_dict()==None or 'money' in user_info.keys():
        
        money=user_info['money']
        del user_info['money']

        print(user_info)

        user_ref.set(user_info)

        fin_ref.document('moa').set({
            'money':money
        })


        


@bot.command()
async def 코인(ctx,mode=None,amount=None):
    try:
        coin_ref=db.collection(u'coins').document(f'moacoin')
        cantrade=coin_ref.get().to_dict()['cantrade']

        user_info=None
        money=None

        price=coin_ref.get().to_dict()['price']

        user_ref= db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
        fin_ref=user_ref.collection(u'자산')

        check(user_ref,fin_ref)

        money,nickname=ReturnInfo(ctx)

        if fin_ref.document('coins').get().to_dict() == None:
            have=0
        else:
            have=fin_ref.document('coins').get().to_dict()['moacoin']

        if mode==None:
            strike=coin_ref.get().to_dict()['strike']
            last=coin_ref.get().to_dict()['last']
            await ctx.send(f"현재 가격 : {price} 연속 상승 횟수 : {strike} 가격 변화 : {last}")
            return
        if not cantrade:
            await ctx.send("거래를 할수없는 시간입니다.(거래 가능 시간 : 오전 10시 ~ 오후 10시)")
            return

        amount=int(amount)

        if mode=="buy":
            if not cantrade:
                return
            if money>=amount*price:
                #구매한다
                fin_ref.document('coins').set({
                    'moacoin':have+amount
                },merge=True)

                fin_ref.document('moa').set({
                    'money':money-price*amount
                },merge=True)

                await ctx.send(f"moacoin {amount}개 구입 완료")
            else:
                await ctx.send(f"{amount*price-money}모아가 부족합니다.")

            
        elif mode=="sell":
            if fin_ref.document('coins').get().to_dict() == None:
                have=0
            else:
                have=fin_ref.document('coins').get().to_dict()['moacoin']

            if amount>have:
                await ctx.send(f"코인이 {amount-have}개 부족합니다.")
                return

            fin_ref.document('coins').set({
                'moacoin':have-amount
            },merge=True)

            fin_ref.document('moa').set({
                'money':money+price*amount
            },merge=True)
            

            await ctx.send(f"moacoin {amount}개 판매 완료")
            
        else :
            await ctx.send("모드를 buy 또는 sell로 입력해주세요.")
            return
    except Exception as e :
        await ctx.send("수량을 숫자로 입력해주세요.")
        traceback.print_exception()



@tasks.loop(seconds=10)
async def test():
    date=datetime.datetime.now()
    coin_ref=db.collection(u'coins').document(f'moacoin')

    coin_info=coin_ref.get().to_dict()

    price=0

    if not coin_info==None: 
        cantrade=coin_info['cantrade']
        price=coin_info['price']
        strike=coin_info['strike']
        maxprice=coin_info['maxprice']
        minprice=coin_info['minprice']
    

    
    if date.hour==10 and date.minute==0 and date.second>=0 and date.second<10:
        if coin_info == None or price<=0:
            coin_ref.set({
                "price":20000,
                "minprice":20000,
                "maxprice":20000,
                "strike":0,
                "last":0,
                "cantrade":True
            },merge=True)
        else:
            coin_ref.set({
                "cantrade":True
            },merge=True)
        return
    elif coin_ref.get().to_dict()==None:
        return
    

    if date.hour==22 and date.minute==0 and date.second>=0 and date.second<10:
        coin_ref.set({
            "cantrade":False
        },merge=True)
        return



    if (date.hour>=12 and date.hour<=20 and date.minute%20==0 and strike!=30 and date.second>=0 and date.second<10) and cantrade :
        if (date.hour==20 and date.minute!=0) :
            return

        udnum=37
        udchan=1.8

        up=udnum-strike*udchan
        down=udnum+strike*udchan
        destroy=abs(strike)*1.03+0.8
        notchange=100-up-down-destroy

        result=None

        amount=0
        cut=0

        
        for i in range(10):
            result=random.random()*100
            cut+=19-i*2

            if result<cut:
                jump=random.random()*4.9+0.1
                amount=math.floor((i+1)*100*jump)
                print(amount)
                break


        result=random.random()*100
        print(result)

        if result<up:
            print(f"{amount}모아 상승 현재 가격 : {price+amount}")
            if strike<=0:
                strike=1
            else:
                strike+=1
            price+=amount
        elif result<up+notchange:
            print(f"변화 없음")
            amount=0
            strike=0
        elif result<up+notchange+down:
            print(f"{amount}모아 하락 현재 가격 : {price-amount}")
            price-=amount
            amount=-amount
            if strike>=0:
                strike=-1
            else:
                strike-=1
        else:
            price=-50000

        if price<=0 :
            strike=-30
            cantrade=False
            print(f"상장 폐지")

        if price>maxprice:
            maxprice=price
        
        if price<minprice:
            minprice=price



        coin_ref.set({
            "strike":strike,
            "price":price,
            "last":amount,
            "minprice":minprice,
            "maxprice":maxprice,
            "cantrade":cantrade
        })
    
def ReturnInfo(ctx):
    user_ref= db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
    fin_ref=user_ref.collection(u'자산')

    check(user_ref,fin_ref)

    money=fin_ref.document('moa').get().to_dict()['money']
    nickname=user_ref.get().to_dict()['nickname']


    return money,nickname

def ChangeMoney(ctx,money,change):
    user_ref= db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
    fin_ref=user_ref.collection(u'자산')

    check(user_ref,fin_ref)

    if change<0:
        if abs(change)>money:
            return -1

    fin_ref.document('moa').set({
        'money':money+change
    },merge=True)

@bot.command()
async def 상점(ctx):
    store_ref= db.collection(u'servers').document(f'{ctx.guild.id}').collection('store')

bot.run(token)