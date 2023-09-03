@echo off
python -m nuitka --onefile --include-data-file=favicon.ico=favicon.ico --windows-icon-from-ico=favicon.ico --enable-plugin=tk-inter main.py
explorer /select,"main.exe"