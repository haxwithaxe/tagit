# Description
Tagit is a tool to tag files in a way that tools already existing in the OS can interact with. There is no database and the tags follow the files wherever they go (in the default mode). This should work in all OSs that support python3.6 or newer. Tagging hasn't been tested on anything but Linux as of writing. For bash users there is tab completion.

# Usage

* `--ro-cache` - Treat cache as read only.
* `--cache <cache_filename>` - Specify the cache file to use. The default is `.tagit.tags.cache` in the current working directory.
* `-c`, `--copy` - Copy files to their tagged form.
* `-l`, `--link` - Symlink files to their tagged form.
* `-m`, `--move` - Move files to their tagged form.
* `-f FILE [FILE ...]`, `--files FILE [FILE ...]` - Specifies files to tag.
* `--log-level {10,20,30,40,50}` - Specify a log level. 10 is debug, 50 is critical. Values correspond to log levels in python's `logging` module.
* `-t TAG [TAG ...]`, `--tags TAG [TAG ...]` - Specifies one or more tags to add. This can be used at the same time as `-r`.
* `-r TAG [TAG ...]`, `--remove-tags TAG [TAG ...]` - Specifies one or more tags to remove. This can be used at the same time as `-t`. Tags are added before tags are removed so tags that are specified for both adding and removing will only be removed.
* `--autocomplete [FRAGMENT]` - For use by `tagit.completion`. This short circuits any other options.

# Examples
These examples use move mode.

Remove `tag2`.
```
$ ls
foo._tags.tag1.tag2._tags.zip
$ tagit -f foo._tags.tag1.tag2._tags.zip -r tag2
$ ls
foo._tags.tag1._tags.zip
```

Remove all tags.
```
$ ls
foo._tags.tag1.tag2._tags.zip
$ tagit -f foo._tags.tag1.tag2._tags.zip -r tag1 tag2
$ ls
foo.zip
```

Replace `tag2` with `tag3`.
```
$ ls
foo._tags.tag1.tag2._tags.zip
$ tagit -f foo._tags.tag1.tag2._tags.zip -t tag3 -r tag2
$ ls
foo._tags.tag1.tag3._tags.zip
```


## Modes

### Move (default)
Move mode (`-m` or `--move`) is the default mode. It moves the specified files to the same directory they are in with tags added to the filename.
```
$ ls
foo.zip
$ tagit -f foo.zip -t tag1
$ ls
foo._tags.tag1._tags.zip
$ tagit -f foo._tags.tag1._tags.zip -t tag2
$ ls
foo._tags.tag1.tag2._tags.zip
```
Notice that the filename being tagged changes to the tagged form in the second call to `tagit`. This is unique to the move mode since the original file has been moved and cannot be referenced again.


### Copy
Copy mode (`-m` or `--move`) copies the specified files to the same directory they are in with tags added to the filename. 
```
$ ls
foo.zip
$ tagit --copy -f foo.zip -t tag1
$ ls
foo.zip
foo._tags.tag1._tags.zip
```

It also removes previous tagged forms of the files. The previously tagged forms of the files are detected using globbing (example glob pattern: `foo._tags.*._tags.zip`) so any files named like the tagged files will be removed as well.
```
$ ls
foo.zip
foo._tags.tag1._tags.zip
$ tagit --copy -f foo.zip -t tag2
$ ls
foo.zip
foo._tags.tag1.tag2._tags.zip
```
Notice that the filename being tagged *does not* change to the tagged form in the second call to `tagit`. If the tagged form is tagged it will not remove the tagged file being tagged.


### Link
Link mode (`-l` or `--link`) symlinks the specified files to the same directory they are in with tags added to the filename.
```
$ ls /folder
foo.zip
$ tagit --link -f /folder/foo.zip -t tag1
$ ls -l /folder
foo.zip
foo._tags.tag1._tags.zip -> /folder/foo.zip
```

It also removes previous tagged forms of the files. The previously tagged symlink forms of the files are detected using globbing (example glob pattern: `foo._tags.*._tags.zip`) so any links named like the tagged files will be removed as well. Only links will be removed.
```
$ ls -l /folder
foo.zip
foo._tags.tag1._tags.zip -> /folder/foo.zip
$ tagit --link -f /folder/foo.zip -t tag2
$ ls -l /folder
foo.zip
foo._tags.tag1.tag2._tags.zip -> /folder/foo.zip
```
Notice that the filename being tagged *does not* change to the tagged form in the second call to `tagit`. If the tagged form is tagged it will not remove the tagged file being tagged.


## Cache File
The cache file is used to provide a pool of previously used tags to the bash-completion system. For this tool the purpose of bash-completion is to keep the tags consistent. Hitting `<tab>` twice after `-t` will show a list of all tags used while using the current cache file. Hitting `<tab>` twice after a partial tag after`-t` will show a list of all tags containing the partial tag used while using the current cache file. This also applies to `-r`. This differs from the usual tab completion behavior in that `tagit -f foo -t top<tab><tab>` will output both `top_hat` and `spinning_top` from a cache that includes both, instead of just `top_hat`. This helps highlight tags that are duplicate in meaning like `spin_left` and `left_spin`.

By default Tagit uses the cache file in the current working directory. This makes it easy to isolate the tag pools from different datasets just by being in the directory associated with the data. A different cache file can be specified with the `--cache` option.

Tagit can be prevented from creating or updating a cache file with the `--ro-cache` option.

The cache files are newline delimited lists of tags (one tag per line no extra formatting). To add/remove/modify a tag in a cache open it in a text editor, make the change, and save it.


# Install
Tagit can be used straight from the downloaded repository (master is always the latest stable version). Or you can install it system wide.
```
git clone https://github.com/haxwithaxe/tagit.git
cd tagit
make install
```
To install it for just your user run the `make` command like this:
```
PREFIX=$HOME/.local make install
```


# Development
Pull requests must be reasonably PEP-8 compliant and must include test coverage of any substantial changes.
