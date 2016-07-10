cd /home/deploy/stage/garpr
sudo stop stage-webapp
sudo stop stage-api
sudo git checkout master
sudo git pull
sudo git checkout $text
sudo pip install -r requirements.txt
sudo nose2 -v -B
sudo start stage-api
sudo start stage-webapp
