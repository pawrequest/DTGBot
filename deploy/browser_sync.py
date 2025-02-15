import os
from subprocess import call

from DTGBot.common.dtg_config import guru_config

os.chdir(guru_config().guru_frontend)
print(os.getcwd())

command = 'browser-sync start --proxy "localhost:8000" --files "templates/*/*.html, static/*/*.css"'
call(command, shell=True)
