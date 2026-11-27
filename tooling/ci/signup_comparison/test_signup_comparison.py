import signup_comparison as sc


def answer(**changes: object) -> sc.Answer:
    base: dict[str, object] = {
        "status": 201,
        "headers": {"content-type": "application/json", "date": "Mon"},
        "body": {"learner_id": "a" * 36, "email": "x@y.z", "csrf_token": "t" * 64},
        "cookie_names": ("gp_csrf",),
    }
    return sc.Answer(**{**base, **changes})  # type: ignore[arg-type]  # test builder


def test_per_account_values_do_not_count_as_a_difference() -> None:
    other = answer(
        headers={"content-type": "application/json", "date": "Tue"},
        body={"learner_id": "b" * 36, "email": "p@q.r", "csrf_token": "u" * 64},
    )
    assert sc.differences(answer(), other) == []


def test_a_different_status_is_reported() -> None:
    assert sc.differences(answer(), answer(status=409)) != []


def test_a_new_session_cookie_is_reported() -> None:
    other = answer(cookie_names=("gp_csrf", "gp_session"))
    assert sc.differences(answer(), other) != []


def test_a_different_header_is_reported() -> None:
    other = answer(headers={"content-type": "text/html", "date": "Mon"})
    assert sc.differences(answer(), other) != []


def test_a_value_of_another_length_is_reported() -> None:
    other = answer(
        body={"learner_id": "b" * 30, "email": "x@y.z", "csrf_token": "t" * 64}
    )
    assert sc.differences(answer(), other) == ["body.learner_id: length differs"]


def test_a_new_address_has_the_length_and_domain_of_the_verified_one() -> None:
    for verified in ("a@x.io", "seeded.learner@staging.example", "x" * 60 + "@y.z"):
        fresh = sc.address_like(verified)
        assert len(fresh) == len(verified)
        assert fresh.split("@")[1] == verified.split("@")[1]
        assert fresh != verified


def test_answers_for_emails_of_another_length_than_the_old_default_match() -> None:
    known = answer(body={"learner_id": "a" * 36, "email": "seeded@s.example"})
    new = answer(
        body={"learner_id": "b" * 36, "email": sc.address_like("seeded@s.example")}
    )
    assert sc.differences(known, new) == []
