DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS top_stories;
DROP TABLE IF EXISTS new_stories;

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  nickname TEXT
);

CREATE TABLE top_stories (
  id INT PRIMARY KEY ON CONFLICT IGNORE,
  title TEXT,
  score INTEGER,
  time INTEGER,
  author TEXT,
  url TEXT
);

CREATE TABLE new_stories (
  id INT PRIMARY KEY ON CONFLICT IGNORE,
  title TEXT,
  score INTEGER,
  time INTEGER,
  author TEXT,
  url TEXT
);