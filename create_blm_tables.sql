-- Create tables for Black Men Read database
-- ERD at https://miro.com/app/board/o9J_l4VnWWE=/

CREATE TABLE IF NOT EXISTS bmr_issue (
  id INTEGER NOT NULL AUTO_INCREMENT, -- Use ISBN or gcd_id instead?
  gcd_id TINYTEXT NOT NULL,
  gcd_series_id INTEGER,
  gb_id TINYTEXT NOT NULL,
  title TEXT NOT NULL,
  subtitle TEXT,
  description LONGTEXT,
  snippet TEXT,
  publisher TEXT,
  published_date DATE,
  language TINYTEXT,
  isbn TINYTEXT,
  page_count INTEGER,
  thumbnail_url TEXT,
  cover_url TEXT,
  last_updated DATETIME,
  mature TINYINT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS bmr_genre (
  id INTEGER NOT NULL AUTO_INCREMENT,
  name TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS bmr_creator (
  id INTEGER NOT NULL AUTO_INCREMENT,
  name TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS bmr_creator_role (
  id INTEGER NOT NULL AUTO_INCREMENT,
  role TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS bmr_issues_creators (
  issue_id INTEGER NOT NULL,
  creator_id INTEGER NOT NULL,
  role INTEGER NOT NULL,
  FOREIGN KEY (issue_id) REFERENCES bmr_issue(id),
  FOREIGN KEY (creator_id) REFERENCES bmr_creator(id)
);

CREATE TABLE IF NOT EXISTS bmr_issues_genres (
  issue_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  FOREIGN KEY (issue_id) REFERENCES bmr_issue(id),
  FOREIGN KEY (genre_id) REFERENCES bmr_genre(id)
);