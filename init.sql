CREATE TABLE "bot_settings" (
	"setting_name"	TEXT,
	"setting_value"	TEXT
);
CREATE TABLE "coin_assets" (
	"uid"	INTEGER,
	"coin"	TEXT DEFAULT 0,
	"coin_amount"	REAL DEFAULT 0,
	"avg_price"	REAL DEFAULT 0
);
CREATE TABLE "condition_flags" (
	"uid"	INTEGER,
	"daily"	INTEGER DEFAULT 0,
	"dice_game_exist"	INTEGER DEFAULT 0,
	"next_dice_game_time"	INTEGER DEFAULT 0,
	"rps_game_exist"	INTEGER DEFAULT 0,
	"next_rps_game_time"	INTEGER DEFAULT 0,
	"battle_game_exist"	INTEGER DEFAULT 0,
	"next_battle_game_time"	INTEGER DEFAULT 0,
	"battle_game_opponent"	TEXT DEFAULT 0,
	"battle_game_timeout"	INTEGER DEFAULT 0,
	"battle_game_paid"	INTEGER DEFAULT 0,
	"working"	INTEGER DEFAULT 0,
	"working_timeout"	INTEGER DEFAULT 0,
	"working_get_paid"	INTEGER DEFAULT 0,
	"working_salary"	INTEGER DEFAULT 0,
	FOREIGN KEY("uid") REFERENCES "user_group"("id") ON DELETE CASCADE,
	PRIMARY KEY("uid")
);
CREATE TABLE "items" (
	"id"	INTEGER,
	"name"	TEXT,
	"price"	INTEGER,
	"desciption"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "money" (
	"uid"	INTEGER,
	"money"	NUMERIC DEFAULT 0,
	FOREIGN KEY("uid") REFERENCES "user_group"("id") ON DELETE CASCADE,
	PRIMARY KEY("uid")
);
CREATE TABLE "user_group" (
	"id"	INTEGER,
	"user"	TEXT,
	"group"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "stock_assets" (
	"uid"	INTEGER,
	"stock"	TEXT,
	"avg_price"	NUMERIC,
	"stock_amount"	INTEGER,
	FOREIGN KEY("uid") REFERENCES "user_group"("id") ON DELETE CASCADE
)