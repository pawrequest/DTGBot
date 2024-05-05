import os
from subprocess import call

from DTGBot.common.dtg_config import dtg_sett

os.chdir(dtg_sett().frontend_dir)

command = 'browser-sync start --proxy "localhost:8000" --files "templates/*/*.html, static/*/*.css"'
call(command, shell=True)
