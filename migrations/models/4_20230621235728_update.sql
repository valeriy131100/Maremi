-- upgrade --
DROP INDEX "uid_serverchann_channel_27675b";
CREATE UNIQUE INDEX "uid_serverchann_server__c8633c" ON "serverchannelalias" ("server_id", "alias");
-- downgrade --
CREATE UNIQUE INDEX "uid_serverchann_server__c8633c" ON "serverchannelalias" ("server_id", "alias");
DROP INDEX "uid_serverchann_channel_27675b";
