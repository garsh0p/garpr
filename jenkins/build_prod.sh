cd /home/deploy/prod/garpr
sudo stop prod-webapp
sudo stop prod-api
sudo git pull
sudo start prod-api
sudo start prod-webapp
