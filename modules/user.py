def GetUserInfo(ctx, db):
    return db.reference(f"servers/server{ctx.guild.id}/users/user{ctx.author.id}")