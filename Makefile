PREFIX ?= /usr/local
COMPLETION_DIR ?= $(PREFIX)/share/bash-completion/completions

install: $(PREFIX)/bin/tagit $(COMPLETION_DIR)/tagit

uninstall:
	rm $(PREFIX)/bin/tagit $(COMPLETION_DIR)/tagit

$(PREFIX)/bin/tagit:
	cp tagit.py $(PREFIX)/bin/tagit

$(COMPLETION_DIR)/tagit: $(COMPLETION_DIR)
	cp tagit.completion $(COMPLETION_DIR)/tagit

$(COMPLETION_DIR):
	mkdir -p $(COMPLETION_DIR)
