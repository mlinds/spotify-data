C:\Users\maxli\anaconda3\envs\spotify\python.exe D:\Projects\spotify-data\download_functions.py
git config --worktree user.name "Automated"
git config --worktree user.email "actions@users.noreply.github.com"
git add -A
git commit -m "Latest data: %date% %time%" || exit 0
git push
@REM git config user.name "mlinds"
@REM git config user.email "max.lindsay95@gmail.com"
@REM git push