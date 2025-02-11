APP_NAME := $(shell python metadata.py name)
APP_VERSION := $(shell python metadata.py version)
IMAGE_NAME := demsking/$(APP_NAME)

# Start the development environment using tmuxinator
shell:
	tmuxinator

stop:
	tmux kill-session -t oremi-forecast

install:
	poetry install

gen-tests:
	dotenv -- python gen.py
	pre-commit run double-quote-string-fixer

test: gen-tests
	pytest -vv

coverage: gen-tests
	pytest --cov=server

coverage-html: gen-tests
	pytest --cov=server --cov-report=html

lint:
	pre-commit run --all-files

fix:
	ruff check . --fix

# Show outdated dependencies using poetry
outdated:
	poetry show --outdated

update:
	poetry -C python update
	devbox update
	pre-commit autoupdate

clean:
	rm -rf dist/

#
## Packaging
build/context:
	docker buildx create --name $(APP_NAME) --bootstrap
	mkdir -p build/
	touch $@

image: build/context
	docker buildx use $(APP_NAME)
	docker buildx build . \
	  --platform linux/amd64,linux/arm64 \
	  --push \
	  --progress plain \
	  --tag $(IMAGE_NAME):$(APP_VERSION) \
	  --tag $(IMAGE_NAME):latest \
	  --build-arg APP_NAME=$(APP_NAME) \
	  --build-arg APP_VERSION=$(APP_VERSION) \
	  --label "org.opencontainers.image.title=$(APP_NAME)" \
	  --label "org.opencontainers.image.description=$(shell python metadata.py description)" \
	  --label "org.opencontainers.image.version=$(APP_VERSION)" \
	  --label "org.opencontainers.image.revision=$(shell git rev-parse HEAD)" \
	  --label "org.opencontainers.image.authors=$(shell python metadata.py authors)" \
	  --label "org.opencontainers.image.created=$(shell date --rfc-3339=seconds)" \
	  --label "org.opencontainers.image.source=$(shell python metadata.py repository)" \
	  --label "org.opencontainers.image.url=$(shell python metadata.py repository)" \
	  --label "org.opencontainers.image.documentation=$(shell python metadata.py documentation)" \
	  --label "org.opencontainers.image.vendor=Sébastien Demanou" \
	  --label "org.opencontainers.image.licenses=$(shell python metadata.py license)"

image-test:
	docker build --debug . \
	  --progress plain \
	  --tag $(IMAGE_NAME):test \
	  --build-arg APP_NAME=$(APP_NAME) \
	  --build-arg APP_VERSION=$(APP_VERSION)

testserver: image-test
	docker run -it --rm -v /tmp/data:/data -p 11111:1111 -e WORKER=1 $(IMAGE_NAME)

publish: image-test
	git commit pyproject.toml -m "Release $(APP_VERSION)"
	$(MAKE) image
	git tag v$(APP_VERSION)
	git push --tags origin main
