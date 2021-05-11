import random
import math


def GetUnknownHave(user_ref):
    unknown_have = user_ref.child(f"inventory/의문의 물건")
    return unknown_have


def DoReinfoce(level, mode=1, fail=None):

    success, notchange, fail, destroy, sucBonus = GetProbability(level, mode)

    # 강화 확률을 구한다.

    result = random.random() * 100

    if result < success or sucBonus >= 100:
        change = 1
    elif result < success + notchange:
        change = 0
    elif result < success + notchange + fail:
        if mode == 1:
            change = -1
        elif mode == 2:
            change = 0
    else:
        change = -10

    return change, success, sucBonus


def GetProbability(level, mode=1):
    notchange = 0
    sucBonus = 0
    if mode == 1:
        sucnum = 2.77
        failnum = 1.53
        desnum = 0.56

        if level % 3 == 0:
            fail = 0
        else:
            fail = (level - 1) * failnum

        success = 100 - sucnum * level

        if level >= 24:
            destroy = 0
        else:
            destroy = (level - 1) * desnum
        notchange = 100 - success - fail - destroy
    elif mode == 2:
        sucnum = 3.98

        sucBonus = (20 - (level - 1) * 0.41) * fail

        success = 100 - sucnum * (level // 2 + 1)

        destroy = 0
        fail = 100 - success

    return success, notchange, fail, destroy, sucBonus


def GetCost(level):
    return math.floor(1000 * ((50 * level) ** (0.05 * level)))