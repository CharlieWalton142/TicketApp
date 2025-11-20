from db import init_db, create_user, init_user_db
init_db()
init_user_db()
create_user("alice", "S3curePass!", "admin")
create_user("bob", "hunter2", "user")
create_user("admin", "ChangeMe123!", "admin")
create_user("tester", "test123", "user")
exit()
