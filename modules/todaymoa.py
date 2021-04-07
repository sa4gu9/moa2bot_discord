import datetime


def GetToday():
    todayBenefit = {
        0: "배팅 성공률 5%p 증가",
        1: "의문의 물건 구매비용 40% 할인",
        2: "강화 비용 20% 할인",
        3: "등급업 확률 2배",
        4: "의문의 물건 판매비용 20% 증가",
        5: "오늘의 주사위 지급 모아 12배",
        6: "구걸 10배",
    }

    return todayBenefit[CheckToday()]


def CheckToday():
    return datetime.datetime.now().weekday()