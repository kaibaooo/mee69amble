import discord
import threading
import time
import config
import random
import asyncio
import traceback
import os
import math
import finnhub
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from sql_helper import *
client = discord.Client()

def dailyReset(db_Thread:DB) -> None:
    now = datetime.now()
    current_date = now.strftime("%Y/%m/%d")
    # print(current_date)
    current_date = datetime.strptime(current_date, "%Y/%m/%d")
    last_date = db_Thread.fetchOneSQL(f'SELECT "setting_value" FROM "bot_settings" WHERE "setting_name"="daily_date"')
    # print(last_date)
    last_date = datetime.strptime(last_date, "%Y/%m/%d")
    if last_date < current_date:
        db_Thread.WSQL(f'UPDATE "condition_flags" SET "daily"=0;')
        # print(f'UPDATE "condition_flags" SET "daily"=0;')
        db_Thread.WSQL(f'''UPDATE "bot_settings" SET "setting_value"="{now.strftime("%Y/%m/%d")}" WHERE "setting_name"="daily_date";''')
        # print(f'UPDATE "bot_settings" SET "setting_value"="{now.strftime("%Y/%m/%d")}" WHERE "setting_name"="daily_date";')
        last_date = db_Thread.fetchOneSQL(f'''SELECT "setting_value" FROM "bot_settings" WHERE "setting_name"="daily_date"''')
        # print(last_date)
        print("Daily Task Reset!")

def battleGameTimeout(db_Thread:DB) -> None:
    crt_time = time.time()
    db_Thread.WSQL(f'''UPDATE "condition_flags" SET "battle_game_opponent"="" WHERE "battle_game_timeout"<{crt_time};''')
    # pass

async def diceGame(message:str, user_uid:str, paid:int, crt_money:int) -> None:
    global db
    db.WSQL(f'UPDATE "condition_flags" SET "next_dice_game_time"={time.time()+config.dice_game_cool_down} WHERE "uid"={user_uid};')
    user_num_1 = random.randint(config.dice_game_min, config.dice_game_max)
    user_num_2 = random.randint(config.dice_game_min, config.dice_game_max)
    bot_num_1 = random.randint(config.dice_game_min, config.dice_game_max)
    bot_num_2 = random.randint(config.dice_game_min, config.dice_game_max)

    await message.channel.send(f"???? {message.author.name} ?????? {paid} {config.economy_icon} ????????????...")
    await asyncio.sleep(config.dice_game_msg_interval)
    await message.channel.send(f"???? {message.author.name} ?????? {user_num_1} ??? {user_num_2}...")
    await asyncio.sleep(config.dice_game_msg_interval)
    await message.channel.send(f"???? {message.author.name}???????????????????????????... ????????? {bot_num_1} ??? {bot_num_2}...")
    await asyncio.sleep(config.dice_game_msg_interval)
    
    if user_num_1+user_num_2 > bot_num_1+bot_num_2: # User Win
        await message.channel.send(f"???? {message.author.name}, ????????? {paid} {config.economy_icon}")
        new_money = crt_money + paid
        db.WSQL(f'UPDATE money SET "money"={new_money} WHERE "uid"={user_uid};')
    elif user_num_1+user_num_2 < bot_num_1+bot_num_2: # Bot Win
        await message.channel.send(f"???? {message.author.name}, ????????? {paid} {config.economy_icon}")
        new_money = crt_money - paid
        db.WSQL(f'UPDATE money SET "money"={new_money} WHERE "uid"={user_uid};')
    else:
        await message.channel.send(f"???? {message.author.name}?????????????????????????????? {paid} {config.economy_icon}")
    db.WSQL(f'UPDATE condition_flags SET "dice_game_exist"=0 WHERE "uid"={user_uid};')

async def rpsGame(message:str, user_uid:str, paid:int, crt_money:int, user_rps) -> None:
    global db
    db.WSQL(f'UPDATE "condition_flags" SET "next_rps_game_time"={time.time()+config.dice_game_cool_down} WHERE "uid"={user_uid};')
    bot_rps = random.choice(config.rps_type)
    new_money = 0
    win_lose_table = [[0, -paid, paid], [paid, 0, -paid], [-paid, paid, 0]]
    reward = win_lose_table[config.rps2id[user_rps]][config.rps2id[bot_rps]]
    await message.channel.send(f"???? 1, 2, 3...")
    await asyncio.sleep(config.rps_game_msg_interval)
    await message.channel.send(f"???? {message.author.name} ?????? {config.rps2icon[user_rps]}??????????????? {config.rps2icon[bot_rps]}")
    await asyncio.sleep(config.rps_game_msg_interval)
    if reward > 0:
        await message.channel.send(f"???? {config.rps2chinese[user_rps]}??????{config.rps2chinese[bot_rps]}, {message.author.name}?????? {paid} {config.economy_icon}")
    elif reward < 0:
        await message.channel.send(f"???? {config.rps2chinese[bot_rps]}??????{config.rps2chinese[user_rps]}, {message.author.name}?????? {paid} {config.economy_icon}")
    else:
        await message.channel.send(f"???? {message.author.name}??????????????????????????????????????????????????? {paid} {config.economy_icon}")
    new_money = crt_money + reward
    db.WSQL(f'UPDATE money SET "money"={new_money} WHERE "uid"={user_uid};')
    db.WSQL(f'UPDATE condition_flags SET "rps_game_exist"=0 WHERE "uid"={user_uid};')


async def battleGame(message:str, src_id:str, dst_id:str, paid:int, src_uid:str, dst_uid:str) -> None:
    src_opponent_num1 = random.randint(1,6)
    src_opponent_num2 = random.randint(1,6)
    dst_opponent_num1 = random.randint(1,6)
    dst_opponent_num2 = random.randint(1,6)

    await message.channel.send(f"?????????????????????????????????????????????????????")
    await asyncio.sleep(config.rps_game_msg_interval)
    await message.channel.send(f"<@!{src_id}> ?????? {src_opponent_num1} ??? {src_opponent_num2}")
    await asyncio.sleep(config.rps_game_msg_interval)
    await message.channel.send(f"??????????????????????")
    await asyncio.sleep(config.rps_game_msg_interval)
    await message.channel.send(f"<@!{dst_id}> ?????? {dst_opponent_num1} ??? {dst_opponent_num2}")
    await asyncio.sleep(config.rps_game_msg_interval)
    src_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={src_uid}')
    dst_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={dst_uid}')
    if src_opponent_num1+src_opponent_num2 > dst_opponent_num1+dst_opponent_num2:
        await message.channel.send(f"?????????????????????? <@!{src_id}> ?????? <@!{dst_id}>???????????????????????{paid} {config.economy_icon}")
        src_money += paid
        dst_money -= paid
        
    elif src_opponent_num1+src_opponent_num2 < dst_opponent_num1+dst_opponent_num2:
        await message.channel.send(f"???????????????????? <@!{src_id}> ????????? <@!{dst_id}>?????????????????????????{paid} {config.economy_icon}")
        src_money -= paid
        dst_money += paid
    else:
        await message.channel.send(f"?????????????????????? <@!{src_id}> ??? <@!{dst_id}>???????????????????????????????????????????????????????????")
    db.WSQL(f'UPDATE money SET "money"={src_money} WHERE "uid"={src_uid};')
    db.WSQL(f'UPDATE money SET "money"={dst_money} WHERE "uid"={dst_uid};')
    db.WSQL(f'UPDATE condition_flags SET "battle_game_opponent"=0, "next_battle_game_time"={time.time()+config.battle_game_timeout}, "battle_game_exist"=0 WHERE "uid"={src_uid};')

async def buyVCoin(message, user_uid:str, paid:int, coin_name:str) -> None:
    try:
        global db
        coin_name = config.coin_names2full[coin_name]
        cg = CoinGeckoAPI()
        result = cg.get_price(ids=[coin_name], vs_currencies='usd')
        crt_price = result[coin_name]["usd"]
        user_buy_unit = paid / crt_price

        crt_user_units = db.fetchOneSQL(f'SELECT "coin_amount" FROM "coin_assets" WHERE "uid"={user_uid} AND "coin"="{coin_name}";')
        crt_user_avgprice = db.fetchOneSQL(f'SELECT "avg_price" FROM "coin_assets" WHERE "uid"={user_uid} AND "coin"="{coin_name}";')
        # print(crt_user_units)
        # print(crt_user_avgprice)
        if crt_user_units == None: # ????????????
            db.WSQL(f'INSERT INTO coin_assets("uid","coin","coin_amount", "avg_price") VALUES ({user_uid},"{coin_name}",0,0)')
            db.WSQL(f'UPDATE coin_assets SET "coin_amount"={user_buy_unit}, "avg_price"={crt_price} WHERE "uid"={user_uid} AND "coin"="{coin_name}";')
        else:
            avg_price = (crt_user_units / (crt_user_units + user_buy_unit) * crt_user_avgprice) + (user_buy_unit / (crt_user_units + user_buy_unit) * crt_price)
            db.WSQL(f'UPDATE coin_assets SET "avg_price"={avg_price}, "coin_amount"={crt_user_units + user_buy_unit} WHERE "uid"={user_uid} AND "coin"="{coin_name}";')
        crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid}')
        # print(crt_money)
        crt_money -= paid
        db.WSQL(f'UPDATE "money" SET "money"={crt_money} WHERE uid={user_uid}')
        embed=discord.Embed(title=f"**{message.author.name} ??????????????????????????? ??????**", description=f"?????? {user_buy_unit} ????????? {coin_name}\n???????????? {crt_price} {config.economy_name}{config.economy_icon} ", color=0xFF3333)
        await message.channel.send(embed=embed)
    except Exception as e:
        print(e)
        embed=discord.Embed(title=f"**{message.author.name} ??????????????????????????? ????????????**", color=0xFF3333)
        await message.channel.send(embed=embed)

async def buyStock(message, trade_msg, user_uid:str, buy_amount:int, stock_name:str, crt_price:int):
    global db
    crt_user_units = db.fetchOneSQL(f'SELECT "stock_amount" FROM "stock_assets" WHERE "uid"={user_uid} AND "stock"="{stock_name}";')
    crt_user_avgprice = db.fetchOneSQL(f'SELECT "avg_price" FROM "stock_assets" WHERE "uid"={user_uid} AND "stock"="{stock_name}";')
    # print(crt_user_units)
    # print(crt_user_avgprice)
    if crt_user_units == None: # ????????????
        db.WSQL(f'INSERT INTO stock_assets("uid","stock","stock_amount", "avg_price") VALUES ({user_uid},"{stock_name}",0,0)')
        db.WSQL(f'UPDATE stock_assets SET "stock_amount"={buy_amount}, "avg_price"={crt_price} WHERE "uid"={user_uid} AND "stock"="{stock_name}";')
    else:
        avg_price = (crt_user_units / (crt_user_units + buy_amount) * crt_user_avgprice) + (buy_amount / (crt_user_units + buy_amount) * crt_price)
        db.WSQL(f'UPDATE stock_assets SET "avg_price"={avg_price}, "stock_amount"={crt_user_units + buy_amount} WHERE "uid"={user_uid} AND "stock"="{stock_name}";')
    crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid}')
    # print(crt_money)
    crt_money -= math.ceil(buy_amount*crt_price)
    db.WSQL(f'UPDATE "money" SET "money"={crt_money} WHERE uid={user_uid}')
    embed=discord.Embed(title=f"**{message.author.name} ??????????????????????????? ??????**", description=f"?????? {buy_amount} ????????? {stock_name} ??? {buy_amount*crt_price} (~{math.ceil(buy_amount*crt_price)})\n???????????? {crt_price} {config.economy_name} {config.economy_icon}", color=0xFF3333)
    # embed=discord.Embed(title=f"", color=0xFF3333)
    # await message.channel.send(embed=embed)
    await trade_msg.edit(content="", embed=embed)
    # await message.channel.send(embed=embed)

def routine() -> None:
    db_Thread = DB()
    while(True):
        dailyReset(db_Thread)
        battleGameTimeout(db_Thread)
        time.sleep(5)

@client.event
async def on_ready():
    t = threading.Thread(target=routine, daemon=True)
    t.start()
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global db
    if message.author == client.user:
        return
    if message.guild.id == "413715439466840071" and message.channel.id != "892697813199237130":
        return
    # print("Delay")
    # time.sleep(10)
    if message.content.startswith(config.prefix):
        user_uid = db.fetchOneSQL(f'SELECT "id" FROM "user_group" WHERE "user"={message.author.id} AND "group"={message.guild.id};')
        # CREATE USER
        # INIT USER
        if user_uid == None:
            print(f"{message.author.display_name} talk in {message.guild.name} : {message.content}")
            db.WSQL(f'INSERT INTO user_group("user", "group") VALUES ({message.author.id}, {message.guild.id});')
            user_uid = db.fetchOneSQL(f'SELECT "id" FROM "user_group" WHERE "user"={message.author.id} AND "group"={message.guild.id};')
            db.WSQL(f'INSERT INTO condition_flags("uid") VALUES ({user_uid});')
            db.WSQL(f'INSERT INTO money("uid") VALUES ({user_uid});')
            db.WSQL(f'INSERT INTO coin_assets("uid") VALUES ({user_uid});')
        # FEATURES
        crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid}')
        parse = message.content.split(" ")
        parse[0] = parse[0].lower()
        if parse[0] == f"{config.prefix}daily": # !daily
            print(f"{message.channel.name}")
            print(f"{message.guild.id}")
            try:
                daily_stat = db.fetchOneSQL(f'SELECT "daily" FROM "condition_flags" WHERE "uid"="{user_uid}";')
                if daily_stat == 0:
                    # print("Check In!!")
                    db.WSQL(f'UPDATE condition_flags SET "daily"=1 WHERE "uid"={user_uid};')
                    reward = random.randint(config.daily_min, config.daily_max)
                    new_money = crt_money + reward
                    db.WSQL(f'UPDATE money SET "money"={new_money} WHERE "uid"={user_uid};')
                    embed=discord.Embed(description=f"<@{message.author.id}>????????????????????????????????????????????????{reward} {config.economy_icon}", color=0x00eeff)
                    await message.channel.send(embed=embed)
                else:
                    # print("Already Checked In")
                    embed=discord.Embed(description=f"<@{message.author.id}>???????????????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
            except:
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}dice": # !dice {amount}
            try:
                paid = int(parse[1])
                if crt_money < paid: # ??????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ??? {config.economy_icon} ???????????? ??????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid > config.dice_game_max_paid: # ????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {config.dice_game_max_paid} {config.economy_icon}", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid < 1: # ??????????????????0
                    embed=discord.Embed(description=f"{message.author.display_name}???????????????????????????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                
                is_gaming = db.fetchOneSQL(f'SELECT "dice_game_exist" FROM "condition_flags" WHERE "uid"={user_uid}')
                available_time = db.fetchOneSQL(f'SELECT "next_dice_game_time" FROM "condition_flags" WHERE "uid"={user_uid}')
                if is_gaming == 1: # ????????????????????????????????????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                elif available_time > time.time(): # CD????????????
                    diff_time = int(available_time - time.time())
                    minute = diff_time // 60
                    second = diff_time % 60
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {minute} ??? {second} ???????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    # return
                else:
                    db.WSQL(f'UPDATE condition_flags SET "dice_game_exist"=1 WHERE "uid"={user_uid};')
                    await diceGame(message, user_uid, paid, crt_money)
                # t = threading.Thread(target=diceGame, args=(message, user_uid, paid, crt_money))
                # t.start()
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}rps": # !rps 50 rock
            try:
                paid = int(parse[1])
                rps = parse[2]
                is_gaming = db.fetchOneSQL(f'SELECT "rps_game_exist" FROM "condition_flags" WHERE "uid"={user_uid}')
                available_time = db.fetchOneSQL(f'SELECT "next_rps_game_time" FROM "condition_flags" WHERE "uid"={user_uid}')
                if crt_money < paid: # ??????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ??? {config.economy_icon} ???????????? ??????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid > config.rps_game_max_paid: # ????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {config.rps_game_max_paid} {config.economy_icon}", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid < 1: # ??????????????????0
                    embed=discord.Embed(description=f"{message.author.display_name}???????????????????????????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if rps not in config.rps_type:
                    embed=discord.Embed(description=f"????????? rock(??????), paper(???), scissors(??????)?", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return

                if is_gaming == 1: # ??????????????????????????????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                elif available_time > time.time(): # CD????????????
                    diff_time = int(available_time - time.time())
                    minute = diff_time // 60
                    second = diff_time % 60
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {minute} ??? {second} ???????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    # return
                else:
                    db.WSQL(f'UPDATE condition_flags SET "rps_game_exist"=1 WHERE "uid"={user_uid};')
                    await rpsGame(message, user_uid, paid, crt_money, rps)
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}battle": # !battle {amount} @someone
            try:
                paid = int(parse[1])
                opp = int(parse[2][3:-1])
                opp_uid = db.fetchOneSQL(f'SELECT "id" FROM "user_group" WHERE "user"={opp} AND "group"={message.guild.id};')
                opp_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={opp_uid}')
                opp_queue = db.fetchOneSQL(f'SELECT "uid" FROM "condition_flags" WHERE "battle_game_opponent"={opp};')
                if opp_queue != None:
                    embed=discord.Embed(description=f"{message.author.display_name} ??????????????????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if crt_money < paid: # ??????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ??????????????? {config.economy_icon} ??????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid > config.battle_game_max_paid: # ????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {config.battle_game_max_paid} {config.economy_icon}", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if paid < 1: # ??????????????????0
                    embed=discord.Embed(description=f"{message.author.display_name}??????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if opp_money < paid:
                    embed=discord.Embed(description=f"{message.author.display_name}???????????? {config.economy_icon} ????????????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return

                is_gaming = db.fetchOneSQL(f'SELECT "battle_game_exist" FROM "condition_flags" WHERE "uid"={user_uid}')
                available_time = db.fetchOneSQL(f'SELECT "next_battle_game_time" FROM "condition_flags" WHERE "uid"={user_uid}')
                if is_gaming == 1: # ??????????????????????????????????????????
                    embed=discord.Embed(description=f"{message.author.display_name} ????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                elif available_time > time.time(): # CD????????????
                    diff_time = int(available_time - time.time())
                    minute = diff_time // 60
                    second = diff_time % 60
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????? {minute} ??? {second} ???????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    # return
                else:
                    embed=discord.Embed(description=f"{message.author.display_name}?????? <@!{opp}> ????????? {paid} ?????????????????????\n<@!{opp}>??????`{config.prefix}accept`??????????????????`{config.prefix}reject`????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    db.WSQL(f'UPDATE condition_flags SET "battle_game_exist"=1 WHERE "uid"={user_uid};')
                    db.WSQL(f'UPDATE condition_flags SET "battle_game_opponent"="{opp}" WHERE "uid"={user_uid};')
                    db.WSQL(f'UPDATE condition_flags SET "battle_game_timeout"="{time.time()+config.battle_game_timeout}" WHERE "uid"={user_uid};')
                    db.WSQL(f'UPDATE condition_flags SET "battle_game_paid"={paid} WHERE "uid"={user_uid};')
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}accept": # !accept
            try:
                opponent_uid = db.fetchOneSQL(f'SELECT "uid" FROM "condition_flags" WHERE "battle_game_opponent"={message.author.id}')
                print("UID ", opponent_uid, " attack ", message.author.id)
                if opponent_uid == None:
                    embed=discord.Embed(description=f"??????????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                opponent_paid = db.fetchOneSQL(f'SELECT "battle_game_paid" FROM "condition_flags" WHERE "uid"={opponent_uid}')
                print(f'SELECT "battle_game_paid" FROM "condition_flags" WHERE "battle_game_paid"={opponent_uid}')
                opponent = db.fetchOneSQL(f'SELECT "user" FROM "user_group" WHERE "id"={opponent_uid}')
                await battleGame(message, opponent, message.author.id, opponent_paid, opponent_uid, user_uid)
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}reject": # !reject
            try:
                opponent_uid = db.fetchOneSQL(f'SELECT "uid" FROM "condition_flags" WHERE "battle_game_opponent"={message.author.id}')
                if opponent_uid == None:
                    embed=discord.Embed(description=f"??????????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                opponent = db.fetchOneSQL(f'SELECT "user" FROM "user_group" WHERE "id"="{opponent_uid}"')
                embed=discord.Embed(description=f"?????? <@!{opponent}> ????????????", color=0xFF3333)
                await message.channel.send(embed=embed)
                db.WSQL(f'UPDATE condition_flags SET "battle_game_opponent"=0, "next_battle_game_time"={time.time()}, "battle_game_exist"=0 WHERE "uid"={opponent_uid};')

            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}work": # !work / !work claim
            try:
                is_working =  db.fetchOneSQL(f'SELECT "working" FROM "condition_flags" WHERE "uid"={user_uid}')
                salary = db.fetchOneSQL(f'SELECT "working_salary" FROM "condition_flags" WHERE "uid"={user_uid}')
                working_timeout =   db.fetchOneSQL(f'SELECT "working_timeout" FROM "condition_flags" WHERE "uid"={user_uid}')
                crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid}')
                print(is_working, salary, working_timeout, crt_money)
                if len(parse) > 1 and parse[1] == "claim":
                    print("Work claim Branch")
                    if salary == 0:
                        embed=discord.Embed(description=f"{message.author.name} ???????????????????????????????????????????????????", color=0xFF3333)
                        await message.channel.send(embed=embed)
                        return
                    elif time.time() >= working_timeout:
                        new_money = crt_money + salary
                        next_salary = random.randint(config.work_salary_min, config.work_salary_max)
                        embed=discord.Embed(description=f"{message.author.display_name}?????????????????????????????? {salary} {config.economy_icon}", color=0x00eeff)
                        await message.channel.send(embed=embed)
                        db.WSQL(f'UPDATE "money" SET "money"={new_money} WHERE "uid"={user_uid};')
                        # db.WSQL(f'UPDATE condition_flags SET "working"=0, "working_get_paid"=1 WHERE "uid"={user_uid};')
                        db.WSQL(f'UPDATE condition_flags SET "working"=0, "working_salary"=0 WHERE "uid"={user_uid};')
                    else:
                        diff_time = int(working_timeout - time.time())
                        minute = diff_time // 60
                        second = diff_time % 60
                        embed=discord.Embed(description=f"{message.author.name} ??????????????????????????????R??? {minute} ??? {second} ?????????????????????", color=0xFF3333)
                        await message.channel.send(embed=embed)
                    return
                    
                print("Work Branch")
                if is_working == 1 and time.time() < working_timeout:
                    diff_time = int(working_timeout - time.time())
                    minute = diff_time // 60
                    second = diff_time % 60
                    embed=discord.Embed(description=f"{message.author.display_name}????????????????????????????????? {minute} ??? {second} ???????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
                if is_working == 1 and time.time() >= working_timeout:
                    new_money = crt_money + salary
                    next_salary = random.randint(config.work_salary_min, config.work_salary_max)
                    embed=discord.Embed(description=f"{message.author.display_name}?????????????????????????????????????????????????????? {salary} {config.economy_icon}??? ?????? 1 ???????????? !work claim ?????? {next_salary} {config.economy_icon} ??????????????????", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    db.WSQL(f'UPDATE "money" SET "money"={new_money} WHERE "uid"={user_uid};')
                    db.WSQL(f'UPDATE condition_flags SET "working"=1, "working_timeout"={time.time()+config.work_time}, "working_salary"={next_salary} WHERE "uid"={user_uid};')
                    return
                if is_working == 0:
                    next_salary = random.randint(config.work_salary_min, config.work_salary_max)
                    db.WSQL(f'UPDATE condition_flags SET "working"=1, "working_salary"={next_salary}, "working_timeout"={time.time()+config.work_time} WHERE "uid"={user_uid};')
                    embed=discord.Embed(description=f"{message.author.display_name}????????????????????????????????? 1??? ??????????????? {next_salary} {config.economy_icon}???", color=0x00eeff)
                    await message.channel.send(embed=embed)
                    return
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}coins": # !coins
            try:
                base_coins = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid};')
                embed=discord.Embed(title=f"**{message.author.display_name} ???????????????**")
                embed.add_field(name=f"{config.economy_name} {config.economy_icon}", value=f"{base_coins}", inline=False)
                vcoins = db.fetchAllSQL(f'SELECT "coin", "coin_amount", "avg_price" FROM "coin_assets" WHERE "uid"={user_uid};')
                exist_coin_names = []
                for row in vcoins:
                    exist_coin_names.append(row[0])
                # print(exist_coin_names)
                if len(exist_coin_names) == 0:
                    await message.channel.send(embed=embed)
                    return
                cg = CoinGeckoAPI()
                result = cg.get_price(ids=exist_coin_names, vs_currencies='usd')
                for row in vcoins:
                    if row[1] == 0:
                        continue
                    crt_price = result[row[0]]["usd"]
                    reward = (crt_price - row[2])/crt_price * 100
                    if reward < 0:
                        embed.add_field(name=f"{row[0]}", value=f"?????? {row[1]:.4f} ??????????????? {crt_price*row[1]:.4f} {config.economy_icon}\n ???????????? {row[2]:.4f} ???? {reward:.6f}%", inline=False)
                    else:
                        embed.add_field(name=f"{row[0]}", value=f"?????? {row[1]:.4f} ??????????????? {crt_price*row[1]:.4f} {config.economy_icon}\n ???????????? {row[2]:.4f} ???? {reward:.6f}%", inline=False)
                await message.channel.send(embed=embed)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}coin-price": # !coins-price
            cg = CoinGeckoAPI()
            result = cg.get_price(ids=['bitcoin', 'litecoin', 'ethereum', 'tether', 'dogecoin', 'iota'], vs_currencies='usd')
            embed=discord.Embed(title="**???????????????????????????**")
            embed.set_thumbnail(url="https://firebasestorage.googleapis.com/v0/b/chatroom-5b1d0.appspot.com/o/rgd.jpg?alt=media&token=947e8bdf-d685-431c-8ec5-98e26e5d29d7")
            for key, val in config.coin_names2full.items():
                embed.add_field(name=f"{key} - {val}", value=f"{config.economy_icon} {result[val]['usd']} ", inline=False)
            await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}buy-coin": # !buy-coin 50 btc
            # try:
            paid = int(parse[1])
            coin_name = parse[2].lower()
            if coin_name not in config.coin_names:
                embed=discord.Embed(description=f"????????????????????????????????????", color=0xFF3333)
                await message.channel.send(embed=embed)
                return
            if crt_money < paid: # ??????????????????
                embed=discord.Embed(description=f"{message.author.display_name} ??? {config.economy_icon} ???????????????", color=0x00eeff)
                await message.channel.send(embed=embed)
                return
            if paid < 1: # ??????????????????0
                embed=discord.Embed(description=f"{message.author.display_name}??????????????????????????????", color=0x00eeff)
                await message.channel.send(embed=embed)
                return
            await buyVCoin(message, user_uid, paid, coin_name)
            # except Exception as e:
            #     print(e)
            #     print(traceback.format_exc())
            #     embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
            #     await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}sell-coin":
            try:
                paid = float(parse[1])
                coin_name = parse[2].lower()
                
                if coin_name not in config.coin_names:
                    embed=discord.Embed(description=f"????????????????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                
                coin_name = config.coin_names2full[coin_name]
                cg = CoinGeckoAPI()
                result = cg.get_price(ids=[coin_name], vs_currencies='usd')
                crt_price = result[coin_name]["usd"]
                crt_vcoin = db.fetchOneSQL(f'SELECT "coin_amount" FROM "coin_assets" WHERE "uid"={user_uid} AND "coin"="{coin_name}"')
                if crt_vcoin == None:
                    embed=discord.Embed(description=f"{message.author.display_name}???{coin_name} ????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                if paid < 1:
                    embed=discord.Embed(description=f"{message.author.display_name}???{coin_name} ?????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                if crt_vcoin < paid/crt_price:
                    embed=discord.Embed(description=f"{message.author.display_name}???{coin_name} ????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                if crt_vcoin * crt_price < 1:
                    embed=discord.Embed(description=f"{message.author.display_name} ?????????????????????????????????", color=0xFF3333)
                    await message.channel.send(embed=embed)
                    return
                expected_reward = int(paid)
                crt_vcoin -= paid/crt_price
                
                db.WSQL(f'UPDATE "coin_assets" SET "coin_amount"={crt_vcoin} WHERE "uid"={user_uid} AND "coin"="{coin_name}"')
                crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid};')
                db.WSQL(f'UPDATE "money" SET "money"={crt_money+expected_reward} WHERE "uid"={user_uid}')
                if crt_vcoin == 0:
                    db.WSQL(f'UPDATE "coin_assets" SET "avg_price"=0 WHERE "uid"={user_uid}" AND "coin"="{coin_name}"')
                embed=discord.Embed(description=f"{message.author.display_name} ???????????? {expected_reward} {config.economy_icon}", color=0xFF3333)
                await message.channel.send(embed=embed)
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
            
            # await buyVCoin(message, user_uid, paid, coin_name)
        elif parse[0] == f"{config.prefix}stocks": # !stocks:
            trade_msg = await message.channel.send(content="?????????...")
            base_coins = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid};')
            embed=discord.Embed(title=f"**{message.author.display_name} ???????????????**")
            embed.add_field(name=f"{config.economy_name} {config.economy_icon}", value=f"{base_coins}", inline=False)
            stocks = db.fetchAllSQL(f'SELECT "stock", "stock_amount", "avg_price" FROM "stock_assets" WHERE "uid"={user_uid};')
            finnhub_client = finnhub.Client(api_key=os.environ["STOCK_API_TOKEN"])
            diff_sum = 0
            for row in stocks:
                if row[1] == 0:
                    continue
                if row[2] == 0:
                    # embed.add_field(name=f"{row[0]} ??? {row[1]} ???", value=f"????????? {row[2]:.6f} {config.economy_icon}????????????? 0 % ", inline=False)
                    continue
                price = finnhub_client.quote(row[0])["c"]
                if price>=row[2]:
                    embed.add_field(name=f"{row[0]} ??? {row[1]} ???", value=f"????????? {row[2]:.6f} {config.economy_icon}????????????? {(price-row[2])*row[1]:.4f} ( {(price-row[2])/row[2]*100:.4f} % )", inline=False)
                else:
                    embed.add_field(name=f"{row[0]} ??? {row[1]} ???", value=f"????????? {row[2]:.6f} {config.economy_icon}????????????? {(price-row[2])*row[1]:.4f} ( {(price-row[2])/row[2]*100:.4f} % )", inline=False)
                diff_sum += (price-row[2])*row[1]
                # embed.add_field(name=f"{row[0]} ??? {row[1]} ???", value=f"????????? {row[2]:.6f} {config.economy_icon}", inline=False)
            # await message.channel.send(embed=embed)
            embed.add_field(name=f"???????????????", value=f"{diff_sum:.6f} {config.economy_icon}", inline=False)
            await trade_msg.edit(content="", embed=embed)
        elif parse[0] == f"{config.prefix}buy-stock": # !buy-stock 50 intc
            # try:
            trade_msg = await message.channel.send(content="?????????...")
            stock_buy_amount = int(parse[1])
            stock_name = parse[2].upper()
            finnhub_client = finnhub.Client(api_key=os.environ["STOCK_API_TOKEN"])
            price = finnhub_client.quote(stock_name)["c"]
            if price == 0:
                embed=discord.Embed(description=f"{message.author.display_name}???????????????", color=0xFF3333)
                # await message.channel.send(embed=embed)
                await trade_msg.edit(content="", embed=embed)
                return
            if crt_money < math.ceil(stock_buy_amount*price): # ??????????????????
                embed=discord.Embed(description=f"{message.author.display_name} ??? {config.economy_icon} ???????????????", color=0x00eeff)
                await trade_msg.edit(content="", embed=embed)
                # await message.channel.send(embed=embed)
                return
            if stock_buy_amount < 1: # ??????????????????0
                embed=discord.Embed(description=f"{message.author.display_name}????????????????????????", color=0x00eeff)
                await trade_msg.edit(content="", embed=embed)
                # await message.channel.send(embed=embed)
                return
            await buyStock(message, trade_msg, user_uid, stock_buy_amount, stock_name, price)
        elif parse[0] == f"{config.prefix}sell-stock": # !sell-stock 50 intc
            try:
                trade_msg = await message.channel.send(content="?????????...")
                stock_sell_amount = int(parse[1])
                stock_name = parse[2].upper()
                
                finnhub_client = finnhub.Client(api_key=os.environ["STOCK_API_TOKEN"])
                price = finnhub_client.quote(stock_name)["c"]
                if price == 0:
                    embed=discord.Embed(description=f"{message.author.display_name}???????????????", color=0xFF3333)
                    # await message.channel.send(embed=embed)
                    await trade_msg.edit(content="", embed=embed)
                    return
                crt_stock = db.fetchOneSQL(f'SELECT "stock_amount" FROM "stock_assets" WHERE "uid"={user_uid} AND "stock"="{stock_name}"')
                if crt_stock == None:
                    embed=discord.Embed(description=f"{message.author.display_name}???{stock_name} ???????????? ??????????????????", color=0xFF3333)
                    # await message.channel.send(embed=embed)
                    await trade_msg.edit(content="", embed=embed)
                    return
                if stock_sell_amount < 1:
                    embed=discord.Embed(description=f"{message.author.display_name}???{stock_name} ????????????", color=0xFF3333)
                    # await message.channel.send(embed=embed)
                    await trade_msg.edit(content="", embed=embed)
                    return
                if crt_stock < stock_sell_amount:
                    embed=discord.Embed(description=f"{message.author.display_name}???{stock_name} ???????????? ??????????????????", color=0xFF3333)
                    # await message.channel.send(embed=embed)
                    await trade_msg.edit(content="", embed=embed)
                    return
                expected_reward = math.floor(stock_sell_amount * price)
                crt_stock -= stock_sell_amount
                
                db.WSQL(f'UPDATE "stock_assets" SET "stock_amount"={crt_stock} WHERE "uid"={user_uid} AND "stock"="{stock_name}"')
                crt_money = db.fetchOneSQL(f'SELECT "money" FROM "money" WHERE "uid"={user_uid};')
                db.WSQL(f'UPDATE "money" SET "money"={crt_money+expected_reward} WHERE "uid"={user_uid}')
                if crt_stock == 0:
                    db.WSQL(f'UPDATE "stock_assets" SET "avg_price"=0 WHERE "uid"={user_uid} AND "stock"="{stock_name}"')
                embed=discord.Embed(description=f"{message.author.display_name} ???????????? {stock_sell_amount} ??? {stock_name} \n???????????? {price} {config.economy_icon} ????????? {expected_reward} {config.economy_icon} ??????", color=0xFF3333)
                # await message.channel.send(embed=embed)
                await trade_msg.edit(content="", embed=embed)
            except Exception as e:
                print(e)
                embed=discord.Embed(description=f"Unexpected Error", color=0xFF3333)
                await message.channel.send(embed=embed)
            
            pass
        elif parse[0] == f"{config.prefix}buy-stock": # !sell-stock 50 intc
            pass
        elif parse[0] == f"{config.prefix}shop": # !shop
            embed=discord.Embed(title=f"**{message.guild.name} ??????**", description="?????? `!shop [item name]` ????????????????????????????????????????????? \n?????? `!buy [item name]` ???????????????\n\n???? ????????????????????????")
            embed.add_field(name=f"?????? - {config.economy_icon} 50", value="???????????????", inline=False)
            await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}richest": # !richest
            guild_user_list = db.fetchAllSQL(f'SELECT "user_group"."id","user_group"."user", "money"."money" FROM "user_group" JOIN "money" ON "user_group"."id"="money"."uid" WHERE "user_group"."group"="{message.guild.id}";')
            result = sorted(guild_user_list, key=lambda x:x[2], reverse=True)
            embed=discord.Embed(title=f"**{message.guild.name} ??????????????????**")
            money_sum = 0
            for row in guild_user_list:
                money_sum+=row[2]
            embed.add_field(name=f"???????????????????", value=f"{config.economy_icon} {money_sum}", inline=False)
            for idx, row in enumerate(result):
                print(row[1])
                user_name = await client.fetch_user(row[1])
                if idx == 0:
                    embed.add_field(name=f"????{idx+1} - {user_name.name}", value=f"{config.economy_icon} {row[2]}", inline=False)
                elif idx == 1:
                    embed.add_field(name=f"????{idx+1} - {user_name.name}", value=f"{config.economy_icon} {row[2]}", inline=False)
                elif idx == 2:
                    embed.add_field(name=f"????{idx+1} - {user_name.name}", value=f"{config.economy_icon} {row[2]}", inline=False)
                elif idx == 9:
                    break
                else:
                    embed.add_field(name=f"{idx+1} - {user_name.name}", value=f"{config.economy_icon} {row[2]}", inline=False)
                
            # print(result)
            # embed=discord.Embed(description=f"**?????????**")
            await message.channel.send(embed=embed)
        elif parse[0] == f"{config.prefix}help": # !help:
            embed=discord.Embed(title="**MEE69amble ???????????????**")
            embed.add_field(name="????????????", value=f"`{config.prefix}daily`", inline=False)
            embed.add_field(name="????????????", value=f"`{config.prefix}dice [money]`", inline=False)
            embed.add_field(name="????????????????????????", value=f"`{config.prefix}work`", inline=False)
            embed.add_field(name="???????????????????????????", value=f"`{config.prefix}coins`", inline=False)
            embed.add_field(name="??????????????????????????????", value=f"`{config.prefix}richest`", inline=False)
            embed.add_field(name="???????????????", value=f"`{config.prefix}rps [money] [rock,scissors,paper]`", inline=False)
            embed.add_field(name="???????????????????????????", value=f"`{config.prefix}battle [money] [@someone]`", inline=False)
            embed.add_field(name="??????????????????", value=f"`{config.prefix}buy-coin [?????????????????????] [btc,ltc,eth,usdt,doge,iota,xrp]`", inline=False)
            embed.add_field(name="??????????????????", value=f"`{config.prefix}sell-coin [?????????????????????] [btc,ltc,eth,usdt,doge,iota,xrp]`", inline=False)
            embed.add_field(name="??????????????????", value=f"`{config.prefix}coin-price`", inline=False)
            embed.add_field(name="????????????????????????", value=f"`{config.prefix}stocks`", inline=False)
            embed.add_field(name="??????????????????", value=f"`{config.prefix}buy-stock [????????????:?????????] [????????????]`", inline=False)
            embed.add_field(name="??????????????????", value=f"`{config.prefix}sell-stock [????????????:?????????] [????????????]`", inline=False)
            await message.channel.send(embed=embed)
db = DB()
client.run(os.environ["DISCORD_BOT_TOKEN"])