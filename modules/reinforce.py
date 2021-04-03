import random


def GetUnknown(user_ref, add=None):
    unknown_have = user_ref.child(f"inventory/의문의 물건{add}")
    return unknown_have


def CheckUnknown(grade, level):
    # 등급 2~3이고 최소레벨 미만일때

    # 등급 4일때
    # 레벨 20미만일때

    # 등급 5,6일때
    return


def DoReinfoce(level, mode=1, fail=None):
    notchange = 0
    if mode == 1:
        sucnum = 2.77
        failnum = 1.53
        desnum = 0.56

        if level % 5 == 0:
            fail = 0
        else:
            fail = (level - 1) * failnum

        success = 100 - sucnum * level
        destroy = (level - 1) * desnum
        notchange = 100 - success - fail - destroy
    elif mode == 2:
        sucnum = 6.53
        desnum = 0.09

        sucBonus = 6 - (level - 1) * 0.13

        success = 100 - sucnum * (level // 3 + 1) + sucBonus * fail

        destroy = (level - 1) * desnum
        fail = 100 - success - destroy

        print(fail)

    # 강화 확률을 구한다.

    result = random.random() * 100
    print(result)

    if result < success:
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

    return change, success
