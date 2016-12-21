cd /home/deploy/stage/garpr
sudo systemctl stop stage.api.service
sudo systemctl stop stage.webapp.service
git checkout master
git pull
git checkout $branch
sudo pip install -r requirements.txt
nose2 -v -B
sudo systemctl start stage.api.service
sudo systemctl start stage.webapp.service
