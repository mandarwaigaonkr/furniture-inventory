@echo off
echo Setting up Vercel deployment...

REM Create api folder
mkdir api 2>nul

REM Create api/index.py
echo from app import app > api\index.py

REM Create requirements.txt
echo Flask> requirements.txt
echo gunicorn>> requirements.txt

REM Create vercel.json
echo {> vercel.json
echo   "builds": [>> vercel.json
echo     {>> vercel.json
echo       "src": "api/index.py",>> vercel.json
echo       "use": "@vercel/python">> vercel.json
echo     }>> vercel.json
echo   ],>> vercel.json
echo   "routes": [>> vercel.json
echo     {>> vercel.json
echo       "src": "/(.*)",>> vercel.json
echo       "dest": "api/index.py">> vercel.json
echo     }>> vercel.json
echo   ]>> vercel.json
echo }>> vercel.json

REM Create .gitignore
echo __pycache__/ > .gitignore
echo *.pyc >> .gitignore
echo venv/ >> .gitignore
echo .env >> .gitignore
echo instance/ >> .gitignore
echo *.db >> .gitignore

REM Git add commit push
git add .
git commit -m "Vercel setup"
git push

echo Done. Your project is now Vercel ready.
pause
