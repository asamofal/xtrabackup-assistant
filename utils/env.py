import psutil


def is_mysql_running():
    mysqld_processes = list(filter(lambda p: p.name() == 'mysqld', psutil.process_iter()))

    return len(mysqld_processes) > 0
