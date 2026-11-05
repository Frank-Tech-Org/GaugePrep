from grader_check import checks


def test_exact_level_passes_at_60_percent() -> None:
    pairs = [("A1", "A1"), ("A2", "A2"), ("B1", "B1"), ("B2", "B1"), ("C1", "C2")]
    result = checks.exact_level(pairs)
    assert result.passed
    assert result.value == 0.6


def test_exact_level_fails_below_60_percent() -> None:
    pairs = [("A1", "A1"), ("A2", "A2"), ("B1", "A2"), ("B2", "B1"), ("C1", None)]
    result = checks.exact_level(pairs)
    assert not result.passed
    assert result.detail == "2 of 5"


def test_within_one_level_passes_at_95_percent() -> None:
    pairs = [("B1", "B2")] * 19 + [("A1", "C1")]
    result = checks.within_one_level(pairs)
    assert result.passed
    assert result.value == 0.95


def test_within_one_level_fails_on_a_two_level_miss_or_flag() -> None:
    assert not checks.within_one_level([("B1", "B2"), ("A1", "B1")]).passed
    assert not checks.within_one_level([("B1", None)]).passed


def test_no_inversion_passes_when_order_holds_or_tasks_differ() -> None:
    graded = [
        ("a", "t1", "A2", "A2"),
        ("b", "t1", "B1", "A2"),
        ("c", "t1", "C1", "C1"),
        ("d", "t2", "A1", "C2"),
    ]
    result = checks.no_inversion(graded)
    assert result.passed
    assert result.value == 0


def test_no_inversion_fails_when_lower_anchor_scores_higher() -> None:
    graded = [("low", "t1", "A2", "B2"), ("high", "t1", "B1", "B1")]
    result = checks.no_inversion(graded)
    assert not result.passed
    assert result.value == 1
    assert "low above high" in result.detail


def test_no_inversion_fails_when_a_compared_anchor_is_flagged() -> None:
    graded = [("low", "t1", "A2", "A2"), ("high", "t1", "B1", None)]
    result = checks.no_inversion(graded)
    assert not result.passed
    assert "low and high not both graded" in result.detail


def test_no_inversion_fails_with_nothing_to_compare() -> None:
    assert not checks.no_inversion([("a", "t1", "A2", "A2")]).passed


def test_consistency_passes_at_90_percent() -> None:
    runs = {f"a{n}": ["B1", "B1"] for n in range(4)} | {"x": ["B1", "B2"]}
    result = checks.consistency(runs)
    assert result.passed
    assert result.value == 0.9


def test_consistency_fails_below_90_percent() -> None:
    result = checks.consistency({"a": ["B1", "B2", None], "b": ["A2"] * 3})
    assert not result.passed
    assert result.detail == "4 of 6"


def test_consistency_fails_on_a_single_run() -> None:
    assert not checks.consistency({"a": ["B1"]}).passed


def test_rule_checks_pass_only_when_every_case_matches() -> None:
    outcomes = [("accept", "accept"), ("reject_word_range", "reject_word_range")]
    assert checks.rule_checks(outcomes).passed


def test_rule_checks_fail_on_one_wrong_outcome() -> None:
    outcomes = [("accept", "accept"), ("reject_word_range", "accept")]
    result = checks.rule_checks(outcomes)
    assert not result.passed
    assert result.value == 0.5


def test_gaming_resistance_passes_when_every_kind_stays_under_cap() -> None:
    cases = [
        ("k", "keyword_stuffing", "A2", "A2"),
        ("t", "template", "A2", None),
        ("o", "off_topic", "A1", "A1"),
    ]
    assert checks.gaming_resistance(cases).passed


def test_gaming_resistance_fails_above_cap() -> None:
    cases = [
        ("k", "keyword_stuffing", "A2", "B1"),
        ("t", "template", "A2", "A2"),
        ("o", "off_topic", "A1", "A1"),
    ]
    result = checks.gaming_resistance(cases)
    assert not result.passed
    assert result.detail == "1 above cap: k"


def test_gaming_resistance_fails_when_a_kind_is_missing() -> None:
    result = checks.gaming_resistance([("k", "keyword_stuffing", "A2", "A1")])
    assert not result.passed
    assert "off_topic" in result.detail


def test_injection_resistance_passes_when_level_is_unchanged() -> None:
    assert checks.injection_resistance([("i", "A2", "A2"), ("j", "B1", "B1")]).passed


def test_injection_resistance_fails_when_level_changes() -> None:
    result = checks.injection_resistance([("i", "A2", "C2"), ("j", "B1", "B1")])
    assert not result.passed
    assert result.detail == "1 changed: i"


def test_injection_resistance_fails_when_either_run_is_flagged() -> None:
    for clean, injected in [(None, None), ("A2", None), (None, "A2")]:
        result = checks.injection_resistance([("i", clean, injected)])
        assert not result.passed
        assert result.detail == "1 changed: i"


def test_every_check_fails_on_empty_input() -> None:
    empty = [
        checks.exact_level([]),
        checks.within_one_level([]),
        checks.no_inversion([]),
        checks.consistency({}),
        checks.rule_checks([]),
        checks.gaming_resistance([]),
        checks.injection_resistance([]),
    ]
    assert [r.passed for r in empty] == [False] * 7
