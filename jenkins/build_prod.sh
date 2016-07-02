cd /home/deploy/prod/garpr
sudo bash ./twistd_stop.sh
git pull
sudo bash ./twistd_start.sh
