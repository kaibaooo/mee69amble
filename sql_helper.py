import sqlite3

class DB:
    def __init__(self):
        self.con = sqlite3.connect('db.sqlite')
        self.cur = self.con.cursor()
    def WSQL(self, sql_str):
        self.cur.execute(f'''{sql_str}''')
        self.con.commit()
    def fetchOneSQL(self, sql_str):
        data = self.cur.execute(f'''{sql_str}''')
        result = data.fetchone()
        if result == None:
            return None
        return result[0]
    def fetchAllSQL(self, sql_str):
        data = self.cur.execute(f'''{sql_str}''')
        result = data.fetchall()
        return result
    def close(self):
        self.con.close()
    def test(self):
        data = self.cur.execute('SELECT "setting_value" FROM "bot_settings" WHERE "setting_name"="daily_date"')
        result = data.fetchone()
        print(result)
        # result = data.fetchone()
        # print(len(result))
        # print(data)
        # print(result)
        for row in data:
            print(row)
        # pass
# db = DB()
# db.test()
# db.close()
