"""Tests for scorecard computation logic.

Covers: _estimate_reading_level, make_scorecard_node.
"""

from __future__ import annotations

from ailine_agents.workflows._plan_nodes import _estimate_reading_level

# ---------------------------------------------------------------------------
# _estimate_reading_level
# ---------------------------------------------------------------------------


class TestEstimateReadingLevel:
    def test_empty_text(self) -> None:
        assert _estimate_reading_level("") == 0.0

    def test_whitespace_only(self) -> None:
        assert _estimate_reading_level("   ") == 0.0

    def test_single_sentence(self) -> None:
        result = _estimate_reading_level("The cat sat on the mat.")
        # 6 words, 1 sentence => ASL=6, grade = 0.39*6 + 11.8*1.5 - 15.59 = 4.15
        assert result > 0.0
        assert result <= 16.0

    def test_multiple_sentences(self) -> None:
        text = "This is sentence one. This is sentence two. And here is three."
        result = _estimate_reading_level(text)
        # 12 words, 3 sentences => ASL=4, grade = 0.39*4 + 11.8*1.5 - 15.59 = 3.37
        assert result >= 1.0
        assert result <= 16.0

    def test_long_complex_text(self) -> None:
        # Long sentences => higher reading level
        text = (
            "The comprehensive evaluation of educational methodologies "
            "demonstrates that differentiated instruction combined with "
            "formative assessment strategies significantly enhances student "
            "outcomes across diverse learning environments."
        )
        result = _estimate_reading_level(text)
        # 1 long sentence => high ASL => high grade
        assert result >= 5.0

    def test_result_clamped_minimum(self) -> None:
        # Very short text: 1 word, 1 sentence => ASL=1, grade = 0.39 + 17.7 - 15.59 = 2.5
        result = _estimate_reading_level("Hello.")
        assert result >= 1.0

    def test_result_clamped_maximum(self) -> None:
        # Extremely long single sentence (many words)
        text = " ".join(["word"] * 200) + "."
        result = _estimate_reading_level(text)
        assert result <= 16.0

    def test_text_with_question_marks(self) -> None:
        text = "What is math? It is numbers? Yes it is."
        result = _estimate_reading_level(text)
        # Should handle ? as sentence delimiter
        assert result >= 1.0

    def test_text_with_exclamation_marks(self) -> None:
        text = "Wow! That is great! I love it!"
        result = _estimate_reading_level(text)
        # Should handle ! as sentence delimiter
        assert result >= 1.0

    def test_no_period_text(self) -> None:
        # Text without sentence-ending punctuation
        # split(".") on "hello world this is a test" => ["hello world this is a test"]
        # which is one non-empty entry, so it counts as 1 sentence with 6 words
        text = "hello world this is a test"
        result = _estimate_reading_level(text)
        # ASL = 6/1 = 6 => grade = 0.39*6 + 11.8*1.5 - 15.59 = 4.45
        assert result > 0.0
        assert 4.0 <= result <= 5.0

    def test_consistent_results(self) -> None:
        text = "The student learned fractions. The student also learned decimals."
        r1 = _estimate_reading_level(text)
        r2 = _estimate_reading_level(text)
        assert r1 == r2


# ---------------------------------------------------------------------------
# make_scorecard_node (integration-level, with mock state)
# ---------------------------------------------------------------------------


class TestMakeScorecardNode:
    """Test the scorecard node by calling it with a constructed RunState dict.

    We test the node factory + the returned function with a minimal mock state.
    This tests the computation logic without needing the full LangGraph machinery.
    """

    def _make_deps(self):
        """Create a minimal AgentDeps-like object."""

        class FakeDeps:
            default_variants = "standard_html"
            max_workflow_duration_seconds = 600

            class circuit_breaker:  # noqa: N801
                @staticmethod
                def check():
                    return True

                @staticmethod
                def record_success():
                    pass

                @staticmethod
                def record_failure():
                    pass

        return FakeDeps()

    def _make_config(self):
        """Create a minimal RunnableConfig."""
        return {"configurable": {}}

    def test_scorecard_from_state(self) -> None:
        from ailine_agents.workflows._plan_nodes import make_scorecard_node

        deps = self._make_deps()
        node_fn = make_scorecard_node(deps)

        state = {
            "run_id": "test-run-1",
            "user_prompt": "Crie um plano de aula sobre fracoes para o 6o ano.",
            "draft": {
                "title": "Fracoes",
                "steps": [
                    {"title": "Introducao", "minutes": 10},
                    {"title": "Pratica", "minutes": 20},
                ],
                "objectives": [
                    {"id": "EF06MA01", "text": "Compreender fracoes"},
                    {"id": "EF06MA02", "text": "Operar com fracoes"},
                ],
                "accessibility_pack_draft": {
                    "applied_adaptations": [
                        {
                            "target": "autism",
                            "strategies": ["visual schedule", "predictability"],
                        },
                        {"target": "adhd", "strategies": ["short instructions"]},
                    ]
                },
            },
            "validation": {
                "score": 85,
                "status": "accept",
                "rag_confidence": 0.72,
            },
            "final": {
                "exports": {"standard_html": "...", "large_print_html": "..."},
            },
            "started_at": None,  # skip timing to avoid time.monotonic issues
        }

        result = node_fn(state, self._make_config())
        scorecard = result["scorecard"]

        assert scorecard is not None
        assert scorecard["quality_score"] == 85
        assert scorecard["quality_decision"] == "accept"
        assert scorecard["rag_groundedness"] == 0.72
        assert len(scorecard["standards_aligned"]) == 2
        assert scorecard["standards_aligned"][0]["code"] == "EF06MA01"
        assert len(scorecard["accessibility_adaptations"]) == 2
        assert scorecard["export_variants_count"] == 2

    def test_scorecard_empty_state(self) -> None:
        from ailine_agents.workflows._plan_nodes import make_scorecard_node

        deps = self._make_deps()
        node_fn = make_scorecard_node(deps)

        state: dict[str, object] = {
            "run_id": "test-run-2",
            "user_prompt": "",
            "draft": {},
            "validation": {},
            "final": {},
            "started_at": None,
        }

        result = node_fn(state, self._make_config())
        scorecard = result["scorecard"]

        assert scorecard is not None
        assert scorecard["quality_score"] == 0
        assert scorecard["standards_aligned"] == []
        assert scorecard["accessibility_adaptations"] == []

    def test_scorecard_reading_levels(self) -> None:
        from ailine_agents.workflows._plan_nodes import make_scorecard_node

        deps = self._make_deps()
        node_fn = make_scorecard_node(deps)

        state = {
            "run_id": "test-run-3",
            "user_prompt": "Create a lesson plan about fractions. Include activities.",
            "draft": {
                "title": "Fractions Lesson",
                "steps": [
                    {"title": "Introduction to basic fractions"},
                    {"title": "Practice with exercises"},
                ],
                "objectives": [],
            },
            "validation": {},
            "final": {},
            "started_at": None,
        }

        result = node_fn(state, self._make_config())
        scorecard = result["scorecard"]

        assert scorecard is not None
        assert scorecard["reading_level_before"] > 0
        assert scorecard["reading_level_after"] > 0

    def test_scorecard_handles_exception_gracefully(self) -> None:
        """If something goes wrong, scorecard should be None, not crash."""
        from ailine_agents.workflows._plan_nodes import make_scorecard_node

        deps = self._make_deps()
        node_fn = make_scorecard_node(deps)

        # Pass a state that will cause issues (draft not a dict)
        state: dict[str, object] = {
            "run_id": "test-run-4",
            "user_prompt": "test",
            "draft": "not-a-dict",
            "validation": {},
            "final": {},
            "started_at": None,
        }

        result = node_fn(state, self._make_config())
        # Should not crash; returns a structured fallback with error info
        scorecard = result["scorecard"]
        assert scorecard is not None
        assert "error" in scorecard
        assert scorecard["error"] == "scorecard_calculation_failed"
