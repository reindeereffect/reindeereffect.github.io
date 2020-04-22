all: generated
	emacs --script default.el --eval '(org-publish-all)'

force: generated
	emacs --script default.el --eval '(org-publish-all t)'

generated: tags index

tags:
	bin/tags . > tags.org
	bin/sort-entries tags.org

index:
	bin/index . > index.org
