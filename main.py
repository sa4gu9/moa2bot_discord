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


version="V2.21.01.02"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$',intents=intents)
token=""

testint=0
cred=None
db=None

if testint==0: #정식 모드
    token = "NzY4MjgzMjcyOTQ5Mzk5NjEy.X4-Njg.NfyDMPVlLmgLAf8LkX9p0s04QDY"
    project_id="moabot-475bc"
    cred = credentials.Certificate('./moabot-475bc-firebase-adminsdk-dlp6a-e629cf966b.json')   
if testint==1: #테스트 모드
    token="NzY4MzcyMDU3NDE0NTY1OTA4.X4_gPg.fg2sLq5F1ZJr9EwIgA_hiVHtfjQ"
    project_id="moa2bot-test"
    cred = credentials.Certificate('./moa2bot-test-firebase-adminsdk-mog9b-41fe3e4992.json')


firebase_admin.initialize_app(cred)
db = firestore.client()


@bot.event
async def on_ready():
    if testint==1:
        channel=bot.get_channel(709647685417697372)
        await channel.send("moa2bot test")
    await bot.change_presence(status=discord.Status.online,activity=discord.Game(version))

@bot.command()
async def 가입(ctx,nickname) :
    random_pool=string.ascii_lowercase+string.digits
    code=""

    for i in random.sample(random_pool,5):
        code+=i

    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')
    print(ctx.guild.id)

    doc = doc_ref.get()
    if doc.exists:
        await ctx.send(f"이미 가입하였습니다.")
    else:
        doc_ref.set({
            u'equiptitle':0,
            u'nickname':f"{nickname}#{code}",
            u'money': 5000,
            u'titles': {0},
        })
        await ctx.send(f"가입 완료 '[첫 시작]{nickname}#{code}'")


def get_chance_multiple(mode) :
    chance=0
    multiple=0
    if mode==1 : 
        chance=80
        multiple=1.2
    elif mode==2 : 
        chance=64
        multiple=1.6
    elif mode==3 : 
        chance=48
        multiple=2.2
    elif mode==4 : 
        chance=32
        multiple=3
    elif mode==5 : 
        chance=16
        multiple=4
    elif mode==6:
        chance=45
        multiple=2
    elif mode==7 :
        chance=50
        multiple=3
           
    return chance,multiple

@bot.command()
async def 베팅(ctx,mode=None,moa=10000) :
    bonusback=0
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        money=doc.to_dict()['money']
        nickname=doc.to_dict()['nickname']

        if mode==None:
            await ctx.send("모드를 입력해주세요.")
            return

        if int(mode)==6 or int(mode)==7:
            if moa==10000:
                moa=math.floor(money*0.5*(int(mode)-5))
            else :
                await ctx.send("베팅 6,7은 금액 입력을 할 수 없습니다. 6-절반 7-올인")
                return


        if int(mode)>7 or int(mode)<1 : 
            await ctx.send('모드를 잘못 입력했습니다.')
            return


        if money<int(moa) or int(moa)<0 : 
            await ctx.send("보유량보다 많거나 0원 미만으로 베팅하실 수 없습니다.")
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
    

        doc_ref.set({
            'money': money+profit-lose+bonusback
        }, merge=True)
        
        


        
        await ctx.send()
        
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
        money=doc.to_dict()['money']
        nickname=doc.to_dict()['nickname']

        print(money)

        if money>0:
            await ctx.send("0모아를 가지고 있어야 구걸할수 있습니다.")
            return

        doc_ref.set({
            'money': getmoa
        }, merge=True)

        await ctx.send(f"{nickname} {getmoa}모아 획득!")


    else:
        await ctx.send(f"가입이 필요합니다.")

@bot.command()
async def 자산(ctx):
    doc_ref = db.collection(u'servers').document(f'{ctx.guild.id}').collection('users').document(f'{ctx.author.id}')

    doc = doc_ref.get()
    if doc.exists:
        money=doc.to_dict()['money']
        nickname=doc.to_dict()['nickname']

        await ctx.send(f"{nickname}의 자산은 {money}모아")
    else:
        await ctx.send(f"가입이 필요합니다.")




bot.run(token)