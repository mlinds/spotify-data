C:\Users\maxli\anaconda3\envs\spotify\python.exe D:\Projects\spotify-data\download_functions.py
git config user.name "Automated"
git config user.email "actions@users.noreply.github.com"
git add .\data_out\*
git commit -m "Latest data: %date% %time%" || exit 0
git push
git config user.name "mlinds"
git config user.email "max.lindsay95@gmail.com"
git push