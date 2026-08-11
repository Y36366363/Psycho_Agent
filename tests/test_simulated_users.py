import unittest

from psycho_agent.simulated_users import (
    build_simulated_user_prompt,
    load_simulated_user_profiles,
    profile_coverage,
)


class SimulatedUserTests(unittest.TestCase):
    def test_profiles_cover_requested_variation(self) -> None:
        profiles = load_simulated_user_profiles()
        coverage = profile_coverage(profiles)
        self.assertGreaterEqual(coverage["profiles"], 8)
        self.assertEqual(coverage["trust_levels"], ["high", "low", "mixed"])
        self.assertGreaterEqual(coverage["cultural_contexts"], 5)
        self.assertGreaterEqual(coverage["ai_attitudes"], 5)

    def test_prompt_requires_behavioral_reaction_without_stereotyping(self) -> None:
        profile = load_simulated_user_profiles()[0]
        prompt = build_simulated_user_prompt(profile)
        self.assertIn("React to the assistant's actual behavior", prompt)
        self.assertIn("Avoid these assumptions", prompt)
        self.assertIn(profile.avoid_assumptions[0], prompt)


if __name__ == "__main__":
    unittest.main()
