
from src.feedback_classifier import (
    TOPICS,
    classify_feedback,
    count_topics,
    group_feedback,
)


def test_all_five_topics():
    comments = [
        "The course content is difficult to understand",
        "The lecturer's teaching explanation is unclear",
        "The workload is too much",
        "The exam grading is unfair",
        "The classroom is painted blue",
    ]

    groups = group_feedback(comments)

    assert set(groups.keys()) == set(TOPICS)
    assert all(len(groups[topic]) == 1 for topic in TOPICS)


def test_uncertain_feedback_is_other():
    assert classify_feedback(
        "The classroom is painted blue"
    ) == "Other"


def test_topic_frequency():
    comments = [
        "The course content is useful",
        "The course content needs improvement",
        "The exam grading is unfair",
    ]

    counts = count_topics(group_feedback(comments))

    assert counts["Course content"] == 2
    assert counts["Assessment"] == 1
    assert counts["Other"] == 0


def test_keyword_fragments_do_not_create_assessment_topics():
    """M5-A05: 'exam'/'test' substrings are not assessment feedback."""
    from src.app import classify_feedback as classify_api_feedback

    for classify in (classify_feedback, classify_api_feedback):
        for comment in ("Helpful examples.", "The latest update was useful.", "A contest outside class."):
            assert classify(comment) == "Other"
        assert classify("The exams were fair.") == "Assessment"
