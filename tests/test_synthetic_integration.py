import unittest

import pandas as pd

from src.data.integration import (
    PREFERENCE_COLUMNS,
    create_synthetic_user_preferences,
    validate_synthetic_user_preferences,
)


class SyntheticPreferenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.users = pd.DataFrame(
            {
                "user_id": range(1, 13),
                "age": [18, 19, 20, 21, 22, 25, 34, 35, 40, 50, 55, 58],
                "gender": ["Female", "Male", "Other"] * 4,
            }
        )
        profiles = []
        for age, gender, genre in [
            ("12-20", "Female", "Pop"),
            ("20-35", "Male", "Rap"),
            ("35-60", "Others", "Melody"),
            ("60+", "Female", "Classical"),
        ]:
            row = {"Age": age, "Gender": gender}
            row.update({column: "sample" for column in PREFERENCE_COLUMNS})
            row["fav_music_genre"] = genre
            row["music_recc_rating"] = 4
            profiles.append(row)
        profiles[0]["fav_pod_genre"] = None
        self.survey = pd.DataFrame(profiles)

    def test_mapping_is_reproducible_and_preserves_profile_quotas(self):
        first, first_metadata = create_synthetic_user_preferences(self.users, self.survey, seed=7)
        second, second_metadata = create_synthetic_user_preferences(self.users, self.survey, seed=7)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first_metadata, second_metadata)
        self.assertEqual(len(first), len(self.users))
        self.assertEqual(first["user_id"].nunique(), len(self.users))
        self.assertEqual(first["source_response_row"].value_counts().to_dict(), {2: 3, 3: 3, 4: 3, 5: 3})
        result = validate_synthetic_user_preferences(self.users, self.survey, first, seed=7)
        self.assertEqual(result["rows"], len(self.users))
        self.assertEqual(int(first["fav_pod_genre"].isna().sum()), 3)


if __name__ == "__main__":
    unittest.main()
