import math
import random
import main


def DoBet(mode, moa):

    chance, multiple = get_chance_multiple(int(mode))

    if main.CheckToday() == 0:
        chance += 5

    result = random.randrange(0, 100)

    change = -moa
    if result < chance:
        change += math.floor(multiple * int(moa))
        success = True
    else:
        success = False

    return success, change


def get_chance_multiple(mode):
    chance = 0
    multiple = 0
    if mode == 1:
        chance = 40
        multiple = 2
    elif mode == 2:
        chance = 30
        multiple = 3
    elif mode == 3:
        chance = 20
        multiple = 4
    elif mode == 4:
        chance = 30
        multiple = 5

    return chance, multiple
