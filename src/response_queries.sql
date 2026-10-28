
-- Task #25: Database queries for course evaluation responses.
-- These queries use named parameters supplied by the API.

-- 1. Create a draft response if one does not exist.
-- The UNIQUE(evaluation_id, student_id) constraint prevents duplicates.
INSERT INTO responses (evaluation_id, student_id, status)
VALUES (:evaluation_id, :student_id, 'draft')
ON CONFLICT (evaluation_id, student_id) DO NOTHING;

-- 2. Retrieve the response belonging to the student and evaluation.
SELECT id, evaluation_id, student_id, status, submitted_at
FROM responses
WHERE evaluation_id = :evaluation_id
  AND student_id = :student_id;

-- 3. Retrieve questions and the student's saved answers.
SELECT
    q.id AS question_id,
    q.question_text,
    q.question_type,
    q.is_required,
    a.rating_value,
    a.text_value
FROM questions AS q
LEFT JOIN responses AS r
    ON r.evaluation_id = q.evaluation_id
   AND r.student_id = :student_id
LEFT JOIN response_answers AS a
    ON a.response_id = r.id
   AND a.question_id = q.id
WHERE q.evaluation_id = :evaluation_id
ORDER BY q.question_order;

-- 4. Count required questions that have not been answered.
-- Rating questions need a rating; text questions need non-blank text.
SELECT COUNT(*) AS missing_required_count
FROM questions AS q
LEFT JOIN response_answers AS a
    ON a.response_id = :response_id
   AND a.question_id = q.id
WHERE q.evaluation_id = :evaluation_id
  AND q.is_required = 1
  AND (
      (q.question_type = 'rating' AND a.rating_value IS NULL)
      OR
      (
          q.question_type = 'text'
          AND (a.text_value IS NULL OR TRIM(a.text_value) = '')
      )
  );

-- 5. Save or update an answer for an existing draft response.
-- The API must first verify student ownership and question type.
INSERT INTO response_answers (
    response_id, question_id, rating_value, text_value
)
VALUES (
    :response_id, :question_id, :rating_value, :text_value
)
ON CONFLICT (response_id, question_id)
DO UPDATE SET
    rating_value = excluded.rating_value,
    text_value = excluded.text_value
WHERE EXISTS (
    SELECT 1
    FROM responses
    WHERE id = :response_id
      AND status = 'draft'
);

-- 6. Submit only if the response is still a draft and all required
-- questions have valid answers. The API must check that one row changed.
UPDATE responses
SET status = 'submitted',
    submitted_at = CURRENT_TIMESTAMP
WHERE id = :response_id
  AND student_id = :student_id
  AND status = 'draft'
  AND NOT EXISTS (
      SELECT 1
      FROM questions AS q
      LEFT JOIN response_answers AS a
          ON a.response_id = responses.id
         AND a.question_id = q.id
      WHERE q.evaluation_id = responses.evaluation_id
        AND q.is_required = 1
        AND (
            (q.question_type = 'rating' AND a.rating_value IS NULL)
            OR
            (
                q.question_type = 'text'
                AND (a.text_value IS NULL OR TRIM(a.text_value) = '')
            )
        )
  );
