frakkup-backup
==============

An incremental backup program for Linux

## About:
A simple and backup program written in Python that manages incremental backups, similar to "Time Machine" style backups.

## Requirements:
* Python 3: 

`sudo apt-get install python3`

* PyGObject (GTK3 Python bindings). On Ubuntu/Debian: 

`sudo apt-get install python3-gi`

## Installation:
**Option 1:** Extract the source, navigate to the directory that contains the setup file and run:

`sudo python3 ./setup.py install`

**Option 2:** Simply run python3 on frakkup.py. No other files are needed:

`python3 frakkup.py`

**Option 3:** If you want to use Pip or Virtualenv, make sure to use the Python 3 versions and (if using Virtualenv) include site-packages, so that PyGObject is available.

## Features:
* Uses Rsync
* Uses Gtk3 GUI bindings
* Backup instances are both incremental and timestamped in separate folders, allowing easy management of back up instances without taking up more space than necessary.
* Allows saving of configuration settings, for easy one click backup jobs.

## How to Use:
* Simply select a source directory and a destination directory and click "Run". 
* Optionally, add a name to the "backup job" field and click "Save". Then select the job and click "Run". This will make the settings available for future backups.
* You can add Rsync options, such as exclude statements, in the applicable field. See the Rsync manpage for more.
* A checkbox is provided to allow you to run with sudo. You will be prompted to enter your password upon running the backup. This option is necessary if there is any read/write permission issues, although this should be uncommon for most backup cases.
* A virtual terminal will pop up giving you a chance to cancel the job midway, or watch it finish successfully.
* You can delete configuration files by clicking the "Delete" button when a backup job is selected.
* All backups are time stamped in separate folders. However, it uses hard links to allow the backups to be incremental in nature. This means there is no redundancy in space, while still being easy to separate and manage backup instances. Every directory will look like it contains all of the files, but any common files are hard linked to the same inode.
* Generally, you will want to delete old back ups after some time. Simply select the time stamped folders that are outdated and delete them.

## How it Works:
This program uses Rsync to run the backup services. Rsync provides a method to set up a destination directory to hard link common files (existing and unchanged) between backup instances. This allows you to have separate timestamped directories for every backup instance, providing you access to the full directory structure and every file backed up, without wasting space. Only new or changed files will be copied and unchanged files will have new hardlinks established in the newly created backup instance.

The hard link is a very robust feature of the operating system and perfect for incremental backups. Unlike soft links, there is no master copy when dealing with multiple hard links. The OS does not distinguish between an original file and any subsequent hard links. In fact even the very first "original" file is simply a hard link to an inode, which is a data structure that contains the actual file content. As long as a hard link still exists to an inode, the data will be available. This means you can freely delete any extra backup instance. 

This program also uses a soft link. When the program runs a backup job, it will always create a soft link called "LatestBackup" to the backup just created. This soft link serves as a link to the directory used for hard linking purposes on the next backup. This is the most robust way that the program performs hard linking for backup purposes.

This program also has a Plan B which is used in the following cases:
* The user accidentally delete the "LatestBackup" soft link. 
* The user decides that the latest backup has undesired updates, and wants to roll back to a previous backup. The user would simply delete the latest backup. However, this will break the soft link to this now nonexisting directory.

In either of the above scenarios, this program will find that the soft link is either nonexistent or is broken, and will pattern match any existing backups, and point to the latest backup that it finds for hardlinking purposes. Any broken links will be automatically fixed upon the next successful backup.

Hardlinking is a very safe procedure. The worst thing that can happen when a wrong directory is used for hardlinking purposes is that it can't find any common files and backs up all the files to the destination directory. 

## Additional notes:
Logs and Configuration:
* Configuration and log file directories are saved in ~/.config/frakkup.
* Log files are generated automatically based on the backup job name. 
* If there is no backup job name (i.e. for on-the-fly backups), it will save to backup.txt.
* Log files can get quite large after repeated back ups. Simply delete them and they will be regenerated upon the next back up.

The following Rsync options are enabled by default:
* Archive mode. This load will copy recursively, while preserving permissions, modification times, group, and owner.
* Verbose with progress, adding information and status to the virtual terminal so you can watch progress.
* Performs whole file copies, without delta-transfer algorithm.
* File sizes in logs and terminal are in human readable format.
* does not cross filesystem boundaries, which means it will not attempt to traverse through mounted drives.
* Stats are included in the output, so you can see additional information upon completion, such as number of files transferred, etc.
* Uses the latest backup as a hard link when unchanged. See discussion above.
* Log file generated in ~/.config/frakkup/logs
