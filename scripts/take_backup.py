import datetime
import dropbox
import os
import sys
import subprocess

# add root directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from config.config import Config

# script take backup, saves in dumps directory, and uploads to dropbox
if __name__=='__main__':
    try:
        config = Config()
        
        backups_directory = config.get_environment_backups_directory()
        db_name = config.get_db_name()
        db_user = config.get_db_user()
        db_password = config.get_db_password()
        auth_db_name = config.get_auth_db_name()

        os.chdir(backups_directory)
        subprocess.check_call(['sudo',
                               'mongodump',
                               '-d', db_name,
                               '-u', db_user,
                               '-p', db_password,
                               '--authenticationDatabase', auth_db_name])
        backup_name = datetime.date.today().isoformat() + '.zip'
        subprocess.check_call(['sudo',
                               'zip',
                               '-r', backup_name,
                               'dump/'])
        subprocess.check_call(['sudo', 'rm', '-r', 'dump/'])

        # upload to dropbox
        access_token = config.get_dropbox_access_token()

        client = dropbox.client.DropboxClient(access_token)
        client.put_file(backup_name, open(backup_name, 'rb'), overwrite=True)

    except Exception as e:
        print 'Error taking backup'
        print e
