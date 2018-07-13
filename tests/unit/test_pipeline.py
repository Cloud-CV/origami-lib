import unittest
import tempfile
import os

from origami_lib.pipeline import OrigamiCache


class OrigamiCacheTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.non_existing_dir = os.path.join(self.tempdir, "xxxxxxxxxx")

    def test__create_cache(self):
        cache_obj = OrigamiCache(cache_path=self.tempdir)
        cache_id = cache_obj._create_cache()

        assert cache_obj.cache_id == cache_id
        assert cache_obj.cache_dir == '{}/{}'.format(self.tempdir, cache_id)

    def test_delete_current_cache(self):
        cache_obj = OrigamiCache(cache_path=self.tempdir)
        cache_dir = cache_obj.cache_dir

        assert os.path.exists(cache_dir)

        cache_obj.delete_current_cache()

        assert not os.path.exists(cache_dir)
        assert cache_obj.cache_dir == ""
        assert cache_obj.cache_id == ""

    def test_new_cache(self):
        cache_obj = OrigamiCache(cache_path=self.tempdir)
        cache_id = cache_obj.cache_id

        new_cache_id = cache_obj.new_cache()

        assert new_cache_id == cache_obj.cache_id
        assert cache_id != new_cache_id
