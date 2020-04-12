# hangouts_takeout_to_backupandrestore
Easily migrate your Hangouts texts to any Android messaging app with [jsontoxml.py](jsontoxml.py)!

The below steps will walk you through [exporting your Project Fi text messages on Hangouts](https://takeout.google.com), converting them to [XML](https://synctech.com.au/sms-backup-restore/fields-in-xml-backup-files/), and importing them into your messaging app of choice with [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore).

# Sensitive Data Warning
>If you are not familiar with analyzing code, I urge you to have this reviewed by someone that is. While you should do that for any software not downloaded directly from trusted entities, it is especially true for your private text messaging conversations. This makes no web calls but it is always best to err on the side of caution and have someone you trust ensure the safety of your data.

# Instructions
1. Go to takeout.google.com, select Hangouts, and proceed to _Create export_
2. Ensure you have Python 3.6+ installed (try [pyenv](https://realpython.com/intro-to-pyenv/) for easy Python versioning)
3. Download [jsontoxml.py](jsontoxml.py)
4. Once the export from Step 1 is ready, download the archive from your email and extract **Hangouts.json** to the same folder as [jsontoxml.py](jsontoxml.py)
5. Navigate to the above folder using the command-line's [cd](https://en.wikipedia.org/wiki/Cd_(command)#Usage)
6. Run `python3 jsontoxml.py`
7. If sucessful, your folder should now contain **Hangouts.xml**
8. Download [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) on your Android phone
9. Copy **Hangouts.xml** to your phone using your application of choice (e.g., Google Drive)
10. Move **Hangouts.xml** to your phone's _SMSBackupRestore_ folder with your File Manager of choice (e.g., [Astro](https://play.google.com/store/apps/details?id=com.metago.astro))
11. Launch _SMS Backup & Restore_ and click _Restore_ from the menu
12. Click _SELECT ANOTHER BACKUP_ under _Messages_ and select **Hangouts.xml**
13. Turn off the Phone Calls import and click _Restore_

# Contributing
Install [pre-commit](https://pre-commit.com/) to utilize [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks), ensuring [proper style](https://www.python.org/dev/peps/pep-0008/) before each commit
```console
$ pip3 install pre-commit
$ pre-commit install
```


[comment]: <> I highly reccommend using venvs when working with python - I really like miniconda https://docs.conda.io/en/latest/miniconda.html

```
conda create -n hangouts python=3.7
source activate hangouts
pip install -r requirements.txt
pre-commit install
```

# Features
- [x] Convert SMS messages
- [x] Convert MMS group messages
- [x] Embed link to MMS image
- [x] Embed transcript of voicemail
- [x] Embed link to dropped pin
- [ ] Create feature toggles
- [ ] Link to voicemail audio
- [ ] Embed attachments directly (i.e., without a link)
- [ ] Convert native Hangouts conversations
