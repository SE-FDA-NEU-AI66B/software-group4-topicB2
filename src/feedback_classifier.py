
from collections import Counter

TOPICS = [
    "Course content",
    "Teaching delivery",
    "Workload",
    "Assessment",
    "Other",
]

KEYWORDS = {
    "Course content": [
        "course content", "course material", "syllabus",
        "theory", "learning material",
    ],
    "Teaching delivery": [
        "teaching", "lecturer", "explanation",
        "presentation", "teaching method",
    ],
    "Workload": [
        "workload", "too much work", "time-consuming",
        "heavy workload", "too many assignments",
    ],
    "Assessment": [
        "assessment", "exam", "grading", "grade",
        "marking", "quiz", "test",
    ],
}


def classify_feedback(comment):
    if not comment or not comment.strip():
        return "Other"

    text = comment.lower()
    scores = {
        topic: sum(keyword in text for keyword in keywords)
        for topic, keywords in KEYWORDS.items()
    }

    highest = max(scores.values())

    if highest == 0:
        return "Other"

    winners = [
        topic for topic, score in scores.items()
        if score == highest
    ]

    if len(winners) != 1:
        return "Other"

    return winners[0]


def group_feedback(comments):
    groups = {topic: [] for topic in TOPICS}

    for comment in comments:
        groups[classify_feedback(comment)].append(comment)

    return groups


def count_topics(groups):
    return Counter({
        topic: len(groups[topic])
        for topic in TOPICS
    })
