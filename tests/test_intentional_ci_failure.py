"""#207 negative rehearsal only. Never merge this branch into main."""


def test_intentional_failure_blocks_release():
    assert False, "Intentional #207 rehearsal: a failing full suite must block CI gate and deployment."
