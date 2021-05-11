import datetime


def GetToday():
    todayBenefit = {
        0: "배팅 성공률 5%p 증가",
        1: "강화 크리티컬 성공시 +2",
        2: "강화 비용 20% 할인",
        3: "강화 20강이하 성공시 1+1",
        4: "무료강화 30강까지 1+1",
        5: "오늘의 주사위 지급 모아 12배",
        6: "구걸 10배",
    }

    return todayBenefit[CheckToday()]


def CheckToday():
    return datetime.datetime.now().weekday()