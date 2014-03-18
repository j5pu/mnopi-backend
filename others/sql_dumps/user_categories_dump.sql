-- MySQL dump 10.13  Distrib 5.5.32, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: mnopi
-- ------------------------------------------------------
-- Server version	5.5.32-0ubuntu0.13.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `user_category`
--

DROP TABLE IF EXISTS `user_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `taxonomy` varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_category`
--

LOCK TABLES `user_category` WRITE;
/*!40000 ALTER TABLE `user_category` DISABLE KEYS */;
INSERT INTO `user_category` VALUES (1,'Hate/Discrimination','opendns'),(2,'Travel','opendns'),(3,'Ecommerce/Shopping','opendns'),(4,'Visual Search Engines','opendns'),(5,'Forums/Message boards','opendns'),(6,'Gambling','opendns'),(7,'Dating','opendns'),(8,'News/Media','opendns'),(9,'Tasteless','opendns'),(10,'Drugs','opendns'),(11,'Lingerie/Bikini','opendns'),(12,'Jobs/Employment','opendns'),(13,'Photo Sharing','opendns'),(14,'Instant Messaging','opendns'),(15,'Business Services','opendns'),(16,'Sexuality','opendns'),(17,'Auctions','opendns'),(18,'Proxy/Anonymizer','opendns'),(19,'Portals','opendns'),(20,'Non-Profits','opendns'),(21,'Adult Themes','opendns'),(22,'Web Spam','opendns'),(23,'Academic Fraud','opendns'),(24,'Pornography','opendns'),(25,'Music','opendns'),(26,'Parked Domains','opendns'),(27,'Humor','opendns'),(28,'Alcohol','opendns'),(29,'Educational Institutions','opendns'),(30,'Sports','opendns'),(31,'Weapons','opendns'),(32,'Video Sharing','opendns'),(33,'File Storage','opendns'),(34,'Tobacco','opendns'),(35,'Government','opendns'),(36,'Automotive','opendns'),(37,'Research/Reference','opendns'),(38,'Health and Fitness','opendns'),(39,'Software/Technology','opendns'),(40,'Anime/Manga/Webcomic','opendns'),(41,'Television','opendns'),(42,'Blogs','opendns'),(43,'Podcasts','opendns'),(44,'Movies','opendns'),(45,'Search Engines','opendns'),(46,'Games','opendns'),(47,'Advertising','opendns'),(48,'P2P/File sharing','opendns'),(49,'Social Networking','opendns'),(50,'Nudity','opendns'),(51,'Financial Institutions','opendns'),(52,'Webmail','opendns'),(53,'Radio','opendns'),(54,'Chat','opendns'),(55,'Politics','opendns'),(56,'Classifieds','opendns'),(57,'Religious','opendns');
/*!40000 ALTER TABLE `user_category` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-03-18 13:07:22