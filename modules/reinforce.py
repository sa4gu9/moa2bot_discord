import random


def GetUnknownHave(user_ref, add=None):
    unknown_have = user_ref.child(f"inventory/의문의 물건{add}")
    return unknown_have


def CheckUnknown(grade, level, unknown_have, unknown_dict, mode):

    minlevel = [1, 10, 20]
    maxlevel = [10, 20, 30]

    # 등급 2~3이고 최소레벨 미만일때
    if mode == 1:
        unknown_have.update({f"레벨{level}": unknown_dict[f"레벨{level}"] - 1})

        if f"레벨{minlevel[grade - 1]}" in unknown_dict.keys():
            unknown_have.update(
                {
                    f"레벨{minlevel[grade - 1]}": unknown_dict[f"레벨{minlevel[grade - 1]}"]
                    + 1
                }
            )
        else:
            unknown_have.update({f"레벨{minlevel[grade - 1]}": 1})

    # 등급 4+등급 20이상일때
    elif mode == 2:
        return
    # 등급 4+등급 20미만일때
    elif mode == 3:
        return

    # 등급 5,6일때
    elif mode == 4:
        return


def DoReinfoce(level, mode=1, fail=None):
    notchange = 0
    sucBonus = 0
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
        sucnum = 3.98

        sucBonus = (20 - (level - 1) * 0.41) * fail

        success = 100 - sucnum * (level // 2 + 1)

        destroy = 0
        fail = 100 - success

        print(fail)

    # 강화 확률을 구한다.

    result = random.random() * 100
    print(result)

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
