sudo rm -rf /var/www/*
sudo mkdir /var/www/api
sudo cp -r webapp /var/www
sudo cp garpr.wsgi /var/www/api
sudo /etc/init.d/apache2 restart
