-- upgrade --
CREATE UNIQUE INDEX "uid_serverchann_channel_27675b" ON "serverchannelalias" ("channel_id", "alias");
-- downgrade --
DROP INDEX "uid_serverchann_channel_27675b";
