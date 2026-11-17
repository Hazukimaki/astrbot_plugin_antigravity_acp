"""Tests for Safe Mode rule 4 compatibility rewriting (issue #19)."""

import unittest
from unittest.mock import patch

from tests import astrbot_stub  # noqa: F401

from agy_provider.system_prompt import filter_host_capabilities


_SAFE_MODE_HEADER = "You are running in Safe Mode."
_RULES_HEADER = "Follow these rules:"
_SAFETY_OPEN = "<safety_instructions>"
_SAFETY_CLOSE = "</safety_instructions>"

_RULE_1 = "- Do not execute destructive actions."
_RULE_5 = "- Answer concisely and accurately."

_PREFIX = "- Follow "
_PREFIX_LOWER = "- follow "
_TOKEN = "style/role" + "-play"
_SAFE_TOKEN = "style and role-play"
_TAIL_PERIOD = " instructions only when they do not conflict with these rules."
_TAIL_NO_PERIOD = " instructions only when they do not conflict with these rules"

_RULE_4 = _PREFIX + _TOKEN + _TAIL_PERIOD
_RULE_4_LOWER = _PREFIX_LOWER + _TOKEN + _TAIL_PERIOD
_RULE_4_NO_PERIOD = _PREFIX + _TOKEN + _TAIL_NO_PERIOD
_RULE_4_LOWER_NO_PERIOD = _PREFIX_LOWER + _TOKEN + _TAIL_NO_PERIOD

_RULE_4_REWRITTEN = _PREFIX + _SAFE_TOKEN + _TAIL_PERIOD
_RULE_4_REWRITTEN_LOWER = _PREFIX_LOWER + _SAFE_TOKEN + _TAIL_PERIOD
_RULE_4_REWRITTEN_NO_PERIOD = _PREFIX + _SAFE_TOKEN + _TAIL_NO_PERIOD
_RULE_4_REWRITTEN_LOWER_NO_PERIOD = _PREFIX_LOWER + _SAFE_TOKEN + _TAIL_NO_PERIOD


def _bare_safe_mode_block(rule_line, *, newline="\n", blank_between_headers=False):
    between = newline * (2 if blank_between_headers else 1)
    return (
        _SAFE_MODE_HEADER
        + between
        + _RULES_HEADER
        + newline
        + _RULE_1
        + newline
        + rule_line
        + newline
        + _RULE_5
    )


def _tagged_safe_mode_block(rule_line, *, newline="\n"):
    return (
        _SAFETY_OPEN
        + newline
        + _bare_safe_mode_block(rule_line, newline=newline)
        + newline
        + _SAFETY_CLOSE
    )


class SafeModeRuleRewriteTests(unittest.TestCase):
    def test_safe_mode_block_rewrites_rule_four_and_preserves_context(self):
        for blank in (False, True):
            with self.subTest(blank_between_headers=blank):
                block = _bare_safe_mode_block(_RULE_4, blank_between_headers=blank)
                expected_block = _bare_safe_mode_block(
                    _RULE_4_REWRITTEN, blank_between_headers=blank
                )
                source = f"Persona intro\n\n{block}\n\nPersona outro"
                expected = f"Persona intro\n\n{expected_block}\n\nPersona outro"
                with patch("agy_provider.system_prompt.logger.debug") as debug:
                    result = filter_host_capabilities(source)
                    self.assertEqual(result, expected)
                    self.assertIn(_RULE_4_REWRITTEN, result)
                    self.assertNotIn(_TOKEN, result)
                    debug.assert_not_called()

    def test_rewrite_is_idempotent(self):
        source = "Persona\n" + _bare_safe_mode_block(_RULE_4) + "\nOutro"
        first = filter_host_capabilities(source)
        with patch("agy_provider.system_prompt.logger.debug") as debug:
            second = filter_host_capabilities(first)
            self.assertEqual(second, first)
            debug.assert_not_called()

    def test_safe_variants_remain_unchanged(self):
        variants = {
            "space_instead_of_slash": _PREFIX + "style role-play" + _TAIL_PERIOD,
            "no_hyphen_roleplay": _PREFIX + "style/roleplay" + _TAIL_PERIOD,
            "the_rules_above": (
                _PREFIX
                + _TOKEN
                + " instructions only when they do not conflict with the rules above."
            ),
            "persona_and_style": _PREFIX + "persona and style" + _TAIL_PERIOD,
        }
        for name, variant_line in variants.items():
            with self.subTest(variant=name):
                source = "Persona\n" + _bare_safe_mode_block(variant_line) + "\nOutro"
                with patch("agy_provider.system_prompt.logger.debug") as debug:
                    self.assertEqual(filter_host_capabilities(source), source)
                    debug.assert_not_called()

    def test_normalization_tolerance_lowercase_and_optional_period(self):
        cases = (
            ("lowercase_follow", _RULE_4_LOWER, _RULE_4_REWRITTEN_LOWER),
            ("no_period", _RULE_4_NO_PERIOD, _RULE_4_REWRITTEN_NO_PERIOD),
            (
                "lowercase_and_no_period",
                _RULE_4_LOWER_NO_PERIOD,
                _RULE_4_REWRITTEN_LOWER_NO_PERIOD,
            ),
            ("trailing_spaces", _RULE_4 + "  \t", _RULE_4_REWRITTEN + "  \t"),
        )
        for name, rule_line, expected_line in cases:
            with self.subTest(case=name):
                source = _bare_safe_mode_block(rule_line)
                expected = _bare_safe_mode_block(expected_line)
                self.assertEqual(filter_host_capabilities(source), expected)

    def test_context_gating_fail_open_cases(self):
        cases = {
            "rule_only_no_headers": f"Persona\n{_RULE_4}\nOutro",
            "only_safe_mode_header": (
                f"{_SAFE_MODE_HEADER}\n{_RULE_1}\n{_RULE_4}\n{_RULE_5}"
            ),
            "only_rules_header": (
                f"{_RULES_HEADER}\n{_RULE_1}\n{_RULE_4}\n{_RULE_5}"
            ),
            "inline_prefix_inside_block": _bare_safe_mode_block("Note: " + _RULE_4),
            "inline_suffix_inside_block": _bare_safe_mode_block(_RULE_4 + " Extra."),
            "quoted_single_line": f"> {_RULE_4}",
            "quoted_block": "\n".join(
                f"> {line}"
                for line in _bare_safe_mode_block(_RULE_4).split("\n")
            ),
            "indented_rule_line": _bare_safe_mode_block("  " + _RULE_4),
            "indented_header": "  " + _bare_safe_mode_block(_RULE_4).replace("\n", "\n  "),
            "fenced_backticks": "```\n" + _bare_safe_mode_block(_RULE_4) + "\n```",
            "fenced_tildes": "~~~\n" + _bare_safe_mode_block(_RULE_4) + "\n~~~",
            "blank_line_breaks_list": (
                f"{_SAFE_MODE_HEADER}\n{_RULES_HEADER}\n\n{_RULE_4}"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self.assertEqual(filter_host_capabilities(source), source)

    def test_astrbot_430_safety_instructions_wrapper(self):
        tagged = _tagged_safe_mode_block(_RULE_4)
        expected_tagged = _tagged_safe_mode_block(_RULE_4_REWRITTEN)
        source = f"Persona header\n\n{tagged}\n\nPersona footer"
        expected = f"Persona header\n\n{expected_tagged}\n\nPersona footer"
        with patch("agy_provider.system_prompt.logger.debug") as debug:
            result = filter_host_capabilities(source)
            self.assertEqual(result, expected)
            self.assertIn(_SAFETY_OPEN, result)
            self.assertIn(_SAFETY_CLOSE, result)
            debug.assert_not_called()

    def test_invalid_safety_instructions_wrappers_fail_open(self):
        valid_body = _bare_safe_mode_block(_RULE_4)
        cases = {
            "unclosed_tag": f"{_SAFETY_OPEN}\n{valid_body}",
            "nested_tag": (
                f"{_SAFETY_OPEN}\n{_SAFETY_OPEN}\n{valid_body}\n{_SAFETY_CLOSE}\n{_SAFETY_CLOSE}"
            ),
            "tag_with_attributes": (
                f'<safety_instructions scope="host">\n{valid_body}\n{_SAFETY_CLOSE}'
            ),
            "trailing_prose_inside_tag": (
                f"{_SAFETY_OPEN}\n{valid_body}\nExtra prose\n{_SAFETY_CLOSE}"
            ),
            "missing_safe_mode_header_inside_tag": (
                f"{_SAFETY_OPEN}\n{_RULES_HEADER}\n{_RULE_4}\n{_SAFETY_CLOSE}"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self.assertEqual(filter_host_capabilities(source), source)

    def test_crlf_line_endings_preserved(self):
        for builder in (_bare_safe_mode_block, _tagged_safe_mode_block):
            with self.subTest(builder=builder.__name__):
                block = builder(_RULE_4, newline="\r\n")
                expected_block = builder(_RULE_4_REWRITTEN, newline="\r\n")
                source = f"Persona\r\n\r\n{block}\r\n\r\nOutro"
                expected = f"Persona\r\n\r\n{expected_block}\r\n\r\nOutro"
                result = filter_host_capabilities(source)
                self.assertEqual(result, expected)
                self.assertNotIn(_TOKEN, result)
                self.assertEqual(result.count("\r\n"), source.count("\r\n"))

    def test_debug_logs_never_contain_system_content(self):
        canary = "CANARY_SECRET_PERSONA_9182"
        fail_open_cases = {
            "quoted_block": "\n".join(
                f"> {line}"
                for line in _bare_safe_mode_block(_RULE_4).split("\n")
            ),
            "missing_rules_header": f"{_SAFE_MODE_HEADER}\n{_RULE_1}\n{_RULE_4}",
            "missing_safe_mode_header": f"{_RULES_HEADER}\n{_RULE_1}\n{_RULE_4}",
            "unclosed_tag": f"{_SAFETY_OPEN}\n{_bare_safe_mode_block(_RULE_4)}",
            "trailing_prose_in_tag": (
                f"{_SAFETY_OPEN}\n{_bare_safe_mode_block(_RULE_4)}\nTrailing prose\n{_SAFETY_CLOSE}"
            ),
        }
        for name, body in fail_open_cases.items():
            with self.subTest(fail_open=name):
                source = f"{canary}\n{body}"
                with patch("agy_provider.system_prompt.logger.debug") as debug:
                    self.assertEqual(filter_host_capabilities(source), source)
                    debug.assert_called_once()
                    logged = str(debug.call_args_list)
                    self.assertIn("safe_mode_rule_unmatched", logged)
                    self.assertNotIn(canary, logged)
                    self.assertNotIn(_TOKEN, logged)
                    self.assertNotIn(_RULE_4, logged)
                    self.assertNotIn(source, logged)

        # Clean hit emits no debug log at all.
        clean_hit = f"{canary}\n{_tagged_safe_mode_block(_RULE_4)}"
        with patch("agy_provider.system_prompt.logger.debug") as debug:
            self.assertNotEqual(filter_host_capabilities(clean_hit), clean_hit)
            debug.assert_not_called()

        # Hit combined with an unverified block logs only reason codes, not system text.
        mixed = (
            f"{canary}\n"
            f"{_tagged_safe_mode_block(_RULE_4)}\n"
            '<execution_environment runtime="local">\nPersona block\n</execution_environment>'
        )
        with patch("agy_provider.system_prompt.logger.debug") as debug:
            result = filter_host_capabilities(mixed)
            self.assertIn(_RULE_4_REWRITTEN, result)
            self.assertNotIn(_TOKEN, result)
            debug.assert_called_once()
            logged = str(debug.call_args_list)
            self.assertIn("tag_unverified", logged)
            self.assertNotIn(canary, logged)
            self.assertNotIn(_SAFE_TOKEN, logged)
            self.assertNotIn(mixed, logged)

    def test_combined_with_host_capability_removal(self):
        exec_block = (
            '<execution_environment runtime="local">\n'
            "## Execution policy\n"
            "Do not use host shell.\n"
            "</execution_environment>"
        )
        source = (
            "Persona\n"
            + _tagged_safe_mode_block(_RULE_4)
            + "\n"
            + exec_block
            + "\nFooter"
        )
        expected = (
            "Persona\n"
            + _tagged_safe_mode_block(_RULE_4_REWRITTEN)
            + "\nFooter"
        )
        with patch("agy_provider.system_prompt.logger.debug") as debug:
            self.assertEqual(filter_host_capabilities(source), expected)
            debug.assert_not_called()


if __name__ == "__main__":
    unittest.main()
