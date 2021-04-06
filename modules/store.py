def UseStore(store_ref, storeInfo, curVersion, ctx, itemName, db, user, amount):
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
            userInfo = user.GetUserInfo(ctx, db)
            money, nickname = user.ReturnInfo(ctx)

            if int(amount) > storeInfo[itemName]["amount"]:
                await ctx.send("매진이거나 남은수량보다 많이 살 수 없습니다.")
                return

            totalPrice = storeInfo[itemName]["price"] * amount
            have = 0
            if money >= totalPrice:
                # 아이템 보유 정보
                userInfo = user.GetUserInfo(ctx, db)
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


def StoreReset(ref, curVersion, ctx):
    ref.child("의문의 물건 등급업 주문서").set({"price": 3000, "amount": 300})
    ref.child("의문의 물건 상자 C").set({"price": 35000, "amount": 1000})
    ref.child("의문의 물건 상자 B").set({"price": 300000, "amount": 500})
    ref.child("의문의 물건 상자 A").set({"price": 6000000, "amount": 250})
    ref.child("LAByteCoin 1개 교환권(상장가 10만모아)").set({"price": 70000, "amount": 200})
    ref.child("시즌 종료 티켓").set({"price": 10000000000, "amount": 1})
    ref.update({"version": curVersion})