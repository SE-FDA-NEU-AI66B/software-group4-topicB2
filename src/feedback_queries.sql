
-- Task #53: Lecturer course ownership and feedback access queries.
-- Named parameters are supplied by the backend API.

-- 1. Check whether the lecturer is assigned to the selected course.
-- The API must deny access if this query returns no rows.
SELECT 1 AS has_access
FROM course_lecturers
WHERE lecturer_id = :lecturer_id
  AND course_id = :course_id
LIMIT 1;


-- 2. Retrieve submitted feedback for a course.
-- Only responses with status = 'submitted' are included.
-- The API must verify lecturer ownership before returning these results.
SELECT
    e.id AS evaluation_id,
    e.title AS evaluation_title,
    c.id AS course_id,
    c.course_code,
    c.course_name,
    r.id AS response_id,
    r.student_id,
    r.submitted_at,
    q.id AS question_id,
    q.question_text,
    q.question_type,
    a.rating_value,
    a.text_value
FROM evaluations AS e
JOIN courses AS c
    ON c.id = e.course_id
JOIN responses AS r
    ON r.evaluation_id = e.id
JOIN response_answers AS a
    ON a.response_id = r.id
JOIN questions AS q
    ON q.id = a.question_id
   AND q.evaluation_id = e.id
WHERE e.course_id = :course_id
  AND r.status = 'submitted'
ORDER BY
    e.id,
    r.submitted_at,
    q.question_order;


-- 3. Count completed evaluations for a course.
-- Count submitted responses, not individual answers or questions.
SELECT COUNT(*) AS completed_evaluation_count
FROM evaluations AS e
JOIN responses AS r
    ON r.evaluation_id = e.id
WHERE e.course_id = :course_id
  AND r.status = 'submitted';


-- 4. Retrieve course feedback summary.
-- The API must verify lecturer ownership before returning this result.
SELECT
    c.id AS course_id,
    c.course_code,
    c.course_name,
    COUNT(DISTINCT r.id) AS completed_evaluation_count
FROM courses AS c
LEFT JOIN evaluations AS e
    ON e.course_id = c.id
LEFT JOIN responses AS r
    ON r.evaluation_id = e.id
   AND r.status = 'submitted'
WHERE c.id = :course_id
GROUP BY
    c.id,
    c.course_code,
    c.course_name;
