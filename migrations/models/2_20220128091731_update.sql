-- upgrade --
CREATE UNIQUE INDEX "uid_messagetome_server__06bdfb" ON "messagetomessage" ("server_id", "vk_message_id");
-- downgrade --
DROP INDEX "uid_messagetome_server__06bdfb";
