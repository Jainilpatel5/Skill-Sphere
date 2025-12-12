-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS skill_sphere_db;
USE skill_sphere_db;

-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS Reviews, Payments, Sessions, TutorSkills, Skills, TutorProfile, Users;

-- Users Table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'tutor', 'admin') NOT NULL,
    bio TEXT,
    profile_image_url VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TutorProfile Table (extends Users)
CREATE TABLE TutorProfile (
    tutor_id INT PRIMARY KEY,
    hourly_rate DECIMAL(10, 2),
    availability_schedule TEXT,
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    rating_avg FLOAT DEFAULT 0,
    FOREIGN KEY (tutor_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Skills Table
CREATE TABLE Skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100),
    description TEXT
);

-- TutorSkills Linking Table (Many-to-Many)
CREATE TABLE TutorSkills (
    tutor_id INT,
    skill_id INT,
    PRIMARY KEY (tutor_id, skill_id),
    FOREIGN KEY (tutor_id) REFERENCES TutorProfile(tutor_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE
);

-- Sessions Table
CREATE TABLE Sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    tutor_id INT NOT NULL,
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('booked', 'completed', 'cancelled') DEFAULT 'booked',
    session_link VARCHAR(255),
    FOREIGN KEY (tutor_id) REFERENCES Users(user_id),
    FOREIGN KEY (student_id) REFERENCES Users(user_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
);

-- Payments Table
CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id)
);

-- Reviews Table
CREATE TABLE Reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    student_id INT NOT NULL,
    tutor_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id),
    FOREIGN KEY (student_id) REFERENCES Users(user_id),
    FOREIGN KEY (tutor_id) REFERENCES Users(user_id)
);

-- --- SAMPLE DATA ---

-- Users (Password for all is 'password123')
-- Hashed passwords generated using bcrypt.hashpw(b'password123', bcrypt.gensalt())
INSERT INTO Users (name, email, password_hash, role, bio) VALUES
('Admin User', 'admin@skillsphere.com', '$2b$12$Ea.mB.xT1eQ.K/4f6tL7gu/jYwL/G.vl.iJvbvW8VbuT3m1vjG/aC', 'admin', 'I manage the Skill Sphere platform.'),
('Alice Johnson (Tutor)', 'alice@example.com', '$2b$12$Ea.mB.xT1eQ.K/4f6tL7gu/jYwL/G.vl.iJvbvW8VbuT3m1vjG/aC', 'tutor', 'Expert Python and Data Science instructor with 5 years of experience.'),
('Bob Smith (Tutor)', 'bob@example.com', '$2b$12$Ea.mB.xT1eQ.K/4f6tL7gu/jYwL/G.vl.iJvbvW8VbuT3m1vjG/aC', 'tutor', 'Professional artist specializing in digital painting and illustration.'),
('Charlie Brown (Student)', 'charlie@example.com', '$2b$12$Ea.mB.xT1eQ.K/4f6tL7gu/jYwL/G.vl.iJvbvW8VbuT3m1vjG/aC', 'student', 'Eager to learn Python for my upcoming projects.'),
('Diana Prince (Student)', 'diana@example.com', '$2b$12$Ea.mB.xT1eQ.K/4f6tL7gu/jYwL/G.vl.iJvbvW8VbuT3m1vjG/aC', 'student', 'Looking to improve my digital art skills.');

-- TutorProfiles
INSERT INTO TutorProfile (tutor_id, hourly_rate, verification_status, rating_avg) VALUES
(2, 50.00, 'verified', 4.8),
(3, 40.00, 'pending', 4.5);

-- Skills
INSERT INTO Skills (skill_name, category, description) VALUES
('Python Programming', 'Technology', 'Learn the fundamentals of Python from scratch.'),
('Data Science with Pandas', 'Technology', 'Analyze data effectively using the Pandas library.'),
('Digital Painting', 'Art', 'Create stunning digital artwork with professional techniques.'),
('Yoga Basics', 'Fitness', 'Master foundational yoga poses for health and wellness.');

-- TutorSkills
INSERT INTO TutorSkills (tutor_id, skill_id) VALUES
(2, 1), (2, 2), (3, 3);

-- Sessions
INSERT INTO Sessions (tutor_id, student_id, skill_id, start_time, end_time, status, session_link) VALUES
(2, 4, 1, '2025-11-10 14:00:00', '2025-11-10 15:00:00', 'completed', 'https://meet.example.com/xyz-123'),
(3, 5, 3, '2025-11-12 18:00:00', '2025-11-12 19:00:00', 'booked', 'https://meet.example.com/abc-456');

-- Payments
INSERT INTO Payments (session_id, amount, payment_status) VALUES
(1, 50.00, 'completed'),
(2, 40.00, 'completed');

-- Reviews
INSERT INTO Reviews (session_id, student_id, tutor_id, rating, comment) VALUES
(1, 4, 2, 5, 'Alice was an amazing teacher! Very clear and patient.');