"""Tests for the Microservices Architecture Trainer."""
import os
import tempfile

import pytest

os.environ["DB_PATH"] = ""  # set before import; overridden per test

from main import LESSONS, LESSON_MAP, app


@pytest.fixture()
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    app.config["TESTING"] = True
    os.environ["DB_PATH"] = db_path
    # Patch DB_PATH at module level
    import main
    main.DB_PATH = db_path
    with app.test_client() as c:
        yield c


# --- Lesson data integrity ---


def test_lesson_count():
    assert len(LESSONS) == 10


def test_lesson_ids_unique():
    ids = [l["id"] for l in LESSONS]
    assert len(ids) == len(set(ids))


def test_lesson_orders_sequential():
    orders = sorted(l["order"] for l in LESSONS)
    assert orders == list(range(1, 11))


def test_each_lesson_has_required_fields():
    for lesson in LESSONS:
        assert "id" in lesson
        assert "title" in lesson
        assert "content" in lesson
        assert "diagram" in lesson
        assert "quiz" in lesson
        assert len(lesson["quiz"]) == 3, f"{lesson['id']} should have 3 quiz questions"


def test_quiz_answers_valid():
    for lesson in LESSONS:
        for i, q in enumerate(lesson["quiz"]):
            assert "question" in q
            assert "options" in q
            assert "answer" in q
            assert 0 <= q["answer"] < len(q["options"]), (
                f"{lesson['id']} q{i}: answer index {q['answer']} out of range"
            )


def test_lesson_map_matches():
    for lesson in LESSONS:
        assert lesson["id"] in LESSON_MAP
        assert LESSON_MAP[lesson["id"]] is lesson


# --- Index page ---


def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Microservices Architecture Trainer" in resp.data


def test_index_lists_all_lessons(client):
    resp = client.get("/")
    for lesson in LESSONS:
        assert lesson["title"].encode() in resp.data


def test_index_shows_progress_bar(client):
    resp = client.get("/")
    assert b"progress-bar" in resp.data


def test_index_sets_session_cookie(client):
    resp = client.get("/")
    assert any("session_id=" in h for h in resp.headers.getlist("Set-Cookie"))


# --- Lesson pages ---


def test_lesson_page_returns_200(client):
    resp = client.get("/lesson/what-are-microservices")
    assert resp.status_code == 200
    assert b"What Are Microservices?" in resp.data


def test_lesson_page_has_diagram(client):
    resp = client.get("/lesson/what-are-microservices")
    assert b'class="diagram"' in resp.data


def test_lesson_page_has_quiz_form(client):
    resp = client.get("/lesson/what-are-microservices")
    assert b"Submit Quiz" in resp.data


def test_invalid_lesson_redirects(client):
    resp = client.get("/lesson/nonexistent")
    assert resp.status_code == 302


def test_all_lessons_accessible(client):
    for lesson in LESSONS:
        resp = client.get(f"/lesson/{lesson['id']}")
        assert resp.status_code == 200, f"Lesson {lesson['id']} not accessible"


# --- Quiz submission ---


def test_quiz_submit_perfect_score(client):
    lesson = LESSONS[0]
    data = {f"q{i}": str(q["answer"]) for i, q in enumerate(lesson["quiz"])}
    resp = client.post(f"/quiz/{lesson['id']}", data=data)
    assert resp.status_code == 200
    assert b"3 / 3" in resp.data


def test_quiz_submit_zero_score(client):
    lesson = LESSONS[0]
    # Submit wrong answers
    data = {}
    for i, q in enumerate(lesson["quiz"]):
        wrong = (q["answer"] + 1) % len(q["options"])
        data[f"q{i}"] = str(wrong)
    resp = client.post(f"/quiz/{lesson['id']}", data=data)
    assert resp.status_code == 200
    assert b"0 / 3" in resp.data


def test_quiz_marks_lesson_completed(client):
    lesson = LESSONS[0]
    data = {f"q{i}": str(q["answer"]) for i, q in enumerate(lesson["quiz"])}
    client.post(f"/quiz/{lesson['id']}", data=data)
    resp = client.get("/")
    assert b"Completed" in resp.data


def test_quiz_invalid_lesson_redirects(client):
    resp = client.post("/quiz/nonexistent", data={"q0": "0"})
    assert resp.status_code == 302


def test_quiz_keeps_best_score(client):
    lesson = LESSONS[0]
    # First: perfect score
    data = {f"q{i}": str(q["answer"]) for i, q in enumerate(lesson["quiz"])}
    client.post(f"/quiz/{lesson['id']}", data=data)
    # Second: zero score
    data2 = {}
    for i, q in enumerate(lesson["quiz"]):
        wrong = (q["answer"] + 1) % len(q["options"])
        data2[f"q{i}"] = str(wrong)
    client.post(f"/quiz/{lesson['id']}", data=data2)
    # Progress should still show best score
    resp = client.get("/api/progress")
    progress = resp.get_json()
    assert progress[0]["quiz_score"] == 3


# --- Certificate ---


def test_certificate_requires_all_lessons(client):
    resp = client.get("/certificate")
    assert resp.status_code == 302  # redirect back to index


def test_certificate_flow(client):
    # Complete all lessons
    for lesson in LESSONS:
        data = {f"q{i}": str(q["answer"]) for i, q in enumerate(lesson["quiz"])}
        client.post(f"/quiz/{lesson['id']}", data=data)
    # Check certificate form accessible
    resp = client.get("/certificate")
    assert resp.status_code == 200
    assert b"Congratulations" in resp.data
    # Submit name
    resp = client.post("/certificate", data={"name": "Test Student"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Test Student" in resp.data
    assert b"Certificate of Completion" in resp.data


# --- Reset ---


def test_reset_clears_progress(client):
    lesson = LESSONS[0]
    data = {f"q{i}": str(q["answer"]) for i, q in enumerate(lesson["quiz"])}
    client.post(f"/quiz/{lesson['id']}", data=data)
    # Verify completed
    resp = client.get("/api/progress")
    assert len(resp.get_json()) == 1
    # Reset
    client.post("/reset")
    resp = client.get("/api/progress")
    assert len(resp.get_json()) == 0


# --- API endpoints ---


def test_api_lessons(client):
    resp = client.get("/api/lessons")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 10
    assert data[0]["id"] == "what-are-microservices"


def test_api_progress_empty(client):
    resp = client.get("/api/progress")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


# --- Navigation ---


def test_lesson_has_nav_links(client):
    # Middle lesson should have both prev and next
    resp = client.get("/lesson/api-gateway")  # lesson 3
    assert b"Previous" in resp.data
    assert b"Next" in resp.data


def test_first_lesson_no_prev(client):
    resp = client.get("/lesson/what-are-microservices")  # lesson 1
    assert b"Previous" not in resp.data
    assert b"Next" in resp.data


def test_last_lesson_no_next(client):
    resp = client.get("/lesson/deployment-strategies")  # lesson 10
    assert b"Previous" in resp.data
    assert b"Next" not in resp.data
