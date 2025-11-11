-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th10 08, 2025 lúc 02:55 PM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `python_project`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `attendance`
--

CREATE TABLE `attendance` (
  `AttendanceID` int(11) NOT NULL,
  `StudyID` int(11) NOT NULL,
  `Date` date NOT NULL,
  `Time` time NOT NULL,
  `PhotoPath` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `class`
--

CREATE TABLE `class` (
  `ClassID` int(11) NOT NULL,
  `Quantity` int(11) NOT NULL,
  `Rank` varchar(50) DEFAULT NULL,
  `Semester` varchar(45) NOT NULL,
  `DateStart` date NOT NULL,
  `DateEnd` date NOT NULL,
  `Session` varchar(45) DEFAULT NULL,
  `ClassName` varchar(100) NOT NULL,
  `FullClassName` varchar(200) DEFAULT NULL,
  `Teacher_class` varchar(100) DEFAULT NULL,
  `TypeID` int(11) NOT NULL,
  `MajorID` int(11) NOT NULL,
  `ShiftID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `login`
--

CREATE TABLE `login` (
  `id_login` int(11) NOT NULL,
  `email` varchar(50) DEFAULT NULL,
  `phone` varchar(10) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `pass` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `major`
--

CREATE TABLE `major` (
  `MajorID` int(11) NOT NULL,
  `MajorName` varchar(100) NOT NULL,
  `Full_name_mj` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `major`
--

INSERT INTO `major` (`MajorID`, `MajorName`, `Full_name_mj`) VALUES
(1, 'ĐHTT', 'Ngành Công nghệ thông tin'),
(2, 'CĐTM', 'Ngành Dịch vụ thương mại hàng không'),
(3, 'CĐAN', 'Ngành Kiểm tra an ninh hàng không'),
(4, 'ĐHKVLQ', 'Ngành Kinh tế vận tải'),
(5, 'CĐCK', 'Ngành Kỹ thuật bảo dưỡng cơ khí tàu bay'),
(6, 'ĐHKT', 'Ngành Kỹ thuật hàng không'),
(7, 'ĐHNATM', 'Ngành Ngôn ngữ Anh'),
(8, 'ĐHKL', 'Ngành Quản lý hoạt động bay'),
(9, 'ĐHDL', 'Ngành Quản lý dịch vụ và lữ hành'),
(10, 'ĐAQT', 'Ngành Quản trị kinh doanh'),
(11, 'ĐHNL', 'Ngành Quản trị nhân lực');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `shift`
--

CREATE TABLE `shift` (
  `ShiftID` int(11) NOT NULL,
  `ShiftName` varchar(50) NOT NULL,
  `TimeStart` time NOT NULL,
  `TimeEnd` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `shift`
--

INSERT INTO `shift` (`ShiftID`, `ShiftName`, `TimeStart`, `TimeEnd`) VALUES
(1, 'Ca 1', '07:00:00', '10:30:00'),
(2, 'Ca 2', '12:00:00', '15:30:00'),
(3, 'Ca 3', '16:45:00', '20:20:00');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `student`
--

CREATE TABLE `student` (
  `StudentID` int(11) NOT NULL,
  `FullName` varchar(100) NOT NULL,
  `StudentCode` varchar(20) NOT NULL,
  `DefaultClass` varchar(45) DEFAULT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `AcademicYear` varchar(10) DEFAULT NULL,
  `DateOfBirth` date DEFAULT NULL,
  `CitizenID` varchar(20) DEFAULT NULL,
  `PhotoStatus` varchar(10) DEFAULT NULL,
  `StudentPhoto` varchar(255) DEFAULT NULL,
  `MajorID` int(11) NOT NULL,
  `TypeID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `student_embeddings`
--

CREATE TABLE `student_embeddings` (
  `EmbeddingID` int(11) NOT NULL,
  `StudentID` int(11) NOT NULL,
  `Embedding` longblob NOT NULL,
  `EmbeddingDim` int(11) NOT NULL,
  `PhotoPath` varchar(1024) DEFAULT NULL,
  `Quality` float DEFAULT NULL,
  `Source` varchar(100) DEFAULT NULL,
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `study`
--

CREATE TABLE `study` (
  `StudyID` int(11) NOT NULL,
  `StudentID` int(11) NOT NULL,
  `ClassID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `teach`
--

CREATE TABLE `teach` (
  `id_teach` int(50) NOT NULL,
  `id_login` int(11) DEFAULT NULL,
  `ClassID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `type`
--

CREATE TABLE `type` (
  `TypeID` int(11) NOT NULL,
  `TypeName` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `type`
--

INSERT INTO `type` (`TypeID`, `TypeName`) VALUES
(1, 'Đại học - Chính quy'),
(2, 'Chất lượng cao'),
(3, 'Hệ vừa học vừa làm');

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`AttendanceID`),
  ADD KEY `StudyID` (`StudyID`);

--
-- Chỉ mục cho bảng `class`
--
ALTER TABLE `class`
  ADD PRIMARY KEY (`ClassID`),
  ADD KEY `TypeID` (`TypeID`),
  ADD KEY `MajorID` (`MajorID`),
  ADD KEY `ShiftID` (`ShiftID`);

--
-- Chỉ mục cho bảng `login`
--
ALTER TABLE `login`
  ADD PRIMARY KEY (`id_login`);

--
-- Chỉ mục cho bảng `major`
--
ALTER TABLE `major`
  ADD PRIMARY KEY (`MajorID`);

--
-- Chỉ mục cho bảng `shift`
--
ALTER TABLE `shift`
  ADD PRIMARY KEY (`ShiftID`);

--
-- Chỉ mục cho bảng `student`
--
ALTER TABLE `student`
  ADD PRIMARY KEY (`StudentID`),
  ADD KEY `MajorID` (`MajorID`),
  ADD KEY `TypeID` (`TypeID`);

--
-- Chỉ mục cho bảng `student_embeddings`
--
ALTER TABLE `student_embeddings`
  ADD PRIMARY KEY (`EmbeddingID`),
  ADD KEY `idx_student_embeddings_student` (`StudentID`);

--
-- Chỉ mục cho bảng `study`
--
ALTER TABLE `study`
  ADD PRIMARY KEY (`StudyID`),
  ADD KEY `StudentID` (`StudentID`),
  ADD KEY `ClassID` (`ClassID`);

--
-- Chỉ mục cho bảng `teach`
--
ALTER TABLE `teach`
  ADD PRIMARY KEY (`id_teach`),
  ADD KEY `login` (`id_login`),
  ADD KEY `class_teach` (`ClassID`);

--
-- Chỉ mục cho bảng `type`
--
ALTER TABLE `type`
  ADD PRIMARY KEY (`TypeID`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `attendance`
--
ALTER TABLE `attendance`
  MODIFY `AttendanceID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `class`
--
ALTER TABLE `class`
  MODIFY `ClassID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `login`
--
ALTER TABLE `login`
  MODIFY `id_login` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `major`
--
ALTER TABLE `major`
  MODIFY `MajorID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT cho bảng `shift`
--
ALTER TABLE `shift`
  MODIFY `ShiftID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `student`
--
ALTER TABLE `student`
  MODIFY `StudentID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `student_embeddings`
--
ALTER TABLE `student_embeddings`
  MODIFY `EmbeddingID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `study`
--
ALTER TABLE `study`
  MODIFY `StudyID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `teach`
--
ALTER TABLE `teach`
  MODIFY `id_teach` int(50) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `type`
--
ALTER TABLE `type`
  MODIFY `TypeID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `attendance`
--
ALTER TABLE `attendance`
  ADD CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`StudyID`) REFERENCES `study` (`StudyID`);

--
-- Các ràng buộc cho bảng `class`
--
ALTER TABLE `class`
  ADD CONSTRAINT `class_ibfk_1` FOREIGN KEY (`TypeID`) REFERENCES `type` (`TypeID`),
  ADD CONSTRAINT `class_ibfk_2` FOREIGN KEY (`MajorID`) REFERENCES `major` (`MajorID`),
  ADD CONSTRAINT `class_ibfk_3` FOREIGN KEY (`ShiftID`) REFERENCES `shift` (`ShiftID`);

--
-- Các ràng buộc cho bảng `student`
--
ALTER TABLE `student`
  ADD CONSTRAINT `student_ibfk_1` FOREIGN KEY (`MajorID`) REFERENCES `major` (`MajorID`),
  ADD CONSTRAINT `student_ibfk_2` FOREIGN KEY (`TypeID`) REFERENCES `type` (`TypeID`);

--
-- Các ràng buộc cho bảng `student_embeddings`
--
ALTER TABLE `student_embeddings`
  ADD CONSTRAINT `fk_student_embeddings_student` FOREIGN KEY (`StudentID`) REFERENCES `student` (`StudentID`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `study`
--
ALTER TABLE `study`
  ADD CONSTRAINT `study_ibfk_1` FOREIGN KEY (`StudentID`) REFERENCES `student` (`StudentID`),
  ADD CONSTRAINT `study_ibfk_2` FOREIGN KEY (`ClassID`) REFERENCES `class` (`ClassID`);

--
-- Các ràng buộc cho bảng `teach`
--
ALTER TABLE `teach`
  ADD CONSTRAINT `class_teach` FOREIGN KEY (`ClassID`) REFERENCES `class` (`ClassID`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `login` FOREIGN KEY (`id_login`) REFERENCES `login` (`id_login`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
