rm -rf /var/www/*
mkdir /var/www/api
mkdir /var/www/webapp
cp -r webapp/* /var/www/webapp/*
cp garpr.wsgi /var/www/api
