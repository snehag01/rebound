"""Tests for the application answer memory (skills/application-packet/scripts/answers.py)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "application-packet" / "scripts"))

import answers as ans  # noqa: E402


def _empty():
    return {"reusable": {}, "questions": []}


def test_set_reusable():
    d = ans.set_reusable(_empty(), "salary_expectation", "$180k")
    assert d["reusable"]["salary_expectation"] == "$180k"


def test_add_qa_updates_same_question_in_place():
    d = _empty()
    ans.add_qa(d, "Why do you want to work here?", "First answer.")
    ans.add_qa(d, "why do you WANT to work here", "Updated answer.")  # same tokens → update
    assert len(d["questions"]) == 1
    assert d["questions"][0]["a"] == "Updated answer."


def test_suggest_finds_a_similar_prior_question():
    d = _empty()
    ans.add_qa(d, "Why do you want to work at this company?", "Because …")
    s = ans.suggest(d, "Why do you want to join our company?")
    assert s["match"] is not None
    assert s["score"] > 0


def test_suggest_returns_none_for_unrelated_question():
    d = _empty()
    ans.add_qa(d, "What is your expected salary?", "$180k")
    s = ans.suggest(d, "Describe a conflict with a teammate")
    assert s["match"] is None


def test_save_and_load_roundtrip(tmp_path):
    store = str(tmp_path / "answers.json")
    d = ans.set_reusable(_empty(), "notice_period", "2 weeks")
    ans.save(d, store)
    reloaded = ans.load(store)
    assert reloaded["reusable"]["notice_period"] == "2 weeks"
    assert "questions" in reloaded  # load() normalizes the shape


def test_load_missing_store_returns_empty_shape(tmp_path):
    d = ans.load(str(tmp_path / "does_not_exist.json"))
    assert d == {"reusable": {}, "questions": []}
