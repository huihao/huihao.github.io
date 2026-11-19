SHELL := /bin/bash
PY ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: help init check test lint run daemon status logs clean backup

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

init: ## 初始化项目结构与示例配置
	$(PY) -m gzh.cli init

check: ## 环境与配置体检
	$(PY) -m gzh.cli check

test: ## 运行全部测试
	$(PY) -m unittest discover -s tests -v

lint: ## 语法检查（无第三方依赖时可用）
	$(PY) -m compileall -q src tests

run: ## 前台运行调度器
	$(PY) -m gzh.cli run

daemon: ## 后台运行调度器
	$(PY) -m gzh.cli daemon

status: ## 查看运行状态
	$(PY) -m gzh.cli status

logs: ## 查看日志
	$(PY) -m gzh.cli logs --lines 50

backup: ## 备份配置与数据库
	./scripts/backup.sh

clean: ## 清理缓存与日志
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache
