-- upgrade --
ALTER TABLE "galleryimages" ADD "video_link" TEXT DEFAULT '' NOT NULL;
ALTER TABLE "galleryimages" ADD "video_name" TEXT DEFAULT '' NOT NULL;
-- downgrade --
ALTER TABLE "galleryimages" DROP COLUMN "video_link";
ALTER TABLE "galleryimages" DROP COLUMN "video_name";
