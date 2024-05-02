import os
from pathlib import Path
from subprocess import call

base_path = Path(__file__).resolve().parent.parent / 'src' / 'DTGBot' / 'frontend'
os.chdir(base_path)

command = 'browser-sync start --proxy "localhost:8000" --files "templates/*.html, static/*.css"'
call(command, shell=True)
