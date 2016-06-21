cd /home/deploy/dumps
sudo mongodump -d garpr -u mongo -p mong0 --authenticationDatabase admin
sudo zip -r `date "+%Y-%m-%d"`.zip dump/
sudo rm -r dump/
