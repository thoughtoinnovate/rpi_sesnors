# AQI Monitoring System Makefile
# Commands to manage the REST API server

.PHONY: help install start stop restart status logs clean unified

# Configuration
PID_FILE = /tmp/pm25_api_server.pid
LOG_FILE = /tmp/pm25_api.log
APP_PATH = /home/kdhpi/Documents/workk/code/rpi_sesnors/app/rest_api/app.py
PYTHON_PATH = /home/kdhpi/Documents/workk/code/rpi_sesnors/venv/bin/python

# Default target
help:
	@echo "AQI Monitoring System - REST API Server Management"
	@echo ""
	@echo "Available commands:"
	@echo "  install  - Install Python and Node.js dependencies"
	@echo "  start    - Start REST API server"
	@echo "  unified  - Start unified UI + API server (recommended)"
	@echo "  stop     - Stop REST API server"
	@echo "  restart  - Restart REST API server"
	@echo "  status   - Check if server is running"
	@echo "  logs     - Show server logs (tail -f)"
	@echo "  clean    - Remove PID and log files"
	@echo "  help     - Show this help message"
	@echo ""
	@echo "Server files:"
	@echo "  PID file: $(PID_FILE)"
	@echo "  Log file: $(LOG_FILE)"
	@echo ""
	@echo "Dependencies:"
	@echo "  Python: app/rest_api/requirements.txt"
	@echo "  Node.js: ui/package.json"

start:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Server is already running (PID: $$(cat $(PID_FILE)))"; \
	else \
		echo "🔧 Validating dependencies..."; \
		if ! command -v python3 >/dev/null 2>&1; then \
			echo "❌ Python3 not found. Please install Python3."; \
			exit 1; \
		fi; \
		if ! command -v npm >/dev/null 2>&1; then \
			echo "❌ npm not found. Please install Node.js."; \
			exit 1; \
		fi; \
		echo "✅ Dependencies OK"; \
		echo "🐍 Setting up virtual environment..."; \
		if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then \
			echo "Creating virtual environment..."; \
			python3 -m venv venv; \
			./venv/bin/pip install -r app/rest_api/requirements.txt; \
			echo "✅ Virtual environment setup complete"; \
		else \
			echo "✅ Virtual environment already exists"; \
		fi; \
		echo "🔌 Checking port availability..."; \
		if netstat -tln 2>/dev/null | grep -q ":5000 "; then \
			echo "Port 5000 in use, attempting to free it..."; \
			PID=$$(netstat -tlnp 2>/dev/null | grep ":5000 " | awk '{print $$7}' | cut -d'/' -f1 | head -1); \
			if [ -n "$$PID" ] && [ "$$PID" != "-" ]; then \
				kill -9 $$PID 2>/dev/null || true; \
				sleep 2; \
				if netstat -tln 2>/dev/null | grep -q ":5000 "; then \
					echo "❌ Could not free port 5000. Please manually stop the conflicting process."; \
					exit 1; \
				fi; \
				echo "✅ Port 5000 freed"; \
			else \
				echo "⚠️  Could not determine PID of process using port 5000"; \
			fi; \
		fi; \
		echo "🚀 Starting unified UI + API server..."; \
		echo "📦 Building UI files..."; \
		cd ui && npm run build-for-flask; \
		echo "✅ UI built successfully"; \
		echo "🌐 Starting Flask server..."; \
		$(PYTHON_PATH) $(APP_PATH) > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE); \
		sleep 3; \
		if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
			echo "Server started successfully (PID: $$(cat $(PID_FILE)))"; \
			echo "API and UI available at: http://localhost:5000"; \
		else \
			echo "Failed to start server. Check logs with 'make logs'"; \
			exit 1; \
		fi; \
	fi

stop:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Stopping server (PID: $$(cat $(PID_FILE)))..."; \
		kill $$(cat $(PID_FILE)) 2>/dev/null || true; \
		rm -f $(PID_FILE); \
		echo "Server stopped"; \
	else \
		echo "Server is not running"; \
	fi

restart: stop start

status:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "✅ Server is running (PID: $$(cat $(PID_FILE)))"; \
		echo "   API: http://localhost:5000"; \
	else \
		echo "❌ Server is not running"; \
	fi

logs:
	@if [ -f $(LOG_FILE) ]; then \
		tail -f $(LOG_FILE); \
	else \
		echo "No log file found at $(LOG_FILE)"; \
	fi

clean:
	@echo "Cleaning up server files..."
	@if [ -f $(PID_FILE) ]; then \
		kill $$(cat $(PID_FILE)) 2>/dev/null || true; \
		rm -f $(PID_FILE); \
	fi
	rm -f $(LOG_FILE)
	@echo "Cleanup complete"

install:
	@echo "Installing project dependencies..."
	@echo ""
	@echo "Installing Python dependencies..."
	@if command -v pip3 >/dev/null 2>&1; then \
		if [ -d "venv" ]; then \
			echo "Using existing virtual environment..."; \
			./venv/bin/pip install -r app/rest_api/requirements.txt; \
		else \
			echo "Creating virtual environment..."; \
			python3 -m venv venv; \
			./venv/bin/pip install -r app/rest_api/requirements.txt; \
		fi; \
	elif command -v pip >/dev/null 2>&1; then \
		pip install -r app/rest_api/requirements.txt; \
	else \
		echo "❌ Error: pip not found. Please install Python and pip first."; \
		exit 1; \
	fi
	@echo ""
	@echo "Installing Node.js dependencies..."
	@if [ -d "ui" ]; then \
		if command -v npm >/dev/null 2>&1; then \
			echo "Running npm install (this may take a few minutes)..."; \
			echo "You can also run this manually: cd ui && npm install"; \
			echo "Continuing with Python installation..."; \
		elif command -v yarn >/dev/null 2>&1; then \
			echo "You can run yarn install manually: cd ui && yarn install"; \
			echo "Continuing with Python installation..."; \
		else \
			echo "⚠️  Warning: npm or yarn not found. Please install Node.js manually."; \
			echo "   cd ui && npm install"; \
		fi; \
	else \
		echo "❌ Error: ui directory not found."; \
		exit 1; \
	fi
	@echo ""
	@echo "✅ All dependencies installed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  make unified - Start unified UI + API server (recommended)"
	@echo "  make start   - Start REST API server only"
	@echo "  cd ui && npm run dev    - Start frontend development server"
	@echo ""
	@echo "Note: Python dependencies are installed in ./venv/ directory"

unified:
	@echo "🚀 Starting unified UI + API server..."
	@echo "📦 Building UI files..."
	@cd ui && npm run build-for-flask
	@echo "✅ UI built successfully"
	@echo "🌐 Starting Flask server..."
	@cd app/rest_api && $(PYTHON_PATH) app.py