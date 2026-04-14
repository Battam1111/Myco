"""Tests for myco.observe_turn (Wave 57 Wave 2 — Agent reflex arc)."""

from myco.observe_turn import observe_turn


class TestObserveTurnBasics:
    def test_empty_input_returns_empty(self):
        r = observe_turn("")
        assert r["should_eat"] is False
        assert r["suggested_calls"] == []
        assert r["confidence"] == "low"

    def test_trivial_input_returns_empty(self):
        r = observe_turn("hi")
        assert r["suggested_calls"] == []

    def test_turn_length_field(self):
        r = observe_turn("this is a test turn that is long enough")
        assert r["turn_length"] == len("this is a test turn that is long enough")


class TestDecisionEating:
    def test_decision_marker_triggers_eat(self):
        r = observe_turn("I decided we will use Postgres for the project.")
        assert r["should_eat"] is True
        eats = [c for c in r["suggested_calls"] if c["tool"] == "myco_eat"]
        assert len(eats) >= 1
        assert "decision" in eats[0]["args"]["tags"]

    def test_chinese_decision_marker(self):
        r = observe_turn("我决定使用 Postgres 作为主要数据库。")
        assert r["should_eat"] is True

    def test_preference_marker_triggers_eat(self):
        r = observe_turn("From now on, always use utf-8 encoding.")
        assert r["should_eat"] is True


class TestVocabularyEating:
    def test_calling_it_triggers_vocab(self):
        r = observe_turn("We're calling it Myco — short for mycelium.")
        assert r["should_eat"] is True
        vocab = [c for c in r["suggested_calls"]
                 if "vocabulary" in c["args"].get("tags", [])]
        assert len(vocab) >= 1


class TestScentSignals:
    def test_what_is_triggers_scent(self):
        r = observe_turn("What is Retrieval-Augmented-Generation really doing?")
        assert r["should_scent"] is True
        scents = [c for c in r["suggested_calls"] if c["tool"] == "myco_scent"]
        assert len(scents) >= 1

    def test_research_triggers_scent(self):
        r = observe_turn("Please investigate LangGraph and tell me about it.")
        assert r["should_scent"] is True


class TestVerifySignals:
    def test_latest_version_triggers_verify(self):
        r = observe_turn("What is the latest version of torch that supports CUDA 12?")
        assert r["should_verify"] is True
        assert any(c["tool"] == "myco_verify" for c in r["suggested_calls"])

    def test_still_triggers_verify(self):
        r = observe_turn("Is it still true that numpy 2.0 breaks torch?")
        assert r["should_verify"] is True


class TestConfidence:
    def test_no_signals_is_low(self):
        r = observe_turn("okay, makes sense, thanks")
        assert r["confidence"] == "low"

    def test_multiple_signals_is_high(self):
        r = observe_turn(
            "I decided to use RAG — please investigate the latest version of langchain."
        )
        # Should trigger decision + scent + verify
        assert r["confidence"] in {"medium", "high"}
