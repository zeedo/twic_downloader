#! /bin/bash    
cd /home/barrie/Dropbox/src/twic_downloader/.venv
source bin/activate
cd ..
# virtualenv is now active, which means your PATH has been modified.
# Don't try to run python from /usr/bin/python, just run "python" and
# let the PATH figure out which version to run (based on what your
# virtualenv has configured).

python twic_downloader.py