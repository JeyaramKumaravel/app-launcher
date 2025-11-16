PYTHON = python

install:

	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py

build:
	$(PYTHON) -m pip install build
	$(PYTHON) -m build

ifeq ($(OS),Windows_NT)
clean:
	rmdir /s /q build dist
	del /q *.spec
else
clean:
	rm -rf build dist
	rm -f *.spec
endif

package:
	pyinstaller --noconsole --name "AppLauncher" --icon=icons/icon.ico main.py