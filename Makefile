.PHONY: help demo dev backend frontend build

help:
	@echo "Available commands:"
	@echo "  make demo     - Start both backend and frontend concurrently"
	@echo "  make backend  - Start only the FastAPI backend"
	@echo "  make frontend - Start only the Next.js frontend"
	@echo "  make build    - Build the Next.js production bundle"

demo:
	pnpm run demo

dev: demo

backend:
	pnpm run backend

frontend:
	pnpm run dev

build:
	pnpm run build
