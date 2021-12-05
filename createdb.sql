CREATE TABLE "Server" (
	"server_id"	INTEGER NOT NULL UNIQUE,
	"server_default_channel"	INTEGER,
	"default_image_channel"	INTEGER,
	PRIMARY KEY("server_id")
);

CREATE TABLE "ServerChannelAlias" (
	"server_id"	INTEGER NOT NULL UNIQUE,
	"channel_id"	INTEGER,
	"alias"	TEXT,
	PRIMARY KEY("server_id"),
	UNIQUE("server_id","alias"),
	FOREIGN KEY("server_id") REFERENCES "Server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "ServerToChat" (
	"server_id"	INTEGER NOT NULL UNIQUE,
	"chat_id"	INTEGER,
	FOREIGN KEY("server_id") REFERENCES "Server"("server_id") ON DELETE CASCADE
);

