# xtrabackup-assistant
Assistant for Percona XtraBackup - tool automates the process of create and restoring your backups.

#### Key features
- Simple use: only a few commands `create`, `restore`, `rotate`
- Fully automated processes
- Display progress bars where possible _(especially handy for large backups)_
- Ability to work with remote storage _(via SFTP)_

#### Requirements
Python 3.9 or newer is required.

#### Config
- `project_name` _(required)_ - the name of a project. It's used in backup file names and Slack notifications
- `xtrabcakup` _(required)_:
  - `xtrabcakup.user` - the MySQL username used when connecting to the server _(required for creating a backup)_
  - `xtrabcakup.password` - the password to use when connecting to the database _(required for creating a backup)_
  - `xtrabcakup.parallel` - the number of threads to use to copy multiple data files concurrently when creating/restoring a backup
- `sftp` _(optional)_ - if set can be used to work with remote SFTP storage _(upload backups, download during restore, rotate backups there)_
  - `host` - the hostname or IP of the SFTP server
  - `user` - the SFTP username 
  - `password` - the SFTP user password
  - `path` - the path on the SFTP storage. It's used for uploading backups, searching available backups for restore and for `rotate` command
- `slack` _(optional)_ - if set Slack message will be sent in a case of failed backup creation
  - `token` - the access API token, the key to the Slack platform
  - `channel` - the name of Slack channel to which notifications will be sent
- `rotation` _(optional)_ - backups rotation settings
  - `max_store_time_years` - how many years backups will be stored on the SFTP storage
  - `keep_for_last_days` - backups created for this N last days will be excluded from rotation

#### Usage
1. Create config
2. Run one of the available commands: `create` _(`--upload` available here)_, `restore`, `rotate`

Example:
```bash
python xtrabackup-assistant/main.py create --upload
```
