C:\Users\maxli\anaconda3\envs\spotify\python.exe D:\Projects\spotify-data\download_functions.py
git config user.name "Automated"
git config user.email "actions@users.noreply.github.com"
git add -A
git commit -m "Latest data: %date%%time%" || exit 0
git push
