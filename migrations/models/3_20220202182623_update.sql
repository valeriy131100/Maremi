-- upgrade --
ALTER TABLE "vknickname" RENAME TO "vkuser";
ALTER TABLE "discordnickname" RENAME TO "discorduser";
-- downgrade --
ALTER TABLE "vkuser" RENAME TO "vknickname";
ALTER TABLE "discorduser" RENAME TO "discordnickname";
