-- upgrade --
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "discordnickname" (
    "discord_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "nickname" VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS "galleryimages" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "gallery_id" INT NOT NULL,
    "image_url" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "server" (
    "server_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "server_default_channel" INT,
    "default_image_channel" INT,
    "duplex_channel" INT,
    "chat_id" INT
);
CREATE TABLE IF NOT EXISTS "messagetomessage" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "channel_id" INT NOT NULL,
    "discord_message_id" INT NOT NULL,
    "vk_message_id" INT NOT NULL,
    "vk_timestamp" INT NOT NULL,
    "server_id" INT NOT NULL REFERENCES "server" ("server_id") ON DELETE CASCADE,
    CONSTRAINT "uid_messagetome_channel_e2b55c" UNIQUE ("channel_id", "discord_message_id")
);
CREATE TABLE IF NOT EXISTS "serverchannelalias" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "channel_id" INT NOT NULL,
    "alias" VARCHAR(100) NOT NULL,
    "server_id" INT NOT NULL REFERENCES "server" ("server_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "vknickname" (
    "vk_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "nickname" VARCHAR(100) NOT NULL
);
