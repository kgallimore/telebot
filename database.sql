/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


CREATE DATABASE IF NOT EXISTS `telegram` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE = utf8mb4_unicode_ci */;
USE `telegram`;


CREATE TABLE IF NOT EXISTS `giveaways` (
  `giveaway_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `chat_id` bigint(20) NOT NULL,
  `username` text DEFAULT NULL,
  `first_name` text DEFAULT NULL,
  `giveaway_details` varchar(125) NOT NULL,
  `status` text NOT NULL DEFAULT 'active',
  PRIMARY KEY (`giveaway_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `participants` (
  `giveaway_id` int(11) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `chat_id` bigint(20) NOT NULL,
  `username` text DEFAULT NULL,
  `first_name` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `settings` (
  `chat_id` bigint(20) NOT NULL,
  `welcome` mediumtext DEFAULT '',
  `store` mediumtext DEFAULT '',
  `rules` mediumtext DEFAULT '',
  UNIQUE KEY `chat_id` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `verified` (
  `chat_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `services` varchar(50) DEFAULT NULL,
  `username` text DEFAULT NULL,
  `first_name` text DEFAULT NULL,
  `input_id` bigint(20) NOT NULL,
  `input_username` text DEFAULT NULL,
  `input_first_name` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `warnings` (
  `chat_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `username` text DEFAULT NULL,
  `first_name` text DEFAULT NULL,
  `reason` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `users` (
  `chat_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `username` text DEFAULT NULL,
  `first_name` text DEFAULT NULL,
  `join_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;


-- Updates
ALTER DATABASE telegram CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
ALTER TABLE giveaways CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE participants CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE settings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE verified CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE warnings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
