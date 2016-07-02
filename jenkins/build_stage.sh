cd /home/deploy/stage/garpr
sudo bash twistd_stop.sh
git pull
sudo pip install -r requirements.txt
nosetests -v
sudo bash twistd_start.sh
