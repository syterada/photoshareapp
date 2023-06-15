CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users(
	u_id INTEGER AUTO_INCREMENT,
    email VARCHAR(20) NOT NULL UNIQUE,
    hometown VARCHAR(20),
    f_name VARCHAR(20) NOT NULL,
    gender VARCHAR(20),
    l_name VARCHAR(20) NOT NULL,
    dob DATE NOT NULL,
    psword VARCHAR(20) NOT NULL,
    PRIMARY KEY (u_id));
    
CREATE TABLE Albums(
	a_id INTEGER AUTO_INCREMENT,
    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    album_name VARCHAR(20) NOT NULL,
    userid INTEGER NOT NULL,
    PRIMARY KEY (a_id),
    FOREIGN KEY (userid) REFERENCES Users(u_id) ON DELETE CASCADE);
    
CREATE TABLE Pictures(
	photo_id INTEGER AUTO_INCREMENT,
    caption VARCHAR(50),
    p_data LONGBLOB,
    a_id INTEGER NOT NULL,
    u_id INTEGER NOT NULL,
    PRIMARY KEY (photo_id),
    FOREIGN KEY (a_id) REFERENCES Albums(a_id) ON DELETE CASCADE,
    FOREIGN KEY (u_id) REFERENCES Users(u_id) ON DELETE CASCADE);
    
CREATE TABLE Tags(
  tag_id INTEGER AUTO_INCREMENT,
	descript VARCHAR(20),
    constraint check_lowercase check (lower(descript) = descript),
    PRIMARY KEY (tag_id));

CREATE TABLE Tagged(
  photo_id INT,
  tags_id INT,
  PRIMARY KEY (photo_id, tags_id),
  FOREIGN KEY (photo_id) REFERENCES Pictures(photo_id) ON DELETE CASCADE,
  FOREIGN KEY (tags_id) REFERENCES Tags(tag_id));
    
CREATE TABLE Comments(
	c_id INTEGER AUTO_INCREMENT,
    c_owner INTEGER NOT NULL,
    contents TEXT NOT NULL,
    photo_id INTEGER NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (c_owner) REFERENCES Users(u_id) ON DELETE CASCADE,
    FOREIGN KEY (photo_id) REFERENCES Pictures(photo_id) ON DELETE CASCADE,
    PRIMARY KEY (c_id));
    
CREATE TABLE Friends(
	a_uid INTEGER,
    b_uid INTEGER,
    CHECK (a_uid <> b_uid),
    PRIMARY KEY (a_uid, b_uid),
    FOREIGN KEY (a_uid) REFERENCES Users(u_id) ON DELETE CASCADE,
    FOREIGN KEY (b_uid) REFERENCES Users(u_id) ON DELETE CASCADE);
    
CREATE TABLE Likes(
	photo_id INTEGER,
    u_id INTEGER,
    PRIMARY KEY (u_id, photo_id),
    FOREIGN KEY (u_id) REFERENCES Users(u_id) ON DELETE CASCADE,
    FOREIGN KEY (photo_id) REFERENCES Pictures(photo_id) ON DELETE CASCADE);

