-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: library_management
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `library_management`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `library_management` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `library_management`;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `adminID` int NOT NULL AUTO_INCREMENT,
  `userID` int NOT NULL,
  PRIMARY KEY (`adminID`),
  UNIQUE KEY `userID` (`userID`),
  CONSTRAINT `fk_admin_user` FOREIGN KEY (`userID`) REFERENCES `users` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `books`
--

DROP TABLE IF EXISTS `books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `books` (
  `bookID` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `publisher` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `publication_year` int DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Available',
  `quantity` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`bookID`),
  CONSTRAINT `chk_book_quantity` CHECK ((`quantity` >= 0)),
  CONSTRAINT `chk_book_status` CHECK ((`status` in (_utf8mb4'Available',_utf8mb4'Unavailable')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `borrowing_details`
--

DROP TABLE IF EXISTS `borrowing_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `borrowing_details` (
  `detailID` int NOT NULL AUTO_INCREMENT,
  `borrowingID` int NOT NULL,
  `bookID` int NOT NULL,
  `return_condition` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `return_date` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`detailID`),
  KEY `fk_detail_borrowing` (`borrowingID`),
  KEY `fk_detail_book` (`bookID`),
  CONSTRAINT `fk_detail_book` FOREIGN KEY (`bookID`) REFERENCES `books` (`bookID`),
  CONSTRAINT `fk_detail_borrowing` FOREIGN KEY (`borrowingID`) REFERENCES `borrowing_records` (`borrowingID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `borrowing_records`
--

DROP TABLE IF EXISTS `borrowing_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `borrowing_records` (
  `borrowingID` int NOT NULL AUTO_INCREMENT,
  `readerID` int NOT NULL,
  `adminID` int DEFAULT NULL,
  `borrow_date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `due_date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `return_date` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pending',
  `renewal_count` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`borrowingID`),
  KEY `fk_borrowing_reader` (`readerID`),
  KEY `fk_borrowing_admin` (`adminID`),
  CONSTRAINT `fk_borrowing_admin` FOREIGN KEY (`adminID`) REFERENCES `admins` (`adminID`),
  CONSTRAINT `fk_borrowing_reader` FOREIGN KEY (`readerID`) REFERENCES `readers` (`readerID`),
  CONSTRAINT `chk_borrowing_status` CHECK ((`status` in (_utf8mb4'Pending',_utf8mb4'Borrowed',_utf8mb4'ReturnRequested',_utf8mb4'Returned',_utf8mb4'Rejected'))),
  CONSTRAINT `chk_renewal_count` CHECK ((`renewal_count` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fines`
--

DROP TABLE IF EXISTS `fines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fines` (
  `fineID` int NOT NULL AUTO_INCREMENT,
  `borrowingID` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fine_date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Unpaid',
  `payment_date` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `adminID` int DEFAULT NULL,
  PRIMARY KEY (`fineID`),
  KEY `fk_fine_borrowing` (`borrowingID`),
  KEY `fk_fine_admin` (`adminID`),
  CONSTRAINT `fk_fine_admin` FOREIGN KEY (`adminID`) REFERENCES `admins` (`adminID`),
  CONSTRAINT `fk_fine_borrowing` FOREIGN KEY (`borrowingID`) REFERENCES `borrowing_records` (`borrowingID`),
  CONSTRAINT `chk_fine_amount` CHECK ((`amount` >= 0)),
  CONSTRAINT `chk_payment_status` CHECK ((`payment_status` in (_utf8mb4'Unpaid',_utf8mb4'Paid')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `readers`
--

DROP TABLE IF EXISTS `readers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `readers` (
  `readerID` int NOT NULL AUTO_INCREMENT,
  `userID` int NOT NULL,
  `expiration_date` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`readerID`),
  UNIQUE KEY `userID` (`userID`),
  CONSTRAINT `fk_reader_user` FOREIGN KEY (`userID`) REFERENCES `users` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `userID` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `account_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Active',
  PRIMARY KEY (`userID`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  CONSTRAINT `chk_account_status` CHECK ((`account_status` in (_utf8mb4'Active',_utf8mb4'Locked',_utf8mb4'Inactive'))),
  CONSTRAINT `chk_user_role` CHECK ((`role` in (_utf8mb4'Admin',_utf8mb4'Reader')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-13 15:34:03
