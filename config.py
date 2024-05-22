import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('MYSQL_URL', 'mysql+pymysql://bibliotec:bibliotec@localhost/bibliotec_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
"""
Criar o usuario

CREATE USER 'bibliotec'@'%' IDENTIFIED BY 'bibliotec';
SET PASSWORD FOR 'bibliotec'@'%' = PASSWORD('bibliotec');
GRANT Create user ON *.* TO 'bibliotec'@'%';
GRANT Event ON *.* TO 'bibliotec'@'%';
GRANT File ON *.* TO 'bibliotec'@'%';
GRANT Process ON *.* TO 'bibliotec'@'%';
GRANT Reload ON *.* TO 'bibliotec'@'%';
GRANT Replication client ON *.* TO 'bibliotec'@'%';
GRANT Replication slave ON *.* TO 'bibliotec'@'%';
GRANT Show databases ON *.* TO 'bibliotec'@'%';
GRANT Shutdown ON *.* TO 'bibliotec'@'%';
GRANT Super ON *.* TO 'bibliotec'@'%';
GRANT Create tablespace ON *.* TO 'bibliotec'@'%';
GRANT Usage ON *.* TO 'bibliotec'@'%';
GRANT Grant option ON *.* TO 'bibliotec'@'%';

Criar banco
CREATE DATABASE `bibliotec_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;


GRANT Alter routine ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Create routine ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Create temporary tables ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Execute ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Lock tables ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Grant option ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Alter ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Create ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Create view ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Delete ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Delete history ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Drop ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Grant option ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Index ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Insert ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT References ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Select ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Show view ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Trigger ON bibliotec_db.* TO 'bibliotec'@'%';
GRANT Update ON bibliotec_db.* TO 'bibliotec'@'%';
"""