# mysqlhelper.py
# MySQL数据库操作封装类,提供简洁的数据库交互接口
# 通用的MySQL操作类,支持连接、查询、插入、更新、删除等操作

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Tuple, Optional, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MySQLHelper:
    def begin_transaction(self) -> bool:
        # 开始事务(关闭自动提交)
        self.connection.autocommit = False
        return True

    def commit(self) -> bool:
        # 提交事务
        self.connection.commit()
        self.connection.autocommit = True  # 恢复自动提交
        return True

    def rollback(self) -> bool:
        # 回滚事务
        self.connection.rollback()
        self.connection.autocommit = True
        return True
    """
    MySQL数据库操作封装类,提供简洁的数据库交互接口
    """
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306, charset: str = 'utf8mb4'):
        """
        初始化数据库连接参数
        
        :param host: 数据库主机地址
        :param user: 数据库用户名
        :param password: 数据库密码
        :param database: 数据库名称
        :param port: 数据库端口,默认3306
        :param charset: 字符集,默认utf8mb4
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset
        self.connection: Optional[mysql.connector.connection.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None

    def connect(self) -> bool:
        """
        建立数据库连接
        
        :return: 连接成功返回True,失败返回False
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset=self.charset
            )
            self.cursor = self.connection.cursor(dictionary=True)  # 返回字典格式结果
            logger.info(f"成功连接到数据库: {self.database}")
            return True
        except Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False

    def close(self) -> None:
        """
        关闭数据库连接
        """
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")

    def execute_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """
        执行查询SQL语句
        
        :param sql: 查询SQL语句,使用%s作为占位符
        :param params: SQL参数,元组形式,可选
        :return: 查询结果列表,每个元素为字典
        """
        result = []
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return result

            self.cursor.execute(sql, params or ())
            result = self.cursor.fetchall()
            logger.info(f"执行查询成功,返回{len(result)}条记录")
            return result
        except Error as e:
            logger.error(f"查询执行失败: {str(e)}, SQL: {sql}, Params: {params}")
            return result

    def execute_non_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        """
        执行非查询SQL语句(INSERT, UPDATE, DELETE等)
        
        :param sql: 非查询SQL语句,使用%s作为占位符
        :param params: SQL参数,元组形式,可选
        :return: 受影响的行数,失败返回-1
        """
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return -1

            self.cursor.execute(sql, params or ())
            self.connection.commit()
            affected_rows = self.cursor.rowcount
            logger.info(f"执行非查询成功,影响{affected_rows}行")
            return affected_rows
        except Error as e:
            logger.error(f"非查询执行失败: {str(e)}, SQL: {sql}, Params: {params}")
            if self.connection:
                self.connection.rollback()
            return -1

    def batch_execute(self, sql: str, params_list: List[Tuple[Any, ...]]) -> int:
        """
        批量执行SQL语句
        
        :param sql: SQL语句,使用%s作为占位符
        :param params_list: 参数列表,每个元素为一个元组
        :return: 受影响的总行数,失败返回-1
        """
        if not params_list:
            return 0

        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return -1

            self.cursor.executemany(sql, params_list)
            self.connection.commit()
            affected_rows = self.cursor.rowcount
            logger.info(f"批量执行成功,影响{affected_rows}行")
            return affected_rows
        except Error as e:
            logger.error(f"批量执行失败: {str(e)}, SQL: {sql}")
            if self.connection:
                self.connection.rollback()
            return -1

    def get_one(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
        """
        获取单条查询结果
        
        :param sql: 查询SQL语句
        :param params: SQL参数,元组形式,可选
        :return: 单条记录字典,无结果返回None
        """
        results = self.execute_query(sql, params)
        return results[0] if results else None

    def get_scalar(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Any:
        """
        获取单个值(第一行第一列)
        
        :param sql: 查询SQL语句
        :param params: SQL参数,元组形式,可选
        :return: 单个值,无结果返回None
        """
        result = self.get_one(sql, params)
        return next(iter(result.values())) if result else None

    def begin_transaction(self) -> bool:
        """
        开始事务
        
        :return: 成功返回True,失败返回False
        """
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return False
            self.connection.autocommit = False
            return True
        except Error as e:
            logger.error(f"开始事务失败: {str(e)}")
            return False

    def commit(self) -> bool:
        """
        提交事务
        
        :return: 成功返回True,失败返回False
        """
        try:
            if self.connection and self.connection.is_connected():
                self.connection.commit()
                self.connection.autocommit = True
                logger.info("事务提交成功")
                return True
            return False
        except Error as e:
            logger.error(f"事务提交失败: {str(e)}")
            return False

    def rollback(self) -> bool:
        """
        回滚事务
        
        :return: 成功返回True,失败返回False
        """
        try:
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
                self.connection.autocommit = True
                logger.info("事务回滚成功")
                return True
            return False
        except Error as e:
            logger.error(f"事务回滚失败: {str(e)}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 使用示例
def example_usage():
        # 配置数据库连接信息
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'your_password',  # 替换为你的密码
        'database': 'school', # 替换为你的数据库
        'port': 3306
    }

    # 创建数据库助手实例
    db_helper = MySQLHelper(**db_config)

    try:
        # 1. 创建学生表(如果不存在)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS students (
            student_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL,
            height DECIMAL(5,2)
        )
        """
        db_helper.execute_non_query(create_table_sql)
        print("学生表创建成功或已存在")

        # 2. 批量插入测试数据
        insert_sql = "INSERT INTO students (name, height) VALUES (%s, %s)"
        students = [
            ('张三', 1.75),
            ('李四', 1.82),
            ('王五', 1.68),
            ('赵六', 1.79),
            ('钱七', 1.65)
        ]
        affected = db_helper.batch_execute(insert_sql, students)
        print(f"批量插入成功,影响{affected}行")

        # 3. 查询所有学生
        print("\n所有学生信息:")
        select_all_sql = "SELECT * FROM students"
        all_students = db_helper.execute_query(select_all_sql)
        for student in all_students:
            print(f"ID: {student['student_id']}, 姓名: {student['name']}, 身高: {student['height']}m")

        # 4. 查询身高大于1.75米的学生
        print("\n身高大于1.75米的学生:")
        select_tall_sql = "SELECT name, height FROM students WHERE height > %s"
        tall_students = db_helper.execute_query(select_tall_sql, (1.75,))
        for student in tall_students:
            print(f"姓名: {student['name']}, 身高: {student['height']}m")

        # 5. 更新学生信息
        update_sql = "UPDATE students SET height = %s WHERE name = %s"
        affected = db_helper.execute_non_query(update_sql, (1.70, '王五'))
        print(f"\n更新成功,影响{affected}行")

        # 6. 删除学生信息
        delete_sql = "DELETE FROM students WHERE name = %s"
        affected = db_helper.execute_non_query(delete_sql, ('钱七',))
        print(f"删除成功,影响{affected}行")

        # 7. 使用事务
        print("\n使用事务插入两条记录:")
        try:
            db_helper.begin_transaction()
            db_helper.execute_non_query(insert_sql, ('孙八', 1.80))
            db_helper.execute_non_query(insert_sql, ('周九', 1.72))
            # 模拟错误
            # raise Exception("模拟事务失败")
            db_helper.commit()
            print("事务提交成功")
        except Exception as e:
            db_helper.rollback()
            print(f"事务回滚: {str(e)}")

    finally:
        # 关闭连接
        db_helper.close()

    # 使用上下文管理器示例
    print("\n使用上下文管理器查询学生:")
    with MySQLHelper(**db_config) as context_db:
        students = context_db.execute_query("SELECT name, height FROM students ORDER BY height DESC")
        for student in students:
            print(f"姓名: {student['name']}, 身高: {student['height']}m")


if __name__ == "__main__":
    # 运行示例
    # example_usage()
    pass
