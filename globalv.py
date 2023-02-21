import datetime
import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def check(listname, type='day'):
    #检查是否过期
    ex = 0
    if(type == 'hour'):
        ex = str(datetime.datetime.now().hour)
    elif(type == 'day'):
        ex = str(datetime.datetime.today())

    if not (r.lindex(listname, 0)):
        #如果没有该列表
        r.lpush(listname, ex)

    if not (r.lindex(listname, 0) == ex):
        r.ltrim(listname, 0, 0)
        r.lset(listname, 0, ex)

        return True
    
    else:
        return False

def push(target, listname, timetype='day'):
    #检测是否过期
    check(listname, timetype)
    r.rpush(listname, target)

def exam(target,listname):
    allitem = r.lrange(listname, 0, -1)
    if(target in allitem):
        r.lrem(listname, target, -1)
        return True
    else:
        return False

def verification_code_get(usr):
    #直接以键值对储存在r里
    r.get(usr)

def verification_code_set(usr, val):
    r.set(usr, val)

def indexlist(index, listname):
    r.lindex(listname, index)

def getlist(listname):
    r.lrange(listname, 0, -1)

def clear(listname):
    r.ltrim(listname, 0, 0)

pwd_change_today = 'pwd_change_today'
pwd_change_rege = 'pwd_change_rege'
pwd_salt = 'koizumimoekadaisuki'
#verification_codes = {'user':'code'}
tempfile_list = 'tempfile_list'
verification_codes_random = 'verification_codes_random'

def init():
    r.flushall()

    r.lpush(pwd_change_today, datetime.datetime.today())
    r.lpush(pwd_change_rege, datetime.datetime.today())
    r.lpush(tempfile_list, datetime.datetime.today())
    r.lpush(verification_codes_random, datetime.datetime.now().hour)