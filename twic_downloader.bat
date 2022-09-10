set original_dir=%CD%
set venv_root_dir=C:\Users\Barrie\Dropbox\src\twic_downloader\.venv
cd %venv_root_dir%
call %venv_root_dir%\Scripts\activate.bat
cd ..
python twic_downloader.py

call %venv_root_dir%\Scripts\deactivate.bat
cd %original_dir%
exit /B 1

twic_downloader.bat