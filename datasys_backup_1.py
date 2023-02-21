from sqlalchemy import create_engine, MetaData, Column, distinct
from sqlalchemy.orm import reconstructor
from sqlalchemy.dialects.mysql import INTEGER, DOUBLE, BIGINT, VARCHAR, CHAR, TEXT, DATETIME, LONGTEXT, DATE
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
import datetime
import random
from collections import OrderedDict
import sqlalchemy.engine.row
import uuid
import os
import util
import urllib.parse
import zipfile

DEFAULTUUID = '00000000-0000-0000-0000-000000000000'
code_key = 'koizumisansuki_c'
pwd_key = 'koizumisansuki_p'
pwd_salt = 'koizumimoekadaisuki'
is_good_array = [0,'大吉','中吉','小吉','吉','末吉','凶','大凶']
horos={"date":datetime.date.today()}

file_path = './files/'
lawsuit_file_path = './files/lawsuit/'
notice_file_path = './files/notice/'
blog_file_path = './files/blog/'
blog_cover_path = 'files/blog/cover/'
arrange_path = './files/arrangement/'
lawsuit_path = './files/arrangement/lawsuit_department.dat'
random_pic_path = './files/pics/'
template_path = './files/template/'
data_file_path = './files/data/'
netdisk_path = './files/netdisk/'

def avg(l):
    sum = 0
    for i in l:
        if(type(i)!='int'):i=i[0]
        if(type(i)==type((1,))):sum += i[0]
        else:sum += i
    return int(sum/len(l))

def random_content(type, amount):
    if(type == 'blog'):
        return Article.get_random_article(amount)

def verification_code(leng):
    aCode = ['A', 'B', 'C', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'q', 'w', 'e', 'r', 't', 'y', 'i', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'z', 'x', 'c', 'b', 'n', 'm']
    result = []
    i = 0
    while(i<leng):
        result.append(aCode[random.randint(0,len(aCode)-1)])
        i+=1
    return result

def len_check(str, length):
    if(len(str)<=length):
        return str
    else:
        return str[-length:]

#, echo=True
engine = create_engine("mysql+mysqlconnector://root:Laobaofa100fen@localhost:3306", encoding="utf-8", pool_recycle=7200, pool_size = 20)
Base = declarative_base(bind=engine, metadata=MetaData(schema='zueldb'))

session = sessionmaker(bind=engine)()

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    tag = Column(VARCHAR(11))
    art_id = Column(CHAR(37))

class Quota(Base):
    __tablename__ = 'quotas'
    id = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    content = Column(VARCHAR(length=110))
    author = Column(CHAR(length=22), default='佚名')

    @staticmethod
    def new_quota(quota):
        if((len(quota.content)>109)or(len(quota.author)>21)):return 0
        session = sessionmaker(bind=engine)()
        session.add(quota)
        session.commit()
        session.close
        return 1
    
    @staticmethod
    def batch_update(l):
        cc = 0
        if(l):
            for i in l:
                if(i):
                    cc += Quota.new_quota(Quota(id=0,content=i[1],author=i[0]))
    
        return cc

class Horoscope(Base):
    __tablename__ = 'horoscopes'
    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, comment='id')
    thing = Column(VARCHAR(length=30), nullable=False, comment='宜/忌')
    abstract1 = Column(VARCHAR(length=30), nullable=False, comment='宜评价')
    abstract2 = Column(VARCHAR(length=30), nullable=False, comment='忌评价')

    @staticmethod
    def new_horo(horo):
        if((len(horo.thing)>28)or(len(horo.abstract1)>28)or(len(horo.abstract2)>28)):return 0
        session = sessionmaker(bind=engine)()
        session.add(horo)
        session.commit()
        session.close()
        return 1

    @staticmethod
    def batch_update(l):
        cc = 0
        if(l):
            for i in l:
                if(i):
                    cc += Horoscope.new_horo(Horoscope(id=0,thing=i[0],abstract1=i[1],abstract2=i[2]))
    
        return cc

def get_user(email):
    session = sessionmaker(bind=engine)()
    t = session.query(User).filter(User.email == email).first()
    session.close()
    return t

class User(UserMixin,Base):
    #用户结构：id，邮箱，昵称，密码，权限（root/admin/volunteer/norm/guest/block），真名，学号，周次（半角逗号隔开），部门，个签，是否部长（值为部门或0），是否组长， 邀请码
    __tablename__ = 'users'
    id = Column(VARCHAR(length=36), primary_key=True, nullable=False, comment='用户id', default=DEFAULTUUID)
    email = Column(VARCHAR(length=30), nullable=False, comment='电子邮箱', default='')
    nickname = Column(VARCHAR(length=30), nullable=False, comment='用户名', default='用户已注销')
    pwd = Column(CHAR(length=32), nullable=False, comment='密码', default='')
    authority = Column(VARCHAR(length=30), nullable=False, comment='用户权限', default='norm')
    realname = Column(VARCHAR(length=30), nullable=False, comment='姓名', default='')
    num = Column(VARCHAR(length=30), nullable=False, comment='学号', default='')
    signature = Column(VARCHAR(length=110), nullable=False, default='')
    code = Column(CHAR(length=37), nullable=False, default=DEFAULTUUID)

    def self_check(self, id):
        return (self.id == id)

    @reconstructor
    def init(self):
        #每日运势
        self.date = datetime.date.today()
        self.goodauthority = 0
        self.horo=[[],[],[],[]]

    def get_attr_tuple(self):
        return (self.id, self.email, self.nickname, self.pwd, self.authority, self.realname, self.num, self.signature, self.code)
    
    @staticmethod
    def empty_user():
        return User()

    @staticmethod
    def new_user(u):
        session = sessionmaker(bind=engine)()
        session.add(u)
        session.commit()
        session.close()

    @staticmethod
    def del_user(id):
        session = sessionmaker(bind=engine)()
        session.query(User).filter(User.id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def update_user(id, address=0, nickname=0, pwd=0, authority=0, name=0, num=0, signature=0):
        if(id == '185fa17d-3050-11ed-8449-bc091babf751'):
            #pwd=0
            authority=0
            #不修改唯一最高用户的密码和权限
        #降级method=1,升级或平级method=0
        address=0
        cmd = {}
        if(address):
            cmd[User.email] = address
        if(nickname):
            cmd[User.nickname] = nickname  
        if(pwd):
            cmd[User.pwd] = pwd
        if(authority):
            cmd[User.authority] = authority
        if(name):
            cmd[User.realname] = name
        if(num):
            cmd[User.num] = num
        if(signature):
            cmd[User.signature] = signature
        session = sessionmaker(bind=engine)()
        session.query(User).filter(User.id == id).update(cmd)
        session.commit()
        session.close()

    @staticmethod
    def set_attr(attr,val,old_val):
        session = sessionmaker(bind=engine)()
        session.query(User).filter(attr == old_val).update({attr:val})
        session.commit
        session.close()

    def get_id(self):
        return self.id

    def verify_password(self,pwd):
        return pwd == self.pwd

    def get_horoscope(self):
        #每日运势
        self.date = datetime.date.today()
        self.goodauthority = 0
        self.horo=[[],[],[],[]]
        #每日运势
        if(self.date != horos["date"]):
            #如果日期与上次不同，清空字典
            horos.clear()
            horos["date"]=self.date
        if(not(self.id in horos)):
            #如果字典被清空或今日没有抽签，重新抽签
            session = sessionmaker(bind=engine)()
            count = session.query(Horoscope).count() - 1
            horolist = session.query(Horoscope).all()
            session.close()
            is_selected = []
            for i in range(4):
                t = horolist[random.randint(0,count)]
                while(t.id in is_selected):
                    t = horolist[random.randint(0,count)]
                is_selected.append(t.id)
                if(i <= 1):
                    self.horo[i].append(t.thing)
                    self.horo[i].append(t.abstract1)
                else:
                    self.horo[i].append(t.thing)
                    self.horo[i].append(t.abstract2)

            self.goodauthority = is_good_array[random.randint(1,7)]

            horos[self.id] = (self.goodauthority,self.horo)
            return horos[self.id]

        else:
            return horos[self.id]

    def get_quota(self):
        #一句名言
        session = sessionmaker(bind=engine)()
        count = session.query(Quota).count() - 1
        result = session.query(Quota).all()
        session.close()
        rand = random.randint(0,count)
        result = [result[rand].id, result[rand].content, result[rand].author]

        return result

    @staticmethod
    def get_user_id(id):
        session_u = sessionmaker(bind=engine)()
        result = session_u.query(User).filter(User.id == id).first()
        session_u.close()
        return result

    @staticmethod
    def get(id):
        """根据用户ID获取用户实体，为 login_user 方法提供支持"""
        session_u = sessionmaker(bind=engine)()
        result = session_u.query(User).filter(User.id == id).first()

        session_u.close()
        if(result):
            return result
        else:return None

    @staticmethod
    def get_name(id):
        session = sessionmaker(bind=engine)()
        result = session.query(User.nickname).filter(User.id == id).first()
        session.close()
        if(result):
            return result[0]
        return '用户已注销'

    @staticmethod
    def get_volunteer(email = 0):
        session = sessionmaker(bind=engine)()
        if(email == 0):data = session.query(User.realname, User.id).filter((User.authority != 'norm') & (User.authority != 'guest') & (User.authority != 'block')).order_by(User.realname.desc()).all()
        else:data = session.query(User.realname, User.email).filter((User.authority != 'norm') & (User.authority != 'guest') & (User.authority != 'block')).order_by(User.realname.asc()).all
        session.close()
        return data

    @staticmethod
    def update_lawsuit(data):
        cc = 0
        line1 = ''
        flag = 0
        for i in data:
            if(flag):
                line1 += ';'
                flag = 0
            line1 += (i[0] + ',' + i[1])
            flag = 1
            cc += 1
        with open(lawsuit_path, "w", encoding="UTF-8") as f:
            f.write(line1)

        return cc

    @staticmethod
    def get_lawsuit_today(for_html=0):
        with open(lawsuit_path, "r", encoding="UTF-8") as f:
            text=f.readline()
        table=text.split(';')
        today=datetime.date.weekday(datetime.datetime.today())
        table=table[today].split(',')
        to=[]
        for i in table:
            t=i.split('_')[1]
            to.append(User.get(t))
            #to.append(User.get('185fa17d-3050-11ed-8449-bc091babf751'))


        if(for_html):
            data=[]
            data.append([to[0].id,to[0].realname,to[0].email])
            data.append([to[1].id,to[1].realname,to[1].email])
            return data
        return to

    @staticmethod
    def get_from_email(email):
        session = sessionmaker(bind=engine)()
        result = session.query(User).filter(User.email == email).first()
        session.close()
        if(result):return result
        else:return None

    @staticmethod
    def get_for_table(id,t='single'):
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(User.id, User.nickname, User.realname, User.num, User.authority).all()
            session.close()
            return result
        result = session.query(User.id, User.nickname, User.realname, User.num, User.authority).filter(User.id == id).first()
        session.close()
        result = list(result)
        if(result):
            #id,昵称,姓名,学号,权限
            return result
        return []

    @staticmethod
    def get_from_code(code, get_id=0):
        key = code_key
        id = util.aesDecrypt(key, code)
        u = User.get(id)
        if(u):
            if(get_id):
                return u.id
            else:
                return u
        return None

    def generate_code(self):
        key = code_key
        return util.aesEncrypt(key, self.id)

    @staticmethod
    def get_from_pwd_code(code, get_id=0):
        key = pwd_key
        code = urllib.parse.unquote(code)
        id = util.aesDecrypt(key, code)
        u = User.get(id)
        if(u):
            if(get_id):
                return u.id
            else:
                return u
        return None

    def generate_pwd_code(self):
        key = pwd_key
        result = util.aesEncrypt(key, self.id)
        result = urllib.parse.quote(result)
        return result

    @staticmethod
    def search_same(item, content):
        session = sessionmaker(bind=engine)()
        result = session.query(User).filter(item == content).first()
        session.close()
        if(result):return result
        else:return None

    @staticmethod
    def get_contact():
        session = sessionmaker(bind=engine)()
        data = session.query(User.email).filter((User.authority == 'admin') | (User.authority == 'root')).all()
        session.close()
        result = []
        if(data):
            for i in data:
                if(i):
                    result.append(i[0])
        return result

    @staticmethod
    def block(id,t='single'):
        result = []
        u = User.get(id)
        if(u):
            if((u.authority != 'root') and (u.authority != 'admin') and (u.authority != 'volunteer')):
                if(t != 'all'):
                    session.query(User).filter(User.id == id).update({User.authority:'block'})
                    session.commit()
                    result.append([u.email,u.realname])
                    util.email(u.email, '中南数据_封号', '你在“中南数据”网站下的账号已被封禁，如需解封请联系系统管理员', 0, 0, 0, 1)
                #更改关系串封号为查询关系串
            if(t == 'all'):
                t0 = User.block(u.code, 'all')
                result.extend(t0)
                return result
        return result

    @staticmethod
    def unblock(id,t='single'):
        result = []
        u = User.get(id)
        if(u):
            result.append([u.email,u.realname])
            if((u.authority != 'root') and (u.authority != 'admin') and (u.authority != 'volunteer')):
                if(t != 'all'):
                    session.query(User).filter(User.id == id).update({User.authority:'norm'})
                    session.commit()
            if(t == 'all'):
                t0 = User.unblock(u.code, 'all')
                result.extend(t0)
                return result
        return result

    @staticmethod
    def batch_update(l):
        if(not l):return -1
        cc = 0
        session = sessionmaker(bind=engine)()

        for i in l:
            #std = ['姓名', '邮箱', '年级']
            t = session.query(User).filter(User.email == i[1]).first()
            if(t):
                if((t.authority != 'root') and (t.authority != 'admin') and (t.authority != 'volunteer')):
                    session.query(User).filter(User.email == i[1]).update({User.authority:'volunteer'})
                    cc += 1
        session.commit()
        session.close()
        return cc

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(CHAR(length=37), primary_key=True, nullable=False)
    from_id = Column(TEXT, nullable=False)
    to_id = Column(TEXT, nullable=False)
    title = Column(VARCHAR(length=110), nullable=False)
    abstract = Column(VARCHAR(length=550), nullable=False)
    file = Column(LONGTEXT(), default='')
    pubdate = Column(DATETIME(), nullable=False)
    subdate = Column(DATETIME(), nullable=False, default='')
    status = Column(VARCHAR(length=50), nullable=False)
    quota_id = Column(TEXT(), nullable=False, default=DEFAULTUUID)

    
    def init(self, id, from_id, to_id, title, abstract, file, pubdate, subdate, status, quota_id):
        self.id = id
        self.title = title
        self.pubdate = pubdate
        self.from_id = from_id
        #半角逗号隔开
        self.to_id = to_id
        #半角逗号隔开
        self.subdate = subdate
        #未完成时是预计提交日期，完成后是提交日期
        self.abstract = abstract
        #content内容格式为多次继承
        self.file = file
        #存放文件id，以半角逗号隔开
        self.status = status
        #'to-do','done'
        self.quota_id = quota_id
        #quota_id为引用待办id，如有引用其他多个待办，以半角逗号隔开
        #代书：提交文书创建待办，待办发给诉讼部当日两位对接同学，并创建相同特征码，回复时提交文件并同时引用上次特征码
        #举报：从举报者向所有管理员发送相同特征码待办

    def get_attr_tuple(self):
        return (self.id, self.from_id, self.to_id, self.title, self.abstract, self.file, self.pubdate, self.subdate, self.status, self.quota_id)
    
    def finish(self, finish_all=0, abstract=''):
        #完成与回复都将subdate由理应提交的日期改为提交日期
        session = sessionmaker(bind=engine)()
        if(self.status == 'done'):return -1
        if(finish_all):
            if(self.to_id[-1:] == ','):self.to_id = self.to_id[:-1]
            t = self.to_id.split(',')
            receiver = []
            for i in t:
                if(i):
                    t0=session.query(User.email).filter(User.id == i).first()
                    if(t0):receiver.append(t0[0])
                    else:return -1
            for i in receiver:
                util.email(i, '【办结】'+self.title, abstract, 0,'https://www.zhongnandata.top/task/content?url=' + self.id, 0)
        session.query(Task).filter(Task.id == self.id).update({Task.status:'done', Task.subdate:datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        session.close()
        
    def reply(self, from_id, to_id, abstract, file, pubdate, subdate):
        if(self.status == 'done'):return -1
        a=Task.new_task(Task(id=str(uuid.uuid1()), from_id=from_id, to_id=to_id, title=self.title, abstract=abstract, file=file, pubdate=pubdate, subdate=subdate, status='todo', quota_id=self.quota_id + ',' + self.id))
        self.finish()
        return a

    @staticmethod
    def new_task(task):
        session = sessionmaker(bind=engine)()
        task.title=len_check(task.title, 100)
        task.abstract=len_check(task.abstract, 500)
        task.status=len_check(task.status, 50)

        if(task.from_id[-1:] == ','):task.from_id = task.from_id[:-1]
        if(task.to_id[-1:] == ','):task.to_id = task.to_id[:-1]
        t = task.to_id.split(',')
        receiver = []
        for i in t:
            if(i):
                t0=session.query(User.email).filter(User.id == i).first()
                if(t0):receiver.append(t0[0])
                else:return -1

        file_t = task.file.split(',')
        file = []
        if(file_t):
            for i in file_t:
                t = File.get_file(i).path
                if(t):file.append(t)
        
        session.add(task)
        session.commit()
        session.close()

        for i in receiver:
            util.email(i, task.title, task.abstract, file,'https://www.zhongnandata.top/task/content?url=' + task.id, str(task.subdate))

    @staticmethod
    def get_task(id):
        return session.query(Task).filter(Task.id == id).first()

    @staticmethod
    def get_user_task(id):
        session = sessionmaker(bind=engine)()
        result = session.query(Task).filter(Task.to_id.like(f'%{id}%')).filter(Task.status!='done').all()
        session.close()
        data = [0]
        if(result):
            for i in result:
                if(i):
                    data.append({'id':i.id, 'title':i.title, 'abstract':i.abstract, 'subdate':i.subdate})
                    data[0] += 1
                else:
                    return data
            return data
        else:
            return data

    @staticmethod
    def get_for_quota(id, need_self=0):
        result = []
        session = sessionmaker(bind=engine)()
        quotas = session.query(Task.quota_id).filter(Task.id == id).first()[0]
        if(quotas[-1:] == ','):quotas = quotas[:-1]
        if(quotas != DEFAULTUUID):
            quotas = quotas.split(',')
            for i in quotas:
                if(i != DEFAULTUUID):
                    t = session.query(Task).filter(Task.id == i).first()
                    result.append([i, t.title, Task.from_to(i), t.subdate])    
        if(need_self):
            t = session.query(Task).filter(Task.id == id).first()
            result.append([id, t.title, Task.from_to(id), t.subdate])
        session.close()
        return result

    @staticmethod
    def from_to(id):
        session = sessionmaker(bind=engine)()
        t = session.query(Task).filter(Task.id == id).first()
        from_t = t.from_id.split(',')
        from_n = []
        to_t = t.to_id.split(',')
        to_n = []
        for i in from_t:
            from_n.append(session.query(User.id,User.realname,User.email).filter(User.id == i).first())
        for i in to_t:
            to_n.append(session.query(User.id,User.realname,User.email).filter(User.id == i).first())
        session.close()
        return {'from':from_n,'to':to_n}
    
    @staticmethod
    def get_for_table(id, t='single'):
        #<th>案件名</th><th>来自</th><th>发往</th><th>上传时间</th><th>状态</th><th>来往案件</th>
        data = []
        last_data = []
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(Task.id, Task.title, Task.from_id, Task.to_id, Task.pubdate, Task.status, Task.quota_id).all()
            no_need = []
            for i in result:
                t0 = list(i)
                fr_t = t0[2].split(',')
                fr = []
                for i in fr_t:
                    t=session.query(User.id, User.realname).filter(User.id == i).first()
                    if(not t):t=['', '已注销']
                    fr.append(t)

                to_t = t0[3].split(',')
                to = []
                for i in to_t:
                    t=session.query(User.id, User.realname).filter(User.id == i).first()
                    if(not t):t=['', '已注销']
                    to.append(t)
                
                qu_t = t0[6].split(',')
                if(DEFAULTUUID in qu_t):qu_t.remove(DEFAULTUUID)
                qu = []
                for i in qu_t:
                    qu.append(session.query(Task.id, Task.pubdate).filter(Task.id == i).first())
                    no_need.append(i)

                t0[2] = fr
                t0[3] = to
                t0[6] = qu

                data.append(t0)


            for i in data:
                if(i[0] not in no_need):
                    last_data.append(i)

            return last_data
        result = session.query(Task.id, Task.title, Task.pubdate, Task.status, Task.quota_id).filter(Task.id == id).first()
        if(result):
            #id,课程号,课程名,任课老师,模块,评分
            result = list(result)
            fr_t = result[2].split(',')
            fr = []
            for i in fr_t:
                t=session.query(User.id, User.realname).filter(User.id == i).first()
                if(not t):t=['', '已注销']
                fr.append(t)

            to_t = result[3].split(',')
            to = []
            for i in to_t:
                t=session.query(User.id, User.realname).filter(User.id == i).first()
                if(not t):t=['', '已注销']
                to.append(t)
            
            qu_t = result[6].split(',')
            if(DEFAULTUUID in qu_t):qu_t.remove(DEFAULTUUID)
            qu = []
            for i in qu_t:
                qu.append(session.query(Task.id, Task.pubdate).filter(Task.id == i).first())

            result[2] = fr
            result[3] = to
            result[6] = qu

            session.close()
            return result
        session.close()
        return []


class Article(Base):
    __tablename__ = 'articles'
    id = Column(CHAR(length=37), primary_key=True, nullable=False, comment='文章id')
    title = Column(VARCHAR(length=30), nullable=False, comment='文章标题')
    pubdate = Column(DATETIME(), nullable=False, comment='发布时间')
    author_id = Column(CHAR(length=37), nullable=False, comment='作者id')
    keyword = Column(VARCHAR(length=110), nullable=False, comment='关键词，用半角逗号隔开', default='')
    abstract = Column(VARCHAR(length=110), nullable=False, comment='100字以内摘要')
    cover = Column(VARCHAR(length=50), nullable=False)
    content = Column(LONGTEXT(), nullable=False, comment='内容')
    files = Column(LONGTEXT(), default='')
    
    def self_check(self, id):
        return (self.author_id == id)

    def init(self, id, title, pubdate, author_id, keyword, abstract, cover, content, files):
        self.id = id
        self.title = title
        self.pubdate = pubdate
        self.author_id = author_id
        self.keyword = keyword
        #keyword=tag,应当以半角逗号分割
        self.abstract = abstract
        self.content = content
        self.files = files
        self.cover = cover

    def get_attr_tuple(self):
        return (self.id, self.title, self.pubdate, self.author_id, self.keyword, self.abstract, self.cover, self.content, self.files)

    def get_tag(self):
        if(not self.keyword):return 0
        elif(',' in self.keyword):return self.keyword.split(',')
        elif('，' in self.keyword):return self.keyword.split('，')
        else:return [self.keyword]
        
    @staticmethod
    def new_blog(blog):
        blog.title=len_check(blog.title, 30)
        blog.keyword=len_check(blog.keyword, 100)
        blog.abstract=len_check(blog.abstract, 100)
        session = sessionmaker(bind=engine)()
        session.add(blog)
        tags = blog.get_tag()
        if(not tags):
            session.commit()
            return
        for i in tags:
            t=len_check(i,10)
            new_tag = Tag(id=0, tag=t, art_id=blog.id)
            session.add(new_tag)
        session.commit()
        session.close()

    @staticmethod
    def del_blog(id):
        session = sessionmaker(bind=engine)()
        t = session.query(Article).filter(Article.id == id).first()
        if(not t):return -1
        if(t.files):
            t0=t.files.split(',')
            for i in t0:
                if(i):File.del_file(i)
        os.remove(blog_cover_path+t.cover)
        session.query(Tag).filter(Tag.art_id == id).delete()
        session.query(Article).filter(Article.id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def get_blog(id):
        session = sessionmaker(bind=engine)()
        result = session.query(Article).filter(Article.id == id).first()
        session.close()
        if(result):
            return result
        else:
            return 0

    @staticmethod
    def get_user_blog(id):
        session = sessionmaker(bind=engine)()
        result = session.query(Article).filter(Article.author_id == id).all()
        session.close()
        data = [0]
        if(result):
            for i in result:
                if(i):
                    data.append({'id':i.id, 'title':i.title, 'abstract':i.abstract, 'cover':'/api/cover?url=' + i.cover, 'pubdate':i.pubdate, 'keyword':i.keyword})
                    data[0] += 1
                else:
                    return data
            return data
        else:
            return data

    @staticmethod
    def get_random_article(quantity):
        session = sessionmaker(bind=engine)()
        result_all = session.query(Article.id, Article.cover, Article.abstract, Article.title).all()
        session.close()
        blog_selected_id = []
        last_result = []
        num_of_blogs = min(len(result_all),quantity)
        while(num_of_blogs):
            num_of_blogs -= 1
            if(result_all):
                result = result_all[random.randint(0, len(result_all) - 1)]
                while(result[0] in blog_selected_id):
                    result = result_all[random.randint(0, len(result_all) - 1)]
                blog_selected_id.append(result[0])
                last_result.append(Article(id = result[0], title = result[3], abstract = result[2], cover = result[1]))
            else:return 0
        return last_result

    @staticmethod
    def get_blog_count():
        session = sessionmaker(bind=engine)()
        result = session.query(Article).count()
        session.close()
        return result

    @staticmethod
    def get_blog_10(pn):
        session = sessionmaker(bind=engine)()
        blogs = session.query(Article).all()
        session.close()
        amount = len(blogs)
        result = []
        i = min((pn-1)*10,amount/10)
        if(amount >= 10*pn):
            i = 10*pn - 10
            while(i < 10*pn):
                result.append(blogs[i])
                i += 1
            return result
        else:
            i = int(amount/10)*10
            while(i < amount):
                result.append(blogs[i])
                i += 1
            return result
        
    @staticmethod
    def get_for_table(id,t='single'):
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(Article.id, Article.title, User.nickname, Article.abstract, Article.keyword, Article.pubdate).outerjoin(User, User.id==Article.author_id).distinct(Article.id, Article.title, User.nickname, Article.abstract, Tag.tag, Article.pubdate).all()
            session.close()
            return result
        result = session.query(Article.id, Article.title, User.nickname, Article.abstract, Article.keyword, Article.pubdate).outerjoin(User, User.id==Article.author_id).filter(Article.id == id).distinct(Article.id, Article.title, User.nickname, Article.abstract, Tag.tag, Article.pubdate).first()
        session.close()
        if(result):
            #id,课程号,课程名,任课老师,模块,评分
            return result
        return []

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(CHAR(length=37), primary_key=True, nullable=False, comment='课程评价id')
    lesson_id = Column(CHAR(length=37), nullable=False, comment='课程id')
    pubdate = Column(DATETIME(), nullable=False, comment='发布时间')
    author_id = Column(CHAR(length=37), nullable=False, comment='作者id')
    lesson_num = Column(VARCHAR(length=30), nullable=False)
    teacher = Column(VARCHAR(length=30), nullable=False)
    scoring = Column(INTEGER(), nullable=False, comment='给分评价')
    useful = Column(INTEGER(), nullable=False, comment='有用程度评价')
    easy = Column(INTEGER(), nullable=False, comment='易学程度评价')
    whole = Column(INTEGER(), nullable=False, comment='总体评价')
    content = Column(LONGTEXT(), nullable=False, default='')
    abstract = Column(VARCHAR(length=110), default='')

    def self_check(self, id):
        return (self.author_id == id)
    
    def init(self, id, lesson_id, pubdate, author_id, lesson_num, teacher, scoring, useful, easy, whole, content, abstract):
        self.id = id
        self.lesson_id = lesson_id
        self.pubdate = pubdate
        self.author_id = author_id
        self.lesson_num = lesson_num
        self.teacher = teacher
        self.abstract = abstract
        self.scoring = scoring
        self.useful = useful
        self.easy = easy
        self.whole = whole
        self.content = content
        #课程综合评分算法：每个课程号和课序号单独区分，给分情况20%，实践适用可能性useful 40%，理解难度easy 40%

    def get_attr_tuple(self):
        return (self.id, self.lesson_id, self.pubdate, self.author_id, self.lesson_num, self.teacher, self.scoring, self.useful, self.easy, self.whole, self.content, self.abstract)

    @staticmethod
    def get_from_id(id):
        if(type(id) == sqlalchemy.engine.row.Row):id=id[0]
        session = sessionmaker(bind=engine)()
        result = session.query(Assessment).filter(Assessment.id == id).first()
        session.close()
        if(result):
            return result
        else:return 0

    @staticmethod
    def assessment_check(id, num):
        #同一用户对一个课程只能评价一次
        session = sessionmaker(bind=engine)()
        t=session.query(Assessment.lesson_num).filter(Assessment.author_id == id).all()
        session.close()
        for i in t:
            if(num in i):
                return 1 #评价过
        else:return 0

    @staticmethod
    def new_assessment(assessment):
        session = sessionmaker(bind=engine)()
        assessment.lesson_num=len_check(assessment.lesson_num,29)
        assessment.teacher=len_check(assessment.teacher,29)
        assessment.abstract=len_check(assessment.abstract,100)
        if(assessment.abstract):
            assessment.abstract = assessment.abstract.replace('\n','。')
            assessment.abstract = assessment.abstract.replace('\r','')
        
        Lesson.update_lesson(assessment.lesson_id, score=(assessment.scoring*0.2 + assessment.useful*0.4 + assessment.easy*0.4))
        session.add(assessment)
        session.commit()
        session.close()

    @staticmethod
    def del_assessment(id):
        session = sessionmaker(bind=engine)()
        t=session.query(Assessment).filter(Assessment.id == id).first()
        if(not t):return -1
        Lesson.reverse(t.lesson_id, score=(t.scoring*0.2 + t.useful*0.4 + t.easy*0.4))
        session.query(Assessment).filter(Assessment.id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def get_user_assessment(id, lesson_id_only=0):
        session = sessionmaker(bind=engine)()
        if(lesson_id_only):
            result = session.query(Assessment.lesson_id).filter(Assessment.author_id == id).all()
            session.close()
            return result
        else:
            result = session.query(Assessment).filter(Assessment.author_id == id).all()
            session.close()
            data = [0]
            if(result):
                for i in result:
                    if(i):
                        lessonname = session.query(Lesson.lessonname).filter(Lesson.id == i.lesson_id).first()[0]
                        i.abstract = i.abstract.replace('\n','。')
                        i.abstract = i.abstract.replace('\r','')
                        data.append({'id':i.id, 'lesson':lessonname, 'teacher':i.teacher, 'abstract':i.abstract, 'score':i.whole, 'pubdate':i.pubdate, 'lesson_id':i.lesson_id})
                        data[0] += 1
                    else:
                        return data
                return data
            else:
                return data

    @staticmethod
    def get_by_teacher_lessonnum(teacher=0,num=0,score_only=0,id_only=1):
        session = sessionmaker(bind=engine)()
        if(score_only):
            scoring = session.query(Assessment.scoring).filter((Assessment.teacher == teacher) & (Assessment.lesson_num == num)).all()
            if(scoring):scoring = avg(scoring)
            else:scoring = 0
            useful = session.query(Assessment.useful).filter(Assessment.lesson_num == num).all()
            if(useful):useful = avg(useful)
            else:useful = 0
            easy = session.query(Assessment.easy).filter(Assessment.lesson_num == num).all()
            if(easy):easy = avg(easy)
            else:easy = 0

            return[scoring,useful,easy]
        
        if(teacher and num):
            result = session.query(Assessment.id).filter((Assessment.teacher == teacher) & (Assessment.lesson_num == num)).all()
        elif(teacher):
            result = session.query(Assessment.id).filter(Assessment.teacher == teacher).all()
        elif(num):
            result = session.query(Assessment.id).filter(Assessment.lesson_num == num).all()
        data = []
        if(result):
            for i in result:
                a = Assessment.get_from_id(i)
                if(a):
                    a.abstract = a.abstract.replace('\n','。')
                    a.abstract = a.abstract.replace('\r','')
                data.append(a)
        session.close()
        return data

    @staticmethod
    def random_from_id(id):
        session = sessionmaker(bind=engine)()
        count = session.query(Assessment).filter(Assessment.lesson_id == id).filter(Assessment.abstract != '').count()
        if(count==0):return 0
        num = random.randint(0,count-1)
        a = session.query(Assessment).filter(Assessment.lesson_id == id).filter(Assessment.abstract != '')[num].abstract
        session.close()

        if(a):
            a = a.replace('\n','。')
            a = a.replace('\r','')
        return a

    @staticmethod
    def get_for_table(id,t='single'):
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(User.nickname, User.realname, Assessment.id, Assessment.lesson_num, Lesson.lessonname, Assessment.teacher, Assessment.whole).join(Lesson,Assessment.lesson_id==Lesson.id).outerjoin(User,Assessment.author_id==User.id).distinct(User.nickname, User.realname, Assessment.id, Assessment.lesson_num, Lesson.lessonname, Assessment.teacher, Assessment.whole).all()
            session.close()
            return result
        result = session.query(User.nickname, User.realname, Assessment.id, Assessment.lesson_num, Lesson.lessonname, Assessment.teacher, Assessment.whole).join(Lesson,Assessment.lesson_id==Lesson.id).outerjoin(User,Assessment.author_id==User.id).filter(Lesson.id == id).distinct(User.nickname, User.realname, Assessment.id, Assessment.lesson_num, Lesson.lessonname, Assessment.teacher, Assessment.whole).first()
        session.close()
        if(result):
            #id,课程号,课程名,任课老师,评分
            return result

class File(Base):
    __tablename__ = 'files'
    id = Column(CHAR(length=37), primary_key=True, nullable=False, comment='文件id')
    title = Column(TEXT, nullable=False)
    pubdate = Column(DATETIME(), nullable=False, comment='发布时间')
    author_id = Column(CHAR(length=37), nullable=False, comment='作者id')
    keyword = Column(VARCHAR(length=110), nullable=False, comment='关键词，用半角逗号隔开', default='')
    path = Column(TEXT, nullable=False)
    abstract = Column(VARCHAR(length=110), comment='100字以内摘要', default='')
    
    def init(self, id, title, pubdate, author_id, keyword, path, abstract):
        self.id = id
        self.title = title
        self.pubdate = pubdate
        self.author_id = author_id
        self.keyword = keyword
        self.path = path
        self.abstract = abstract

    def get_attr_tuple(self):
        return (self.id, self.title, self.pubdate, self.author_id, self.keyword, self.path, self.abstract)

    @staticmethod
    def new_file(file):
        file.abstract=len_check(file.abstract, 100)
        session = sessionmaker(bind=engine)()
        session.add(file)
        session.commit()
        session.close()

    @staticmethod
    def del_file(id):
        session = sessionmaker(bind=engine)()
        t=session.query(File).filter(File.id == id).first()
        if(not t):return -1
        os.remove(t.path)
        session.query(File).filter(File.id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def get_file(id):
        session = sessionmaker(bind=engine)()
        result = session.query(File).filter(File.id == id).first()
        session.close()
        if(result):
            return result
        else:
            return 0

    @staticmethod
    def get_file_list(x):
        result = []
        for root, dirs, files in os.walk(x):
            if root != x:
                break
            for a in files:
                path = os.path.join(root, a)
                result.append(path)
        return result

    @staticmethod
    def get_random_file(path):
        dir_l = File.get_file_list(path)
        return dir_l[random.randint(0,len(dir_l)-1)]

    @staticmethod
    def get_template(name):
        return template_path + name
    
    @staticmethod
    def get_netdisk(type = 'netdisk', query = ''):
        session = sessionmaker(bind=engine)()
        if(query):
            if(type == 'netdisk'):
                path_p = list(session.query(File.path).filter(File.keyword.not_like('\_%') & File.path.like('%\.pptx')).all())
                path_d = list(session.query(File.path).filter(File.keyword.not_like('\_%') & File.path.like('%\.docx')).all())

            elif(type == 'all'):
                path_p = list(session.query(File.path).filter(File.path.like('%.pptx')).all())
                path_d = list(session.query(File.path).filter(File.path.like('%.docx')).all())

            path_p_f = []
            path_d_f = []
            for i in path_p:
                path_p_f.append(i[0])
            for i in path_d:
                path_d_f.append(i[0])
            
            data = util.aggregate_search_list(query, path_d_f, path_p_f)
            result = []
            for key in data:
                #username:命中次数，keyword:文件类型，abstract:命中内容
                elmt = list(session.query(File.id,File.title,File.pubdate).filter(File.path == key).first())
                elmt.insert(2, data[key][0])
                elmt.insert(2, key[-4:])
                elmt.insert(2, len(data[key]))
                result.append(elmt)
            session.close()
            return result
        else:
            if(type == 'netdisk'):
                return list(session.query(File.id,File.title,User.nickname,File.keyword,File.abstract,File.pubdate).outerjoin(User, User.id==File.author_id).distinct(File.id,File.title,User.nickname,File.keyword,File.abstract,File.pubdate).filter(File.keyword.not_like('\_%')).all())
            elif(type == 'all'):
                return list(session.query(File.id,File.title,User.nickname,File.keyword,File.abstract,File.pubdate).outerjoin(User, User.id==File.author_id).distinct(File.id,File.title,User.nickname,File.keyword,File.abstract,File.pubdate).all())

    @staticmethod
    def clear_redundancy():
        session = sessionmaker(bind=engine)()
        del_str = ''
        blog_list = []
        notice_list = []
        cover = []
        for i in session.query(Article.cover):
            cover.append(i[0])

        for i in session.query(Article.files):
            if(i and i[0]):
                tl = i[0].split(',')
                if(tl):
                    for j in tl:
                        if(j and (j not in blog_list)):
                            blog_list.append(j)

        for i in session.query(Notice.files):
            if(i):
                tl = i[0].split(',')
                if(tl):
                    for j in tl:
                        if(j and (j not in notice_list)):
                            notice_list.append(j)

        t_del_list = []
        for f in session.query(File):
            if(not os.path.exists(f.path)):
                del_str = del_str + f'{f.title};'
                t_del_list.append(f.id)
        for i in t_del_list:
            session.query(File).filter(File.id == i).delete()

        for f in session.query(File).filter(File.keyword == '_blog'):
            if(f.id not in blog_list):
                del_str = del_str + f'{f.title};'
                File.del_file(f.id)
        for f in session.query(File).filter(File.keyword == '_notice'):
            if(f.id not in notice_list):
                del_str = del_str + f'{f.title};'
                File.del_file(f.id)
        
        files = [x for x in os.listdir(blog_cover_path)]
        for f in files:
            if(f not in cover):
                del_str = del_str + f'封面：{f};'
                os.remove(blog_cover_path + f)
                
        session.commit()
        session.close()

        if(not del_str):del_str = '未找到冗余项'
        return del_str

    @staticmethod
    def get_zip(target_list):
        if(not target_list):return ''
        session = sessionmaker(bind=engine)()

        paths = []
        for i in target_list:
            t = session.query(File.path).filter(File.id == i).first()
            if(t):
                if(t[0]):
                    paths.append(t[0])
        session.close()
        if(not paths):return ''
        
        fname = netdisk_path + str(uuid.uuid1()) + '.zip'
        zfile = zipfile.ZipFile(fname, "w", compression=zipfile.ZIP_DEFLATED)
        for i in paths:
            zfile.write(i, i[i.find('_')+1:])
        zfile.close()

        return fname

class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(CHAR(length=37), primary_key=True, nullable=False, comment='课程id')
    lessonname = Column(VARCHAR(length=55), nullable=False, comment='课程名')
    num = Column(VARCHAR(length=30), nullable=False, comment='课程号')
    serial_num = Column(VARCHAR(length=300), nullable=False, comment='课序号')
    teacher = Column(VARCHAR(length=30), nullable=False, comment='任课老师')
    lessontime = Column(VARCHAR(length=300))
    module = Column(VARCHAR(length=30), default='')
    week = Column(VARCHAR(length=30), nullable=False, comment='上课周次')
    credit = Column(INTEGER(), nullable=False, comment='学分')
    note = Column(VARCHAR(length=30), default='')
    score = Column(DOUBLE(asdecimal=True), default=0.0)
    score_times = Column(INTEGER(), default=0)
    updatetime = Column(DATE(), default='2023-01-04', comment='最后一次更新日期')
    
    def init(self, id, lessonname, num, serial_num, teacher, lessontime, module, week, credit, note, score, score_times):
        self.id = id
        self.lessonname = lessonname
        self.num = num
        self.serial_num = serial_num
        self.teacher = teacher
        self.lessontime = lessontime
        self.module = module
        self.week = week
        self.credit = credit
        self.note = note
        self.score = score
        self.score_times = score_times

    def get_attr_tuple(self):
        return (self.id, self.lessonname, self.num, self.serial_num, self.teacher, self.lessontime, self.module, self.week, self.credit, self.note, self.score, self.score_times, self.updatetime)

    @staticmethod
    def get_from_num(num):
        #返回一组课程，包括同一课程号的所有课程
        session = sessionmaker(bind=engine)()
        lessons = session.query(Lesson).filter(Lesson.num == num).all()
        session.close()
        if(lessons):
            return lessons
        else:
            return 0

    @staticmethod
    def get_from_teacher(name):
        #返回一组课程，包括同一老师的所有课程
        session = sessionmaker(bind=engine)()
        lessons = []
        t = session.query(Lesson).filter(Lesson.teacher == name).all()
        lessons.extend(t)
        t = session.query(Lesson).filter(Lesson.teacher.like(f'{name}\,%')).all()
        lessons.extend(t)
        t = session.query(Lesson).filter(Lesson.teacher.like(f'%\,{name}')).all()
        lessons.extend(t)
        session.close()
        return lessons

    @staticmethod
    def update_lesson(id, lessonname=0, num=0, serial_num=0, teacher=0, lessontime=0, module=0, week=0, credit=0, note=0, score=0):
        session = sessionmaker(bind=engine)()
        old_score = session.query(Lesson.score).filter(Lesson.id == id).first()
        if(old_score):old_score=float(old_score[0])
        else:old_score=0
        old_score_times = session.query(Lesson.score_times).filter(Lesson.id == id).first()
        if(old_score_times):old_score_times=float(old_score_times[0])
        else:old_score_times=0
        cmd = {}
        if(lessonname):
            cmd[Lesson.lessonname] = lessonname
        if(num):
            cmd[Lesson.num] = num
        if(serial_num):
            cmd[Lesson.serial_num] = serial_num
        if(teacher):
            cmd[Lesson.teacher] = teacher
        if(lessontime):
            cmd[Lesson.lessontime] = lessontime
        if(module):
            cmd[Lesson.module] = module
        if(week):
            cmd[Lesson.week] = week
        if(credit):
            cmd[Lesson.credit] = credit
        if(note):
            cmd[Lesson.note] = note
        if(score):
            cmd[Lesson.score] = (old_score + score)/(old_score_times+1)
            cmd[Lesson.score_times] = old_score_times+1
        session.query(Lesson).filter(Lesson.id == id).update(cmd)
        session.commit()
        session.close()

    @staticmethod
    #删除评分
    def reverse(id, score):
        session = sessionmaker(bind=engine)()
        t = session.query(Lesson).filter(Lesson.id == id).first()
        if(int(t.score_times) == 1):
            t.score = 0
            t.score_times = 0
            session.commit()
            return

        t.score = (float(t.score) * int(t.score_times) - score)/(int(t.score_times) - 1)
        t.score_times -= 1
        session.commit()
        session.close()

    @staticmethod
    def get_timetable(time):
        #0:单双周,剩下的每一组第一个是周几，第二个是数组第节节课
        result = []
        t = time.split(' ')
        result.append(t[1])
        t = t[0].split(',')
        for i in t:
            t1 = i[0]
            t2 = []
            lastcur = len(i)
            while(lastcur > 1):
                t2.append(int(i[(lastcur-2):lastcur]))
                lastcur -= 2
            result.append([t1,t2])

        return result

    #todo:有关于是否实现对于老师的评分功能
    @staticmethod
    def get_from_id(id):
        session = sessionmaker(bind=engine)()
        result = session.query(Lesson).filter(Lesson.id == id).first()
        session.close()
        if(result):
            return result
        else:return 0

    @staticmethod
    def get_for_table(id, t='single'):
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(Lesson.id, Lesson.num, Lesson.lessonname, Lesson.teacher, Lesson.module, Lesson.score, Lesson.updatetime).all()
            session.close()
            return result
        session.close()
        result = session.query(Lesson.id, Lesson.num, Lesson.lessonname, Lesson.teacher, Lesson.module, Lesson.score, Lesson.updatetime).filter(Lesson.id == id).first()
        if(result):
            #id,课程号,课程名,任课老师,模块,评分,最后一次更新时间
            return result
        return []

    @staticmethod
    def get_for_poster(q):

        result=[]
        session = sessionmaker(bind=engine)()
        general_l = session.query(Lesson).filter(Lesson.module != '-1').order_by(Lesson.score.desc()).all()
        session.close()
        i=0
        if(len(general_l) < q):q = len(general_l)
        while(i<q):
            comment = Assessment.random_from_id(general_l[i].id)
            score=0
            if(comment==0):
                comment='暂无评分'
            score=general_l[i].score
            t = {'lesson_url':'/lesson/content?url=' + general_l[i].id,'lesson_name':general_l[i].lessonname,'lesson_comment':comment,'score':score}
            result.append(t)
            i+=1
        return result

    @staticmethod
    def del_lesson(id):
        session = sessionmaker(bind=engine)()
        session.query(Lesson).filter(Lesson.id == id).delete()
        session.query(Assessment).filter(Assessment.lesson_id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def batch_update(l):
        session = sessionmaker(bind=engine)()
        this_time_flag = []
        if(not l):return -1
        cc_n = 0
        cc_u = 0
        new_l = ''
        up_l = ';;;;'
        for i in l:
            #['0课程号', '1课序号', '2课程名', '3学时', '4学分', '5任课教师', '6上课时间', '7周学时', '8上课周次', '9选课限制说明', 
            # 10'上课班级', '11上课年级', '12课程性质', '13模块']
            t = session.query(Lesson).filter((Lesson.num == i[0]) & (Lesson.teacher == i[5])).first()
            if(t):
                time = t.lessontime
                time=time.split(' ')
                if((time[0] != i[6].split(' ')[0]) and (len(time[0] + ',' + i[6].split(' ')[0] + ' ' + time[1])<50)):
                    time = time[0] + ',' + i[6].split(' ')[0] + ' ' + time[1]
                else:
                    time = t.lessontime
                if(len(t.serial_num + ',' + i[1])<29):
                    serial = t.serial_num + ',' + i[1]
                else:
                    serial = t.serial_num 

                if(t.id in this_time_flag):
                    cmd = {Lesson.serial_num:serial,Lesson.lessonname:i[2],Lesson.lessontime:time,Lesson.module:i[13],Lesson.week:i[8],Lesson.credit:i[4],Lesson.note:i[9],Lesson.updatetime:datetime.datetime.now().strftime("%Y-%m-%d")}
                else:
                    cmd = {Lesson.serial_num:i[1],Lesson.lessonname:i[2],Lesson.lessontime:i[6],Lesson.module:i[13],Lesson.week:i[8],Lesson.credit:i[4],Lesson.note:i[9],Lesson.updatetime:datetime.datetime.now().strftime("%Y-%m-%d")}
                    this_time_flag.append(t.id)
                session.query(Lesson).filter((Lesson.num == i[0]) & (Lesson.teacher == i[5])).update(cmd)
                up_l = up_l + f'更新：{t.num} ： {t.lessonname},{t.teacher};'
                cc_u += 1
            else:
                #id, lessonname, num, serial_num, teacher, lessontime, module, week, credit, note, score, score_times
                new = Lesson(id=str(uuid.uuid1()), lessonname=i[2], num=i[0], serial_num=i[1], teacher=i[5], lessontime=i[6], module=i[13], week=i[8], credit=i[4], note=i[9], score=0, score_times=0)
                session.add(new)
                new_l = new_l + f'新增：{new.num} ： {new.lessonname},{new.teacher};'
                cc_n += 1
        session.commit()
        session.close()
        return f'共修改{cc_u}条记录，新增{cc_n}条记录;' + new_l + up_l


class Notice(Base):
    __tablename__ = 'notices'
    id = Column(CHAR(length=37), primary_key=True, nullable=False, comment='公告id')
    title = Column(VARCHAR(length=30), nullable=False, comment='公告标题')
    pubdate = Column(DATETIME(), nullable=False, comment='发布时间')
    author_id = Column(CHAR(length=37), nullable=False, comment='作者id')
    content = Column(LONGTEXT(), nullable=False)
    sign = Column(VARCHAR(length=10), nullable=False)
    files = Column(LONGTEXT(), default='')

    def self_check(self, id):
        return (self.author_id == id)

    def init(self, id, title, pubdate, author_id, content, sign, files):
        self.id = id
        self.title = title
        self.pubdate = pubdate
        self.author_id = author_id
        self.files = files
        self.content = content
        self.sign = sign

    def get_attr_tuple(self):
        return (self.id, self.title, self.pubdate, self.author_id, self.content, self.sign, self.files)

    @staticmethod
    def new_notice(notice):
        notice.title=len_check(notice.title, 29)
        notice.sign=len_check(notice.sign, 9)
        session = sessionmaker(bind=engine)()
        session.add(notice)
        session.commit()
        session.close()

    @staticmethod
    def del_notice(id):
        session = sessionmaker(bind=engine)()
        t=session.query(Notice).filter(Notice.id == id).first()
        if(not t):return -1
        f=t.files
        if(f):
            f=f.split(',')
            if(f):
                for i in f:
                    if(i):
                        File.del_file(i)
        session.query(Notice).filter(Notice.id == id).delete()
        session.commit()
        session.close()

    @staticmethod
    def get_notice(id):
        session = sessionmaker(bind=engine)()
        result = session.query(Notice).filter(Notice.id == id).first()
        session.close()
        if(result):
            return result
        else:
            return 0

    @staticmethod
    def get_notice_count():
        session = sessionmaker(bind=engine)()
        result = session.query(Notice).count()
        session.close()
        return result

    @staticmethod
    def get_notice_10(pn):
        session = sessionmaker(bind=engine)()
        notices = session.query(Notice).all()
        amount = len(notices)
        result = []
        session.close()
        i = min((pn-1)*10,amount/10)
        if(amount >= 10*pn):
            i = 10*pn - 10
            while(i < 10*pn):
                result.append(notices[i])
                i += 1
            return result
        else:
            i = int(amount/10)*10
            while(i < amount):
                result.append(notices[i])
                i += 1
            return result

    @staticmethod
    def get_for_table(id, t='single'):
        session = sessionmaker(bind=engine)()
        if(t=='all'):
            result = session.query(Notice.id, Notice.title, User.nickname, Notice.sign, Notice.pubdate).outerjoin(User, User.id==Notice.author_id).distinct(Notice.id, Notice.title, User.nickname, Notice.sign, Notice.pubdate).all()
            session.close()
            return result
        result = session.query(Notice.id, Notice.title, User.nickname, Notice.sign, Notice.pubdate).outerjoin(User, User.id==Notice.author_id).filter(Notice.id == id).distinct(Notice.id, Notice.title, User.nickname, Notice.sign, Notice.pubdate).first()
        session.close()
        if(result):
            #id,课程号,课程名,任课老师,模块,评分
            return result
        return []
    
    @staticmethod
    def get_latest(num):
        session = sessionmaker(bind=engine)()
        all = session.query(Notice).count()
        num = min(all, num)
        noticel = list(session.query(Notice.title, Notice.content, Notice.pubdate, Notice.id).order_by(Notice.pubdate.desc()).limit(num).all())
        session.close()
        result = []

        for i in noticel:
            i = list(i)
            i[1] = str(i[1])[:50] + '……'
            result.append(i)

        return result
            

#搜索引擎
def search(query = 0, type='all', authority='norm'):
    #query搜索内容，type区分只搜索课程还是全局搜索，authority是否有权搜索用户
    result = {}
    tables = {'tags':[Tag.tag],'lessons':[Lesson.lessonname,Lesson.teacher,Lesson.module,Lesson.week,Lesson.note,Lesson.num],'assessments':[Assessment.content,Assessment.abstract],'articles':[Article.title,Article.keyword,Article.abstract,Article.content],'users':[User.nickname,User.realname,User.num,User.email],'notices':[Notice.title,Notice.content,Notice.sign]}
    id_map = {'tags':Tag.id,'lessons':Lesson.id,'assessments':Assessment.id,'articles':Article.id,'users':User.id,'notices':Notice.id}
    if(authority != 'root' and authority != 'admin'):
        tables['users'].remove(User.realname)
        tables['users'].remove(User.num)
        tables['users'].remove(User.email)
    #tables_natural = {'tags':['tag'],'lessons':['lessonname','teacher','module','week','note','num'],'assessments':['content','abstract'],'articles':['title','keyword','abstract','content'],'users':['nickname','realname'],'notices':['title','content','sign']}
    #tables_like = {'tags':['tag'],'lessons':['lessonname','teacher','module','week','note','num'],'assessments':['content','abstract'],'articles':['title','keyword','abstract','content'],'users':['nickname','realname','num','email'],'notices':['title','content','sign']}
    if(type != 'all'):
        if(type in tables):
            t = tables[type]
            tables = {}
            tables[type] = t
        else:return
    session = sessionmaker(bind=engine)()
    for key in tables:
        result[key] = []
        match = []
        for i in tables[key]:
            if(query):
                t = session.query(id_map[key]).filter(i.like(f'%{query}%')).all()
            else:
                t = session.query(id_map[key]).all()
            for i in t:
                match.extend(i)
        result[key].extend(match)
    session.close()

    for i in result:
        result[i] = list(OrderedDict.fromkeys(result[i]))

    return result

id_map = {'tags':Tag,'lessons':Lesson,'assessments':Assessment,'articles':Article,'users':User,'notices':Notice}
'''
a=session.query(User).all()
for i in a:
    print(i.id, i.realname, i.nickname)

tempu = Tag(tag='temp', art_id='cfb6b34a-3100-11ed-a38f-bc091babf751')
session.add(tempu)
session.commit()
print('commit')
'''
'''
data = {'art_id':DEFAULTUUID, 'tag':'temp0'}
a = session.query(Tag).filter(Tag.art_id == 'cfb6b34a-3100-11ed-a38f-bc091babf751').update(data)
session.commit()
print(a)
session.query(Tag).filter(Tag.tag == 'temp0').delete()
session.commit()
'''