@echo off
call C:\Anaconda\Scripts\activate.bat ml_env >nul 2>&1
F:
cd "F:\courses\Machine Learning"
jupyter notebook
