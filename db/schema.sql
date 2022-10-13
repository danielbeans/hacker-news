DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS posts;

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  nickname TEXT
);

CREATE TABLE stories (
  id INT PRIMARY KEY ON CONFLICT IGNORE,
  title TEXT,
  score TEXT,
  time INT,
  author TEXT,
  url TEXT,
  
)