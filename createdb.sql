CREATE TABLE "Server" (
	"server_id"	INTEGER NOT NULL UNIQUE,
	"server_default_channel"	INTEGER,
	"default_image_channel"	INTEGER,
	"duplex_channel"	INTEGER,
	PRIMARY KEY("server_id")
);

CREATE TABLE "ServerChannelAlias" (
	"server_id"	INTEGER NOT NULL,
	"channel_id"	INTEGER,
	"alias"	TEXT,
	UNIQUE("server_id","alias"),
	FOREIGN KEY("server_id") REFERENCES "Server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "ServerToChat" (
	"server_id"	INTEGER NOT NULL UNIQUE,
	"chat_id"	INTEGER NOT NULL UNIQUE,
	FOREIGN KEY("server_id") REFERENCES "Server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "VkNickName" (
	"vk_id"	INTEGER NOT NULL UNIQUE,
	"nickname"	TEXT,
	PRIMARY KEY("vk_id")
);

CREATE TABLE "DiscordNickName" (
	"discord_id"	INTEGER NOT NULL UNIQUE,
	"nickname"	TEXT,
	PRIMARY KEY("discord_id")
);

CREATE TABLE "GalleryToImage" (
	"gallery_id"	INTEGER NOT NULL,
	"image_url"	TEXT NOT NULL
);

CREATE TABLE "MessageToMessage" (
	"server_id"	INTEGER NOT NULL,
	"channel_id"	INTEGER NOT NULL,
	"chat_id"	INTEGER NOT NULL,
	"vk_message_id"	INTEGER NOT NULL,
	"vk_timestamp" INTEGER NOT NULL,
	"discord_message_id"	INTEGER NOT NULL,
	FOREIGN KEY("chat_id") REFERENCES "ServerToChat"("chat_id") ON DELETE CASCADE,
	FOREIGN KEY("server_id") REFERENCES "ServerToChat"("server_id") ON DELETE CASCADE,
	UNIQUE("channel_id","discord_message_id")
);
