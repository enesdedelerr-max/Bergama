# Sprint 1 — Infrastructure foundation gate
# Requires helm on PATH (recommended: $HOME/.local/bin/helm).

export PATH := $(HOME)/.local/bin:$(PATH)
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT := $(abspath .)
SCRIPTS := $(ROOT)/infra/scripts

.PHONY: help helm-lint helm-template full-check verify-locks validate-secrets backup restore-smoke platform-validate build-release gate-sprint1

help:
	@echo "Sprint 1 targets:"
	@echo "  make helm-lint"
	@echo "  make helm-template"
	@echo "  make full-check"
	@echo "  make verify-locks"
	@echo "  make validate-secrets"
	@echo "  make backup"
	@echo "  make restore-smoke"
	@echo "  make platform-validate"
	@echo "  make build-release"
	@echo "  make gate-sprint1"

helm-lint:
	@bash "$(SCRIPTS)/helm-lint.sh"

helm-template:
	@bash "$(SCRIPTS)/helm-template.sh"

full-check:
	@bash "$(SCRIPTS)/full-check.sh"

verify-locks:
	@bash "$(SCRIPTS)/verify-locks.sh"

validate-secrets:
	@bash "$(SCRIPTS)/validate-secrets.sh"

backup:
	@bash "$(SCRIPTS)/backup.sh"

restore-smoke:
	@bash "$(SCRIPTS)/restore-smoke.sh"

platform-validate:
	@bash "$(SCRIPTS)/platform-validate.sh"

build-release:
	@bash "$(SCRIPTS)/build-release.sh"

gate-sprint1:
	@bash "$(SCRIPTS)/gate-sprint1.sh"
