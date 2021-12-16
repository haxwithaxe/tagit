#!/usr/bin/env python3

import glob
import os
import stat
import tempfile
import unittest

import tagit


TEST_TAG_CACHE = 'tagit_test.tags.cache'
TEST_INPUT_FILE = 'tagit_test.zip'
TEST_OUTPUT_FILE = 'tagit_test._tags.bar.foo._tags.zip'
TEST_OUTPUT_PARTS = ['tagit_test', ['bar', 'foo'], [], '.zip']
TEST_OLD_FILE = 'tagit_test._tags.foo._tags.zip'
MISSING_DIRECTORY = 'this directory doesn\'t exist'
MISSING_DIRECTORY_CACHE_FILE = 'this directory doesn\'t exist/tagit_test.tags.cache'


class _FileModTestCase(unittest.TestCase):

    def _path(self, *parts):
        return os.path.join(self.tmpdir, *parts)

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='tagit_test-{}-'.format(self.__class__.__name__))
        os.chmod(self.tmpdir, mode=stat.S_IRWXU)

    def tearDown(self):
        os.chmod(self.tmpdir, mode=stat.S_IRWXU)
        for filename in glob.glob(self._path('*')):
            os.remove(filename)
        os.removedirs(self.tmpdir)


class EscapeTag(unittest.TestCase):

    def test_escapes_tag(self):
        self.assertEqual(tagit.escape_tag('foo bar.baz'), 'foo_bar_baz')


class SplitFilename(unittest.TestCase):

    def test_split_filename_without_tags(self):
        self.assertEqual(tagit.split_filename('tagit_test_file.zip'), ('tagit_test_file', [], '.zip'))

    def test_split_filename_with_tags(self):
        self.assertEqual(tagit.split_filename('tagit_test_file._tags.bar.foo._tags.zip'), ('tagit_test_file', ['bar', 'foo'], '.zip'))

    def test_split_filename_without_tags_without_ext(self):
        self.assertEqual(tagit.split_filename('tagit_test_file.zip'), ('tagit_test_file', [], '.zip'))

    def test_split_filename_with_tags_without_ext(self):
        self.assertEqual(tagit.split_filename('tagit_test_file._tags.bar.foo._tags'), ('tagit_test_file', ['bar', 'foo'], '._tags'))


class JoinFilename(unittest.TestCase):

    def test_join_filename_with_tags(self):
        self.assertEqual(tagit.join_filename('tagit_test_file', ['bar', 'foo'], '.zip'), 'tagit_test_file._tags.bar.foo._tags.zip')

    def test_join_filename_with_tags_without_ext(self):
        # Missing extensions are replaced with TAGS_PREFIX in split_filename
        self.assertEqual(tagit.join_filename('tagit_test_file', ['bar', 'foo'], '._tags'), 'tagit_test_file._tags.bar.foo._tags')

    def test_join_filename_without_tags(self):
        self.assertEqual(tagit.join_filename('tagit_test_file', [], '.zip'), 'tagit_test_file.zip')

    def test_join_filename_without_tags_without_ext(self):
        # Missing extensions are replaced with TAGS_PREFIX in split_filename
        self.assertEqual(tagit.join_filename('tagit_test_file', [], '._tags'), 'tagit_test_file')


class ReconsileTags(unittest.TestCase):

    def test_reconsile_tags_add_tags(self):
        self.assertEqual(tagit.reconsile_tags(['foo'], ['bar'], []), ['bar', 'foo'])

    def test_reconsile_tags_remove_tags(self):
        self.assertEqual(tagit.reconsile_tags(['foo', 'bar'], [], ['bar']), ['foo'])

    def test_reconsile_tags_remove_missing_tags(self):
        self.assertEqual(tagit.reconsile_tags(['bar', 'foo'], [], ['baz']), ['bar', 'foo'])

    def test_reconsile_tags_add_and_remove_tags(self):
        # Add 'baz' and remove 'bar'
        self.assertEqual(tagit.reconsile_tags(['bar', 'foo'], ['baz'], ['bar']), ['baz', 'foo'])


class LoadTagCache(_FileModTestCase):

    def test_load_tag_cache_empty_cache(self):
        open(self._path(TEST_TAG_CACHE), 'w').close()
        self.assertEqual(tagit.load_tag_cache(self._path(TEST_TAG_CACHE)), [])

    def test_load_tag_cache_full_cache(self):
        with open(self._path(TEST_TAG_CACHE), 'w') as cache:
            cache.write('bar\nfoo')
        self.assertEqual(tagit.load_tag_cache(self._path(TEST_TAG_CACHE)), ['bar', 'foo'])

    def test_load_tag_cache_missing_cache(self):
        assert (not os.path.exists(self._path(TEST_TAG_CACHE)))
        self.assertEqual(tagit.load_tag_cache(self._path(TEST_TAG_CACHE)), [])

    def test_load_tag_cache_bad_permissions(self):
        open(self._path(TEST_TAG_CACHE), 'w').close()
        os.chmod(self._path(TEST_TAG_CACHE), mode=stat.S_IWUSR)  # Disable read access
        with self.assertRaises(tagit.CacheError):
            tagit.load_tag_cache(self._path(TEST_TAG_CACHE))


class WriteTagsCache(_FileModTestCase):

    def test_cache_tags_nominal(self):
        tagit.write_tag_cache(['foo', 'bar'], self._path(TEST_TAG_CACHE))
        with open(self._path(TEST_TAG_CACHE)) as cache:
            output = cache.read()
        self.assertEqual(output, 'bar\nfoo')

    def test_cache_tags_bad_permissions(self):
        open(self._path(TEST_TAG_CACHE), 'w').close()
        os.chmod(self._path(TEST_TAG_CACHE), mode=stat.S_IRUSR)  # Disable write access
        with self.assertRaises(tagit.CacheError):
            tagit.write_tag_cache([], self._path(TEST_TAG_CACHE))

    def text_cach_tags_missing_parent_directory(self):
        assert not os.path.exists(MISSING_DIRECTORY)
        with self.assertRaises(tagit.CacheError):
            tagit.write_tag_cache([], MISSING_DIRECTORY_CACHE_FILE)


class CopyWriteMethod(_FileModTestCase):

    def test_copy_write_method_missing_file(self):
        assert not os.path.exists(self._path(TEST_INPUT_FILE))
        with self.assertRaises(FileNotFoundError):
            tagit.copy_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertFalse(os.path.exists(self._path(TEST_OUTPUT_FILE)))

    def test_copy_write_method_bad_permission(self):
        open(self._path(TEST_INPUT_FILE), 'w').close()
        open(self._path(TEST_OLD_FILE), 'w').close()
        os.chmod(self.tmpdir, mode=stat.S_IRUSR|stat.S_IXUSR)  # Disable write access
        with self.assertRaises(PermissionError):
            tagit.copy_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertTrue(os.path.isfile(self._path(TEST_INPUT_FILE)))
        self.assertTrue(os.path.isfile(self._path(TEST_OLD_FILE)))
        self.assertFalse(os.path.exists(self._path(TEST_OUTPUT_FILE)))

    def test_copy_write_method_remove_old_and_copy(self):
        open(self._path(TEST_INPUT_FILE), 'w').close()
        open(self._path(TEST_OLD_FILE), 'w').close()
        tagit.copy_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertTrue(os.path.isfile(self._path(TEST_INPUT_FILE)))
        self.assertFalse(os.path.exists(self._path(TEST_OLD_FILE)))
        self.assertTrue(os.path.isfile(self._path(TEST_OUTPUT_FILE)))


class LinkWriteMethod(_FileModTestCase):

    def test_link_write_method_missing_file(self):
        assert not os.path.exists(self._path(TEST_INPUT_FILE))
        with self.assertRaises(FileNotFoundError):
            tagit.link_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertFalse(os.path.exists(self._path(TEST_OUTPUT_FILE)))

    def test_link_write_method_bad_permission(self):
        open(self._path(TEST_INPUT_FILE), 'w').close()
        os.symlink(self._path(TEST_INPUT_FILE), self._path(TEST_OLD_FILE))
        os.chmod(self.tmpdir, mode=stat.S_IRUSR|stat.S_IXUSR)  # Disable write access
        with self.assertRaises(PermissionError):
            tagit.link_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertTrue(os.path.isfile(self._path(TEST_INPUT_FILE)))
        self.assertTrue(os.path.islink(self._path(TEST_OLD_FILE)))
        self.assertFalse(os.path.exists(self._path(TEST_OUTPUT_FILE)))

    def test_link_write_method_remove_old_and_link(self):
        open(self._path(TEST_INPUT_FILE), 'w').close()
        os.symlink(self._path(TEST_INPUT_FILE), self._path(TEST_OLD_FILE))
        tagit.link_write_method(self._path(TEST_INPUT_FILE), self._path(TEST_OUTPUT_PARTS[0]), *TEST_OUTPUT_PARTS[1:])
        self.assertTrue(os.path.isfile(self._path(TEST_INPUT_FILE)))
        self.assertFalse(os.path.exists(self._path(TEST_OLD_FILE)))
        self.assertTrue(os.path.islink(self._path(TEST_OUTPUT_FILE)))


class MoveWriteMethod(unittest.TestCase):
    # Currently `tagit.move_write_method` is `shutil.move` so it isn't being
    #  tested directly.
    pass


class TagFile(_FileModTestCase):

    def test_tag_file_missing_file(self):
        assert (not os.path.exists(self._path(TEST_INPUT_FILE)))
        with self.assertRaises(tagit.FailedToTag):
            tagit.tag_file(self._path(TEST_INPUT_FILE), ['foo', 'bar'], [], tagit.move_write_method)

    def test_tag_file_bad_permissions(self):
        open(self._path(TEST_INPUT_FILE), 'w').close()
        os.chmod(self.tmpdir, mode=stat.S_IRUSR)  # Disable write access
        with self.assertRaises(tagit.FailedToTag):
            tagit.tag_file(self._path(TEST_INPUT_FILE), ['foo', 'bar'], [], tagit.move_write_method)

    def test_tag_file_add_tags(self):
        open(self._path('foo'), 'w').close()
        open(self._path(TEST_INPUT_FILE), 'w').close()
        tagit.tag_file(self._path(TEST_INPUT_FILE), ['foo', 'bar'], [], tagit.move_write_method)
        self.assertTrue(os.path.isfile(self._path(TEST_OUTPUT_FILE)))
        self.assertFalse(os.path.isfile(self._path(TEST_INPUT_FILE)))

    def test_tag_file_remove_all_tags(self):
        open(self._path(TEST_OUTPUT_FILE), 'w').close()
        tagit.tag_file(self._path(TEST_OUTPUT_FILE), [], ['foo', 'bar'], tagit.move_write_method)
        self.assertTrue(os.path.isfile(self._path(TEST_INPUT_FILE)))
        self.assertFalse(os.path.isfile(self._path(TEST_OUTPUT_FILE)))
