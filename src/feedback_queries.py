TOPICS = [
    "Course Content",
    "Teaching Delivery",
    "Workload",
    "Assessment",
    "Other",
]


def get_feedback_topic_frequencies(connection, evaluation_id, classify_feedback):
    rows = connection.execute(
        """
        SELECT ra.text_value
        FROM response_answers AS ra
        JOIN responses AS r ON r.id = ra.response_id
        JOIN questions AS q ON q.id = ra.question_id
        WHERE r.evaluation_id = ?
          AND r.status = 'submitted'
          AND q.evaluation_id = r.evaluation_id
          AND q.question_type = 'text'
          AND ra.text_value IS NOT NULL
          AND TRIM(ra.text_value) != ''
        ORDER BY r.id, q.question_order
        """,
        (evaluation_id,),
    ).fetchall()

    frequencies = {topic: 0 for topic in TOPICS}

    for row in rows:
        topic = classify_feedback(row["text_value"].strip())
        frequencies[topic] += 1

    return [
        {"topic": topic, "count": count}
        for topic, count in sorted(
            frequencies.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
