import os
from pathlib import Path
from subprocess import call

import DTGBot
from DTGBot import frontend
from importlib import resources

from DTGBot.common.dtg_config import dtg_sett

sett = dtg_sett()
fe_path = sett.frontend_dir
# base_path = Path(__file__).resolve().parent.parent / 'src' / 'DTGBot' / 'frontend'
os.chdir(fe_path)

command = 'browser-sync start --proxy "localhost:8000" --files "templates/*.html, static/*.css"'
call(command, shell=True)
