import pymysql

conn=pymysql.connect(host='localhost',user='capstone',password='capstone',db='capstone_db',charset='utf8',autocommit=True)
curs=conn.cursor()

#sql=""
#curs.execute(sql)
#conn.commit()
#conn.close()
