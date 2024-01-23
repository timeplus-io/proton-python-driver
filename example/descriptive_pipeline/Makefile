VERSION = $(shell git rev-parse --short HEAD)
BIN_NAME = proton-pipeline-service
IMAGE_NAME = $(BIN_NAME):$(VERSION)
DOCKER_ID_USER = timeplus
FULLNAME=$(DOCKER_ID_USER)/${IMAGE_NAME}

.PHONY: service

service:
	uvicorn server.main:app --port 5001 --host 0.0.0.0 --reload

proton:
	docker run -d -p 8463:8463 --pull always --name proton ghcr.io/timeplus-io/proton:latest

docker: Dockerfile
	docker build -t $(IMAGE_NAME) .

docker_run: 
	docker run -p 5001:5001  $(IMAGE_NAME)

push:
	docker tag $(IMAGE_NAME) $(FULLNAME)
	docker push $(FULLNAME)