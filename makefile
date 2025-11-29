venv:
	uv venv

install:
	uv pip install --upgrade pip
	uv pip install -r requirements.txt

run:
	uv run main.py

build:
	uv pip install build
	uv build

ifeq ($(OS),Windows_NT)
clean:
	rmdir /s /q dist
	rmdir /s /q build
	del /q *.spec
else
clean:
	rm -rf build
	rm -rf dist
	rm -f *.spec
endif

package:
	uv run pyinstaller --noconsole --name "AppLauncher" --icon=icons/icon.ico main.py