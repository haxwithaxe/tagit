#!/usr/bin/env python3

import argparse
import glob
import logging
import os
import shutil
import sys


DEFAULT_TAG_CACHE = '.tagit.tags.cache'
TAG_DELIM = '.'
TAGS_PREFIX = '._tags'


class TagitException(Exception):
    pass


class FailedToTag(TagitException):
    pass


class CacheError(TagitException):
    pass


def escape_tag(tag):
    return tag.replace(' ', '_').replace(TAG_DELIM, '_')


def load_tag_cache(cache_filename):
    try:
        with open(cache_filename, 'r') as cache:
            tags_text = cache.read()
    except FileNotFoundError:
        return []
    except PermissionError:
        raise CacheError('Failed to read the tag cache from "{}" because the user does not have permission.'.format(cache_filename))
    else:
        return [tag for tag in tags_text.strip().split('\n') if tag]


def write_tag_cache(tags, cache_filename):
    existing_tags = load_tag_cache(cache_filename)
    unique_tags = list(set([escape_tag(tag) for tag in tags] + existing_tags))
    unique_tags.sort()
    try:
        with open(cache_filename, 'w') as cache:
            cache.write('\n'.join(unique_tags))
    except FileNotFoundError:
        raise CacheError('Failed to cache the tags to "{}" because the directory does not exist.'.format(cache_filename))
    except PermissionError:
        raise CacheError('Failed to cache the tags to "{}" because the user does not have permission.'.format(cache_filename))


def split_filename(filename):
    name_part, ext = os.path.splitext(filename)
    if TAGS_PREFIX in name_part:
        name, tags_string, *_ = name_part.split(TAGS_PREFIX)
        tags = tags_string.strip(TAG_DELIM).split(TAG_DELIM)
    else:
        name = name_part
        tags = []
    ext = ext or TAGS_PREFIX
    return name, tags, ext


def join_filename(name, tags, ext):
    if not tags:
        if ext == TAGS_PREFIX:
            return name
        return '{}{}'.format(name, ext)
    tags_string = TAG_DELIM.join(tags)
    if ext == TAGS_PREFIX:
        return '{}{}.{}{}'.format(name, TAGS_PREFIX, tags_string, ext)
    return '{}{}.{}{}{}'.format(name, TAGS_PREFIX, tags_string, TAGS_PREFIX,
                                ext)


def reconsile_tags(existing_tags, new_tags, remove_tags):
    logging.debug('existing_tags: %s', existing_tags)
    # Add tags
    uniq_tags = list(set([escape_tag(tag) for tag in new_tags] + existing_tags))
    # Remove tags
    if remove_tags:
        logging.debug('Hit remove')
        for tag in [escape_tag(tag) for tag in remove_tags]:
            try:
                uniq_tags.pop(uniq_tags.index(tag))
                logging.debug('Removed tag: %s', tag)
            except (IndexError, ValueError):
                pass
    uniq_tags.sort()
    return uniq_tags


def copy_write_method(filename, name, add_tags, remove_tags, ext):
    tags = []
    tagged = glob.glob(join_filename(name, ['*'], ext))
    for tagged_file in tagged:
        if tagged_file != filename:
            _, tgs, _ = split_filename(tagged_file)
            tags.extend(tgs)
            os.remove(tagged_file)
    uniq_tags = reconsile_tags(tags, add_tags, remove_tags)
    new_filename = join_filename(name, uniq_tags, ext)
    if filename == new_filename:
        return
    shutil.copy(filename, new_filename)
    return new_filename


def link_write_method(filename, name, add_tags, remove_tags, ext):
    tags = []
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    tagged = glob.glob(join_filename(name, ['*'], ext))
    for tagged_file in tagged:
        if tagged_file != filename and os.path.islink(tagged_file):
            _, tgs, _ = split_filename(tagged_file)
            tags.extend(tgs)
            os.remove(tagged_file)
    uniq_tags = reconsile_tags(tags, add_tags, remove_tags)
    new_filename = join_filename(name, uniq_tags, ext)
    if filename == new_filename:
        return
    os.symlink(os.path.abspath(filename), new_filename)
    return new_filename

def move_write_method(filename, name, add_tags, remove_tags, ext):
    uniq_tags = reconsile_tags([], add_tags, remove_tags)
    new_filename = join_filename(name, uniq_tags, ext)
    if filename == new_filename:
        return
    shutil.move(filename, new_filename)
    return new_filename

def tag_file(filename, add_tags, remove_tags, write_method):
    name, existing_tags, ext = split_filename(filename)
    add_tags.extend(existing_tags)
    try:
        new_filename = write_method(filename, name, add_tags, remove_tags, ext)
    except FileNotFoundError:
        raise FailedToTag('Failed to tag "{}" because it does not exist.'.format(filename))
    except PermissionError:
        raise FailedToTag('Failed to tag "{}" because the user doesn\'t have permission.'.format(filename))
    if not new_filename:
        return True
    if write_method == move_write_method:
        logging.info('Moved "%s" to "%s"', filename, new_filename)
    else:
        logging.info('Tagged "%s" as "%s"', filename, new_filename)
    return True


def tag_files(files, add_tags, remove_tags, write_method):
    for filename in files:
        tag_file(filename, add_tags, remove_tags, write_method)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ro-cache', action='store_true',
                        default=False)
    parser.add_argument('--cache', default=os.path.join(os.curdir, DEFAULT_TAG_CACHE))
    parser.add_argument('-c', '--copy', action='store_true', default=False)
    parser.add_argument('-l', '--link', action='store_true', default=False)
    parser.add_argument('-m', '--move', action='store_true', default=True)
    parser.add_argument('-f', '--files', nargs='+', default=[])
    parser.add_argument('--log-level', type=int, choices=[
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL
    ], default=logging.INFO)
    parser.add_argument('-t', '--tags', nargs='+', default=[])
    parser.add_argument('-r', '--remove-tags', nargs='+', default=[])
    parser.add_argument('--autocomplete', nargs='?', default=False)

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    # Handle autocomplete
    #  args.autocomplete can be falsey and still be present
    if args.autocomplete is not False:
        if isinstance(args.autocomplete, str):
            if args.autocomplete and args.autocomplete[-1] != ' ':
                tags = load_tag_cache(args.cache)
                for tag in tags:
                    if args.autocomplete in tag:
                        print(tag)
                return
        print('\n'.join(load_tag_cache(args.cache)))
        return

    write_method = move_write_method
    if args.copy:
        write_method = copy_write_method
    if args.link:
        write_method = link_write_method
    if not args.ro_cache:
        write_tag_cache(args.tags, args.cache)
    tag_files(args.files, args.tags, args.remove_tags, write_method)


if __name__ == '__main__':
    try:
        main()
    except TagitException as err:
        print(err, file=sys.stderr)
        sys.exit(1)
