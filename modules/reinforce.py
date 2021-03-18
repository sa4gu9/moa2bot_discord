import random


def GetUnknown(user_ref, add=None):
    unknown_have = user_ref.child(f"inventory/의문의 물건{add}").get()
    return unknown_have


def DoReinfoce(level):
    sucnum = 2.77
    failnum = 1.53
    desnum = 0.56

    # 강화 확률을 구한다.
    success = 100 - sucnum * level

    if level % 5 == 0:
        fail = 0
    else:
        fail = (level - 1) * failnum

    result = random.random() * 100

    destroy = (level - 1) * desnum
    notchange = 100 - success - fail - destroy

    if result < success:
        change = 1
    elif result < success + notchange:
        change = 0
    elif result < success + notchange + fail:
        change = -1
    else:
        change = -10

    return change