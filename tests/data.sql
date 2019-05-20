INSERT INTO user (username, id_tag, repo)
VALUES ("aaa", "111", "aaa/test"),
       ("bbb", "222", "bbb/test"),
       ("ccc", "333", "ccc/test");

INSERT INTO test (user_id, test_status, error_log,test_grade)
VALUES ("1", "passed", "ok","100"),
       ("2", "passed", "ok","100"),
       ("3", "failure", "error","24");