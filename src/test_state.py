import json
import os
import tempfile
import unittest
from unittest.mock import patch

import state_manager


class StateManagerTests(unittest.TestCase):
    def test_loads_legacy_state_and_saves_atomically(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as directory:
            path = os.path.join(directory, "state.json")
            with open(path, "w", encoding="utf-8") as state_file:
                json.dump({"processed_ids": ["old-id"]}, state_file)

            with patch.object(state_manager, "STATE_FILE", path):
                state = state_manager.load_state()
                self.assertTrue(state_manager.is_processed(state, "old-id"))
                state_manager.mark_pending(state, "pending-id")
                state_manager.mark_processed(state, "new-id")
                state_manager.save_state(state)
                loaded = state_manager.load_state()

            self.assertEqual(loaded["processed_ids"], {"old-id", "new-id"})
            self.assertEqual(loaded["pending_ids"], {"pending-id"})

    def test_rejects_corrupt_or_invalid_state_without_resetting_checkpoint(self):
        for contents in ("{", "[]", '{"processed_ids": "message-id"}'):
            with self.subTest(contents=contents), tempfile.TemporaryDirectory(dir=os.getcwd()) as directory:
                path = os.path.join(directory, "state.json")
                with open(path, "w", encoding="utf-8") as state_file:
                    state_file.write(contents)
                with patch.object(state_manager, "STATE_FILE", path):
                    with self.assertRaisesRegex(ValueError, "checkpoint"):
                        state_manager.load_state()


if __name__ == "__main__":
    unittest.main()
