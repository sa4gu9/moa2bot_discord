def GetUnknown(user_ref,add=None):
    unknown_have = user_ref.child(f'inventory/의문의 물건{add}').get()
    return unknown_have