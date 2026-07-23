import unittest

from retrieval.engine import IntentTag, SearchIntent, parse_intent
from scripts.prompt_library import (
    merged_related_hits,
    related_candidate_allowed,
    related_relaxation_plan,
)


def tag(tag_id: str, scopes: tuple[str, ...] = ("image", "prompt")) -> dict:
    return {"id": tag_id, "scopes": list(scopes)}


def candidate(*tags: dict, tweet_id: str = "1", score: float = 10.0) -> dict:
    return {
        "tweet_id": tweet_id,
        "score": score,
        "_tag_ids": {item["id"] for item in tags},
        "_tag_scopes": {item["id"]: set(item["scopes"]) for item in tags},
    }


class RelatedRetrievalTests(unittest.TestCase):
    def test_plan_relaxes_only_one_safe_aesthetic_facet_at_a_time(self):
        intent = parse_intent("克制暗调香水广告")
        plan = related_relaxation_plan(intent)
        self.assertIn("visual_style:minimal", plan)
        self.assertIn("color_palette:dark-moody", plan)
        self.assertNotIn("subject_type:product", plan)
        self.assertNotIn("usage:ad-campaign", plan)
        self.assertNotIn("visual_style:product-photography", plan)

    def test_locked_and_scene_constraints_are_never_related_relaxations(self):
        intent = parse_intent("森林里的水彩角色", ["color_palette:dark-moody"])
        plan = related_relaxation_plan(intent)
        self.assertNotIn("color_palette:dark-moody", plan)
        self.assertNotIn("scene:forest", plan)
        self.assertNotIn("subject_type:character", plan)
        self.assertNotIn("visual_style:watercolor", plan)

    def test_related_candidate_requires_image_evidence_for_visual_constraints(self):
        intent = SearchIntent(
            query="watercolor character",
            language="en",
            must_tags=[
                IntentTag("subject_type:character", "must"),
                IntentTag("visual_style:watercolor", "must"),
            ],
        )
        prompt_only_subject = candidate(
            tag("subject_type:character", ("prompt",)),
            tag("visual_style:watercolor"),
        )
        image_confirmed = candidate(
            tag("subject_type:character"),
            tag("visual_style:watercolor"),
        )
        self.assertFalse(related_candidate_allowed(intent, prompt_only_subject))
        self.assertTrue(related_candidate_allowed(intent, image_confirmed))

    def test_related_candidate_rejects_unrequested_text_and_document_images(self):
        intent = SearchIntent(
            query="street fashion editorial",
            language="en",
            must_tags=[IntentTag("subject_type:fashion-person", "must")],
        )
        screenshot = candidate(
            tag("subject_type:fashion-person"),
            tag("subject_type:diagram-document"),
            tag("quality_flags:embedded-text"),
        )
        self.assertFalse(related_candidate_allowed(intent, screenshot))

    def test_requested_typography_is_not_treated_as_gallery_noise(self):
        intent = SearchIntent(
            query="typography poster",
            language="en",
            must_tags=[
                IntentTag("subject_type:graphic-design", "must"),
                IntentTag("quality_flags:typography-heavy", "must"),
            ],
        )
        poster = candidate(
            tag("subject_type:graphic-design"),
            tag("quality_flags:typography-heavy"),
        )
        self.assertTrue(related_candidate_allowed(intent, poster))

    def test_related_merge_excludes_exact_ids_and_keeps_best_score(self):
        lower = candidate(tag("subject_type:product"), tweet_id="2", score=8)
        higher = candidate(tag("subject_type:product"), tweet_id="2", score=12)
        exact = candidate(tag("subject_type:product"), tweet_id="1", score=20)
        merged = merged_related_hits([[lower, exact], [higher]], {"1"})
        self.assertEqual([item["tweet_id"] for item in merged], ["2"])
        self.assertEqual(merged[0]["score"], 12)


if __name__ == "__main__":
    unittest.main()
