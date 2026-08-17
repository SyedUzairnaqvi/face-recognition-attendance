-- ============================================================
-- SECURE VISION ATTENDANCE
-- ANALYTICS QUERIES
-- ============================================================
--
-- Purpose:
-- Read-only SQL queries for attendance, recognition,
-- and video analytics.
--
-- These queries are designed for:
-- - Power BI
-- - Reporting
-- - Dashboard development
-- - Manual database analysis
--
-- IMPORTANT:
-- These queries do NOT modify application data.
-- ============================================================


-- ============================================================
-- 1. DAILY ATTENDANCE
-- ============================================================
-- Shows how many attendance records and unique people
-- were recorded on each calendar date.

SELECT
    attendance_date,                              -- Attendance date
    COUNT(*) AS total_attendance,                 -- Total attendance records
    COUNT(DISTINCT person_id) AS unique_people    -- Distinct people present
FROM attendance
GROUP BY attendance_date
ORDER BY attendance_date DESC;


-- ============================================================
-- 2. ATTENDANCE BY PERSON
-- ============================================================
-- Shows the number of days each person has attended.

SELECT
    p.person_id,                                  -- Person identifier
    p.name,                                       -- Person name
    COUNT(a.attendance_id) AS attendance_days    -- Number of attendance days
FROM persons p
LEFT JOIN attendance a
    ON p.person_id = a.person_id                  -- Link attendance to person
GROUP BY
    p.person_id,
    p.name
ORDER BY
    attendance_days DESC,
    p.name;


-- ============================================================
-- 3. TODAY'S ATTENDANCE
-- ============================================================
-- Returns attendance for the current database date.
--
-- Application endpoints already calculate today's date
-- using IST. This query is mainly for reporting.

SELECT
    a.attendance_id,                              -- Attendance record
    p.name,                                       -- Person name
    a.attendance_date,                            -- Attendance date
    a.attendance_time,                            -- Attendance time
    a.status,                                     -- Attendance status
    a.method                                      -- Recognition method
FROM attendance a
JOIN persons p
    ON p.person_id = a.person_id                  -- Link person
WHERE a.attendance_date = CURRENT_DATE()
ORDER BY a.attendance_time;


-- ============================================================
-- 4. ATTENDANCE BY METHOD
-- ============================================================
-- Shows how attendance was recorded.

SELECT
    method,                                       -- Face Recognition / Video Recognition
    COUNT(*) AS total_attendance                  -- Number of attendance records
FROM attendance
GROUP BY method
ORDER BY total_attendance DESC;


-- ============================================================
-- 5. RECOGNITION RESULT SUMMARY
-- ============================================================
-- Shows matched versus unknown recognition events.

SELECT
    result,                                       -- matched / unknown
    COUNT(*) AS total_events                      -- Number of events
FROM recognition_events
GROUP BY result
ORDER BY total_events DESC;


-- ============================================================
-- 6. RECOGNITION SUMMARY BY SOURCE
-- ============================================================
-- Separates image recognition from video recognition.

SELECT
    source,                                       -- Recognition source
    result,                                       -- matched / unknown
    COUNT(*) AS total_events                      -- Number of events
FROM recognition_events
GROUP BY
    source,
    result
ORDER BY
    source,
    result;


-- ============================================================
-- 7. RECOGNITION QUALITY
-- ============================================================
-- Shows average recognition distance and match score.
--
-- Unknown faces have a match_score of 0 in the current
-- implementation, so matched results are more useful
-- for score analysis.

SELECT
    source,                                       -- Image / Video
    result,                                       -- matched / unknown
    COUNT(*) AS total_events,                     -- Number of events
    ROUND(AVG(distance), 6) AS average_distance,  -- Average embedding distance
    ROUND(AVG(match_score), 4) AS average_score   -- Average match score
FROM recognition_events
GROUP BY
    source,
    result
ORDER BY
    source,
    result;


-- ============================================================
-- 8. RECOGNITION EVENTS BY PERSON
-- ============================================================
-- Shows how many times each known person was recognized.

SELECT
    p.person_id,                                  -- Person identifier
    p.name,                                       -- Person name
    COUNT(re.event_id) AS recognition_events      -- Recognition occurrences
FROM persons p
LEFT JOIN recognition_events re
    ON p.person_id = re.person_id                 -- Link events to person
GROUP BY
    p.person_id,
    p.name
ORDER BY
    recognition_events DESC,
    p.name;


-- ============================================================
-- 9. VIDEO SESSION SUMMARY
-- ============================================================
-- Shows statistics for every processed video.

SELECT
    video_id,                                     -- Video session identifier
    filename,                                     -- Uploaded filename
    duration_seconds,                             -- Video duration
    frames_sampled,                               -- Frames processed
    faces_detected,                               -- Faces detected
    recognized_faces,                             -- Recognized faces
    unknown_faces,                                -- Unknown faces
    processing_status,                            -- Processing result
    processed_at                                  -- Processing timestamp
FROM video_sessions
ORDER BY processed_at DESC;


-- ============================================================
-- 10. OVERALL VIDEO ANALYTICS
-- ============================================================
-- Provides high-level video processing statistics.

SELECT
    COUNT(*) AS total_videos,                     -- Number of videos
    ROUND(AVG(duration_seconds), 2)
        AS average_duration_seconds,              -- Average duration
    SUM(frames_sampled)
        AS total_frames_sampled,                  -- Total sampled frames
    SUM(faces_detected)
        AS total_faces_detected,                  -- Total faces
    SUM(recognized_faces)
        AS total_recognized_faces,                -- Total recognized
    SUM(unknown_faces)
        AS total_unknown_faces                    -- Total unknown
FROM video_sessions
WHERE processing_status = 'Completed';


-- ============================================================
-- 11. VIDEO RECOGNITION PERFORMANCE
-- ============================================================
-- Calculates the percentage of detected faces that were
-- recognized in completed video sessions.

SELECT
    ROUND(
        100.0 * SUM(recognized_faces)
        / NULLIF(SUM(faces_detected), 0),
        2
    ) AS recognition_rate_percent                -- Recognition percentage
FROM video_sessions
WHERE processing_status = 'Completed';


-- ============================================================
-- 12. DAILY RECOGNITION ACTIVITY
-- ============================================================
-- Useful for time-series charts in Power BI.

SELECT
    DATE(event_time) AS event_date,               -- Recognition calendar date
    COUNT(*) AS total_events,                     -- Total recognition events
    SUM(result = 'matched')
        AS matched_events,                        -- Matched events
    SUM(result = 'unknown')
        AS unknown_events                         -- Unknown events
FROM recognition_events
GROUP BY DATE(event_time)
ORDER BY event_date DESC;


-- ============================================================
-- 13. DAILY RECOGNITION RATE
-- ============================================================
-- Calculates the percentage of recognition events that
-- resulted in a match.

SELECT
    DATE(event_time) AS event_date,               -- Recognition date
    COUNT(*) AS total_events,                     -- Total events
    SUM(result = 'matched')
        AS matched_events,                        -- Matched events
    SUM(result = 'unknown')
        AS unknown_events,                        -- Unknown events
    ROUND(
        100.0 * SUM(result = 'matched')
        / NULLIF(COUNT(*), 0),
        2
    ) AS recognition_rate_percent                -- Match percentage
FROM recognition_events
GROUP BY DATE(event_time)
ORDER BY event_date DESC;


-- ============================================================
-- 14. PERSON ATTENDANCE + RECOGNITION ACTIVITY
-- ============================================================
-- Combines attendance history with recognition-event counts.
--
-- Useful for a Power BI person-level dashboard.

SELECT
    p.person_id,                                  -- Person identifier
    p.name,                                       -- Person name
    COUNT(DISTINCT a.attendance_date)
        AS attendance_days,                       -- Days attended
    COUNT(DISTINCT re.event_id)
        AS recognition_events                     -- Recognition occurrences
FROM persons p
LEFT JOIN attendance a
    ON p.person_id = a.person_id
LEFT JOIN recognition_events re
    ON p.person_id = re.person_id
GROUP BY
    p.person_id,
    p.name
ORDER BY
    attendance_days DESC,
    recognition_events DESC;


-- ============================================================
-- END OF ANALYTICS QUERIES
-- ============================================================