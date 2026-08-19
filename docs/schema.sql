-- Secure Vision Attendance database schema
-- MySQL 8.x
CREATE TABLE IF NOT EXISTS persons (
    person_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (person_id),
    UNIQUE KEY uq_person_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    person_id BIGINT UNSIGNED NOT NULL,
    attendance_date DATE NOT NULL,
    attendance_time TIME NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'Present',
    method VARCHAR(128) NOT NULL DEFAULT 'Face Recognition',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (attendance_id),
    UNIQUE KEY uq_person_attendance_date (person_id, attendance_date),
    KEY idx_attendance_date (attendance_date),
    CONSTRAINT fk_attendance_person
        FOREIGN KEY (person_id) REFERENCES persons(person_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recognition_events (
    event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    person_id BIGINT UNSIGNED NULL,
    result VARCHAR(32) NOT NULL,
    match_score DECIMAL(8,4) NULL,
    distance DECIMAL(12,8) NULL,
    threshold DECIMAL(12,8) NULL,
    source VARCHAR(128) NOT NULL DEFAULT 'Image Recognition',
    video_filename VARCHAR(512) NULL,
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id),
    KEY idx_recognition_event_time (event_time),
    KEY idx_recognition_person (person_id),
    CONSTRAINT fk_recognition_person
        FOREIGN KEY (person_id) REFERENCES persons(person_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS video_sessions (
    video_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    filename VARCHAR(512) NOT NULL,
    duration_seconds DECIMAL(12,3) NULL,
    frames_sampled INT UNSIGNED NULL,
    faces_detected INT UNSIGNED NULL,
    recognized_faces INT UNSIGNED NULL,
    unknown_faces INT UNSIGNED NULL,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'Completed',
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id),
    KEY idx_video_processed_at (processed_at)
) ENGINE=InnoDB;
