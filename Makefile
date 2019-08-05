ifeq (,$(wildcard .env))
$(error "Please create the .env file first. Use .env.dist as baseline.")
endif

ifeq (, $(shell which npm))
$(error "NPM was not detected in $(PATH). Please install it first.")
endif

ifeq (, $(shell which pip3))
$(error "PIP3 was not detected in $(PATH). Please install it first.")
endif

include .env

bootstrap:
	npm install -g serverless
	npm install
	pip3 install -r requirements.txt

deploy:
	serverless deploy

