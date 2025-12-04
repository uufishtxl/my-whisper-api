import sqlite3
import datetime

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME) # 创建数据库连接
    c = conn.cursor() # 创建游标，游标负责执行 SQL 语句，之前使用的 sqlalchemy 底层也有 Cursor，只是封装了，使用起来更方便
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  status TEXT,
                  result TEXT,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def create_task(filename):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    created_at = datetime.datetime.now()
    # (?， ?, ?) 表示占位符，一一对应于后面的参数
    c.execute("INSERT INTO tasks (filename, status, created_at) VALUES (?, ?, ?)",
              (filename, "queued", created_at))
    task_id = c.lastrowid # 获取自增的 ID
    conn.commit()
    conn.close()
    return task_id

def get_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)) # c.execute 只是负责执行 SQL 语句，数据库找到记录后会将记录准备好，但是这时候数据还在数据库的内存里，并没有变成 Python 代码里的变量
    row = c.fetchone() # c.fetchone() 会将记录转换成 Python 代码里的变量
    conn.close()
    if row:
        return dict(row)
    return None

def update_task_status(task_id, status, result=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if result is not None:
        c.execute("UPDATE tasks SET status=?, result=? WHERE id=?", (status, result, task_id))
    else:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()
    conn.close()
