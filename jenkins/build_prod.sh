cd /home/deploy/prod/garpr
sudo systemctl stop prod.webapp.service
sudo systemctl stop prod.api.service
sudo git pull
sudo systemctl start prod.api.service
sudo systemctl start prod.webapp.service
