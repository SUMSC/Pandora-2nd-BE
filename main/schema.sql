DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS test;

CREATE TABLE user
(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(10) UNIQUE NOT NULL,
    id_tag   VARCHAR(20) UNIQUE NOT NULL,
    repo     TEXT UNIQUE
);

CREATE TABLE test
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER   NOT NULL,
    test_time   TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
    test_status TEXT      NOT NULL,
    test_grade  INTEGER   NOT NULL,
    error_log   TEXT      NOT NULL,
    repo        TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id)
);