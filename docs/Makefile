MKDOCS := mkdocs

build:
	$(MKDOCS) build

serve:
	$(MKDOCS) serve

deploy:
	$(MKDOCS) gh-deploy

clean:
	rm -rf site

new:
	$(MKDOCS) new .

.PHONY: build serve deploy clean new
