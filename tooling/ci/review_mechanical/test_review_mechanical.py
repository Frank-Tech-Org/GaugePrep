import review_mechanical as rm


def diff(path: str, *lines: str) -> str:
    body = "".join(f"+{line}\n" for line in lines)
    head = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
    return head + f"@@ -0,0 +1,{len(lines)} @@\n{body}"


def findings(path: str, *lines: str) -> list[str]:
    out: list[str] = []
    for p, n, t in rm.added_lines(diff(path, *lines)):
        out += (
            rm.check_code(p, n, t)
            + rm.check_suppression(p, n, t)
            + rm.check_prose(p, n, t, set())
        )
    return out


def test_added_lines_tracks_numbers() -> None:
    assert rm.added_lines(diff("a.py", "x", "y")) == [
        ("a.py", 1, "x"),
        ("a.py", 2, "y"),
    ]


def test_long_comment() -> None:
    assert any("over 100" in f for f in findings("a.py", "# " + "x" * 100))


def test_short_tagged_comment_is_clean() -> None:
    assert findings("a.py", "# WHY: the base is trusted.") == []


def test_banner_and_todo() -> None:
    assert any("banner" in f for f in findings("a.py", "# ----- Setup -----"))
    assert any("TODO" in f for f in findings("a.py", "# TODO: later"))
    assert findings("a.py", "# TODO(#12): later") == []


def test_suppression_needs_a_reason() -> None:
    assert any("suppression" in f for f in findings("a.py", "x = 1  # noqa: E501"))
    assert findings("a.py", "x = 1  # noqa: E501 - generated URL") == []


def test_prose_checks() -> None:
    assert any("em dash" in f for f in findings("a.md", "one — two"))
    assert any("signature" in f for f in findings("a.md", "Co-Authored-By: x"))


def test_markdown_comments_are_not_code() -> None:
    assert findings("a.md", "# " + "x" * 120) == []


def test_pr_text_names() -> None:
    names = {"cto"}
    assert rm.check_pr_text("I moved the check.", names) == []
    assert rm.check_pr_text("Run /lm-next after.", names)
    assert rm.check_pr_text("the cto agent said so", names)
