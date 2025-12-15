-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 10, 2023 at 04:25 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4


START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_arduino`
--

-- --------------------------------------------------------

--
-- Table structure for table `students_attendance`
--

CREATE TABLE `students_attendance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(255) DEFAULT NULL,
  `UID` varchar(255) DEFAULT NULL,
  `Attendance` varchar(255) DEFAULT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `Course_code` varchar(255) DEFAULT NULL,
   PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students_attendance`
--

INSERT INTO `students_attendance` (`Name`, `UID`, `Attendance`, `Timestamp`, `Course_code`) VALUES
('John Miles', '43B4C495', 'Present', '2023-05-31 05:37:34', 'CSC 302'),
('John Miles', '43B4C495', 'Absent',  '2023-05-31 05:37:38', 'CSC 401');



/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_arduino`
--

-- --------------------------------------------------------

--
-- Table structure for table `courses`
CREATE TABLE `courses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
 `Course_name` varchar(255) DEFAULT NULL,
 `Course_code` varchar(255) DEFAULT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
   PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `attendance_records`
--

INSERT INTO `courses` (`Course_name`, `Course_code`, `Timestamp`) VALUES
('Hardware system', 'CSC 302', '2023-05-31 07:01:23'),
('Computer Architecture', 'CSC 401', '2023-05-31 07:01:27');



/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_arduino`
--

-- --------------------------------------------------------

--
-- Table structure for table `attendance_records`
--
CREATE TABLE `attendance_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(255) DEFAULT NULL,
  `UID` varchar(255) DEFAULT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `Course_code` varchar(255) DEFAULT NULL,
  `Present_Count` int(11) DEFAULT NULL,
  `Absent_Count` int(11) DEFAULT NULL,
   PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `attendance_records`
--

INSERT INTO `attendance_records` (`Name`, `UID`, `Timestamp`, `Course_code`, `Present_Count`, `Absent_Count`) VALUES
('John Miles', '43B4C495', '2023-05-31 07:01:23', 'CSC 302', 18, 4),
('Fujiwara Kaede', '63B001A6', '2023-05-31 07:01:27', 'CSC 401', 8, 0);


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_arduino`
--

-- --------------------------------------------------------

--
-- Table structure for table `students`
CREATE TABLE `students` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
 `Name` varchar(255) DEFAULT NULL,
  `UID` varchar(255) DEFAULT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `Department` varchar(100) DEFAULT NULL,
  `Level` int(255) DEFAULT NULL,
  `Matric_Number` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`Name`, `UID`, `Timestamp`, `Department`, `Level`, `Matric_Number`) VALUES
('Ovwigho kevwe', '43B4C495', '2023-05-31 07:01:23', 'Software Engineering', 400, 'ADUN/FS/20/448');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
