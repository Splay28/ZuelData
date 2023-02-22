# -*- coding: UTF-8 -*-
import json
import datasys
from util import *
import sqlalchemy.engine.row
import hashlib as hash

from flask import Flask, render_template, redirect, url_for, request, jsonify, session, send_file

from werkzeug.utils import secure_filename

from flask_login import LoginManager, current_user
from flask_login import logout_user, login_user, login_required

import uuid
from datetime import timedelta, date, datetime
import datetime
import os

from flask.json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):
  "Add support for serializing timedeltas"

  def default(self, o):
    if type(o) == sqlalchemy.engine.row.Row:
        return tuple(o)
    else:
        return super(CustomJSONEncoder, self).default(o)

'''
todo
1. 改密码的功能 √
2. 封号 √
3. 邀请注册 √
4. 验证码 √
5. 密码哈希 
7. 批量操作数据 √
    检查课表更新能力√
8. 检查用户数据更新 ×
9. 连接查询去除重复列 √
10. 法援数据聚合检索 √
11. 网盘 √
12. 最新公告 √
13. 更新诉讼部安排 √
14. 注册案件一览 √
15. 文件冗余（公告，博客 √
16. 网盘文件管理 √
16. 关于 √
'''

#用redis解决全局变量问题
app = Flask(__name__)  # 创建 Flask 应用

app.secret_key = 'moeka'  # 设置表单交互密钥
app.json_encoder = CustomJSONEncoder

login_manager = LoginManager()  # 实例化登录管理对象
login_manager.init_app(app)  # 初始化应用
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'  # 设置用户登录视图函数 endpoint

from globalv import *
'''
pwd_change_today= []
pwd_change_rege = []
pwd_salt = 'koizumimoekadaisuki'
verification_codes = {'user':'code'}
#检查每小时清空一次
tempfile_list = [datetime.datetime.today()]
verification_codes_random = [datetime.datetime.now().hour]
'''

match_id = r'"/user/base\?url=(.*?)"'
match_name = r'>(.*?)</a>'

filetypes = {
    "word":["doc","docx","docm","dot","dotx","dotm","rtf"],
    "powerpoint":["ppt","pptx","pptm","potx","potm","pot"],
    "excel":["xls","xlsx","xlsm","xlsb","csv"],
    "audio":["flac","wav","mp3","aac","ogg","mid","wma","m4a","midi"],
    "image":["webp","jpg","bmp","png","tif","gif","psd"],
    "video":["mp4","mpg","mkv","mpeg","3gp","webm","mov","wmv","flv","avi"],
    "archive":["7z","zip","rar","iso"],
    "pdf":["pdf"]
}
def filetype(extention):
    for i in filetypes:
        if(extention in filetypes[i]):
            return "-" + i
    return ""

#计算页数，默认一页十个，传入总数，请求页数，返回正确的请求页数
def pagenum(psum, pn, b=10):
    pmax = int((psum+b-1)/b)
    pn = max(1,pn)
    pn = min(pn,pmax)
    return pn

# 用户数据

@login_manager.user_loader  # 定义获取登录用户的方法
def load_user(user_id):
    if not request.endpoint:
        return None
    user = datasys.User.get(user_id)
    if(not user):return None
    if(user.authority == 'block'):
        return None
    return user

#登录程序
@app.route('/api/login',methods=['POST'])
def logoinform():
    data = json.loads(request.form.get('data'))
    emsg = None

    v = data['v'].upper()
    if(not exam(v, verification_codes_random)):
        return jsonify('验证码不正确')

    user_name = data['username']
    password = data['password']
    password = hash.md5((password + pwd_salt).encode()).hexdigest()
    remember = data['remember']
    user = datasys.get_user(user_name)
    if user is None:
        emsg = "用户名或密码密码有误"
    else:
        if(user.verify_password(password) and (user.authority != 'block')):
            login_user(user)
            #return redirect(request.args.get('next') or url_for('index'))
            emsg = "登录成功"
            if(remember == "on"):
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=7)
        elif(user.authority == 'block'):
            emsg = "账号已封禁"
        else:
            emsg = "用户名或密码密码有误"
    return jsonify(emsg)

@app.route('/api/regester', methods=['POST'])  # 注册
def regester():
    data = json.loads(request.form.get('data'))
    v = data['v_in_r'].upper()
    if(not exam(v, verification_codes_random)):
        return jsonify('验证码不正确')
    code = data['code']
    code = datasys.User.get_from_code(code, get_id=1)
    if(not code):return jsonify('邀请码不正确')
    email = data['email']
    e = datasys.User.search_same(datasys.User.email, email)
    if(e):return jsonify('邮箱已注册')
    nick = data['nick']
    e = datasys.User.search_same(datasys.User.nickname, nick)
    if(e):return jsonify('用户名重复')
    realname = data['realname']
    e = datasys.User.search_same(datasys.User.realname, realname)
    if(e):return jsonify('真实姓名已注册')
    num = data['num']
    e = datasys.User.search_same(datasys.User.realname, realname)
    if(e):return jsonify('学号已注册')
    pwd = data['pwd']
    pwd_c = data['pwd_c']
    if(pwd != pwd_c):return jsonify('两次输入密码不符')
    #用户结构：id，邮箱，昵称，密码，权限（root/admin/volunteer/norm/guest/block），真名，学号，周次（半角逗号隔开），部门，个签，是否部长（值为部门或0），是否组长， 邀请码
    new = datasys.User(id=str(uuid.uuid1()), email=email, nickname=nick, pwd=hash.md5((pwd + pwd_salt).encode()).hexdigest(), authority='norm', realname=realname, num=num, code=code)
    datasys.User.new_user(new)
    login_user(new)
    return jsonify('注册成功')

@app.route('/api/code')  # 邀请码
@login_required
def show_code():
    msg = current_user.generate_code() + ';每人的邀请码唯一确定，滥用邀请码或邀请用户的不规范行为可能导致邀请码提供者被封号'
    return render_template('alert_p.html', title='我的邀请码', msg=msg)

@app.route('/api/block' ,methods=['GET'])  # 封号
@login_required
def block():
    auth = current_user.authority
    if((auth != 'root') and (auth != 'admin')):return jsonify('无效操作，权限不足')
    id = request.args.get('user')
    t = request.args.get('type')
    l = []
    msg = ''
    if(t == 'all'):
        l = datasys.User.block(id, 'all')
        if(not l):return render_template('alert.html', msg='内容为空')
        for i in l:
            if(i):
                tm = ''
                for j in i:
                    tm = tm + j + '，'
                msg = msg + tm[:-1] + ';'
        return render_template('alert_p.html', title='关系串包含以下人员：', msg=msg[:-1])
    elif(t == 'single'):
        l = datasys.User.block(id, 'single')
        if(not l):return render_template('alert.html', msg='操作无效')
        for i in l[0]:
            msg = msg + i + '，'
        return render_template('alert_p.html', title='封禁成功', msg=msg[:-1])
    return render_template('alert.html', msg='操作无效')

@app.route('/api/unblock' ,methods=['GET'])  # 解封
@login_required
def unblock():
    auth = current_user.authority
    if((auth != 'root') and (auth != 'admin')):return jsonify('无效操作，权限不足')
    id = request.args.get('user')
    t = request.args.get('type')
    l = []
    msg = ''
    if(t == 'all'):
        l = datasys.User.unblock(id, 'all')
        for i in l:
            if(i):
                tm = ''
                for j in i:
                    tm = tm + j + ' , '
                msg = msg + tm[:-1] + ';'
        return render_template('alert_p.html', title='关系串包含以下人员', msg=msg[:-1])
    elif(t == 'single'):
        l = datasys.User.unblock(id, 'single')
        for i in l[0]:
            msg = msg + i
        return render_template('alert_p.html', title='解封成功', msg=msg)
    return render_template('alert.html', msg='操作无效')

@app.route('/api/change_pwd_request', methods=['POST'])  # 发送修改密码请求
def change_pwd_request():
    data = json.loads(request.form.get('data'))
    e = data['email']
    u = datasys.User.get_from_email(e)

    if(not exam(u.id,pwd_change_today)):
        url = 'https://www.zhongnandata.top/user/change_pwd?url=' + u.generate_pwd_code()
        url = '你正在尝试修改你在中南数据账号的密码，如果你没有进行上述操作，你的账号可能已经处于风险，请加强密码强度\n请点击以下链接修改密码：\n' + url
        email(u.email, '中南数据_修改密码', url, [], '', 0,free_u=1)
        push(u.id, pwd_change_rege)
    else:
        return jsonify('一天内只能修改一次密码')
    return jsonify('发送邮件成功')

@app.route('/user/change_pwd', methods=['GET'])  # 更改密码界面
def change_pwd_page():
    auth = request.args.get('url')
    u = datasys.User.get_from_pwd_code(auth)

    if(not exam(u.id, pwd_change_rege, pop=0)):
        return render_template('alert.html', msg='操作非法')
    return render_template('change_pwd.html', auth=auth, contact=datasys.User.get_contact())

@app.route('/login')  # 登录界面
def login():
    return render_template('login.html', contact=datasys.User.get_contact())
    
@app.route('/api/write_off',methods=['POST'])
def write_off():
    data = json.loads(request.form.get('data'))
    pwd = data['pwd']
    pwd = hash.md5((pwd + pwd_salt).encode()).hexdigest()
    if(current_user.id == data['id']):
        if(current_user.verify_password(pwd)):
            logout_user()
            datasys.User.del_user(data['id'])
            return jsonify('注销成功！')
    return jsonify("操作无效！")

@app.route('/')  # 首页
@app.route('/index')
@login_required  # 需要登录才能访问
def index():
    horo=current_user.get_horoscope()
    quotas=current_user.get_quota()
    return render_template('index.html', userlevel=current_user.authority, username=current_user.nickname, daynow=date.today().isoformat(), is_good=horo[0],
    horo1=horo[1][0][0], horo2=horo[1][1][0], horo3=horo[1][2][0], horo4=horo[1][3][0], 
    abs1=horo[1][0][1], abs2=horo[1][1][1], abs3=horo[1][2][1], abs4=horo[1][3][1], 
    quota=quotas[1], quota_author=quotas[2], userspace='/user/base?url='+current_user.id, posters=datasys.Lesson.get_for_poster(6), 
    notice=datasys.Notice.get_latest(2))

@app.route('/logout')  # 登出
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/api/checklevel', methods=['POST'])  # 检查权限
@login_required
def check_level():
    data = json.loads(request.form.get('data'))
    id = data['id']
    if(id):return jsonify(datasys.User.get(id).authority)
    return jsonify(current_user.authority)

@app.route('/api/change_pwd', methods=['POST'])  # 修改密码
def change_pwd():
    data = json.loads(request.form.get('data'))
    auth = data['auth']

    u = datasys.User.get_from_pwd_code(auth)
    if(not exam(u.id, pwd_change_rege)):
        return jsonify("操作非法")
    pwd = data['pwd']
    pwd = hash.md5((pwd + pwd_salt).encode()).hexdigest()
    datasys.User.update_user(id=u.id,pwd=pwd)

    push(u.id, pwd_change_today)
    email(u.email, '中南数据_修改密码', '你在中南数据的密码已修改\n希望上述行为是你本人的操作，如果是，请勿理会此邮件\n如果不是你本人操作，你的账号可能已经被盗，请迅速与系统管理员联系', [], '', 0,free_u=1)
    return jsonify("修改密码成功")

@app.route('/user/setting', methods=['GET'])  # 修改用户设置
@login_required
def user_setting_page():
    id = request.args.get("user", default=current_user.id)
    is_self=0
    if(id == current_user.id):is_self=1
    if(current_user.authority != 'root' and current_user.authority != 'admin' and (not is_self)):return render_template('alert.html', msg = "权限不足!")

    usr = datasys.User.get_user_id(id)
    if(not usr):return render_template('alert.html', msg = "用户不存在!")
    data = [id, usr.email, usr.nickname, usr.authority, usr.realname, usr.num, usr.signature]

    if(current_user.authority == 'root'):
        return render_template("user_setting.html", level='root', is_self=is_self, data=data)
    if(current_user.authority == 'admin'):
        return render_template("user_setting.html", level='admin', is_self=is_self, data=data)
    elif(id == current_user.id):
        return render_template("user_setting.html", level='norm', is_self=is_self, data=data)
@app.route('/api/user/setting', methods=['POST'])  # 修改用户设置
@login_required
def user_setting():
    #data = request.files.getlist("file")
    id = request.form.get("usr")
    if(current_user.authority != 'root' and current_user.authority != 'admin' and current_user.id != id):return render_template('alert.html', msg = "权限不足!")
    nick = request.form.get("nick")
    nick.replace('\n','。')
    nick.replace('\r','')
    name = request.form.get("name")
    email = request.form.get("email")
    num = request.form.get("num")
    authority = request.form.get("level")
    sig = request.form.get("sig")
    sig.replace('\n','。')
    sig.replace('\r','')

    #id, address, nickname, pwd, authority, name, num, signature
    if(current_user.authority == 'root'):
        datasys.User.update_user(id,0,0,0,authority,name,num,sig)
    elif(current_user.authority == 'admin'):
        datasys.User.update_user(id,0,0,0,0,name,num,sig,0,0)
    if(current_user.id == id):
        datasys.User.update_user(id,email,nick,0,0,0,0,sig,0,0)
    return render_template('alert.html', msg = "修改信息成功!")
@app.route('/user/base', methods=['GET'])
@login_required
def user_base():
    id = request.args.get("url", current_user.id)
    usr = datasys.User.get_user_id(id)
    if(not usr):return render_template('alert.html', msg="用户不存在...")
    blogs = datasys.Article.get_user_blog(id)
    ccb = blogs.pop(0)
    assessments = datasys.Assessment.get_user_assessment(id)
    cca = assessments.pop(0)
    tasks = datasys.Task.get_user_task(id)
    cct = tasks.pop(0)
    return render_template("user_space.html", usrname=usr.nickname, sig=usr.signature, blogs=blogs, ccb=ccb, assessments=assessments, cca=cca, isroot=current_user.authority, cct=cct, tasks=tasks, url="/user/setting?user="+id)

@app.route('/lesson/list')
@login_required
def lessonlist():
    data = datasys.search(0,'lessons',current_user.authority)
    result = {'lessons':[]}
    for i in data['lessons']:
        result['lessons'].append(datasys.Lesson.get_for_table(i))
    return render_template('search_list.html', data=result, type='lessons')
@app.route('/lesson/content',methods=['GET'])
def lessoncontent():
    id = request.args.get("url")
    data = datasys.Lesson.get_from_id(id)
    if(not data):return render_template('alert.html', msg="课程不存在...")
    result = {}
    #最后添加两个列表，同一课程的其他老师，同一老师的其他课程（不排除重名）
    t = datasys.Lesson.get_from_num(data.num)
    samenum = []
    for i in t:
        if(i.id == id):continue
        samenum.append([i.id,i.serial_num,i.teacher,i.lessontime])
    result['samenum'] = samenum

    t = datasys.Lesson.get_from_teacher(data.teacher)
    sameteacher = []
    for i in t:
        if(i.id == id):continue
        sameteacher.append([i.id,i.num,i.lessonname,i.lessontime])
    result['sameteacher'] = sameteacher

    timetable = datasys.Lesson.get_timetable(data.lessontime)

    assessments_t = datasys.Assessment.get_by_teacher_lessonnum(num=data.num)
    assessments = []
    for i in assessments_t:
        rich = 0
        if(i.content):rich=i.id
        nick = datasys.User.get_user_id(i.author_id)
        if(not nick):nick="用户已注销"
        else:nick=nick.nickname
        assessments.append([i.teacher,nick,i.pubdate,i.abstract,rich,i.content,i.author_id])

    scores = datasys.Assessment.get_by_teacher_lessonnum(teacher=data.teacher,num=data.num,score_only=1)

    return render_template('lesson_content.html', data=result, num=data.num, lessonname=data.lessonname, serial_num=data.serial_num,
                            timetable=timetable, assessments=assessments, teacher=data.teacher, module=data.module, scores=scores,
                            lessontime=data.lessontime, week=data.week, credit=data.credit, note=data.note, url=data.id, updatetime=data.updatetime)
#课程评价页面
@app.route('/assessment/publish',methods=['GET'])
@login_required
def uploadassessment_page():
    id = request.args.get("url")
    data = datasys.Lesson.get_from_id(id)
    if(not data):render_template('alert.html', msg="未找到课程...")
    if(datasys.Assessment.assessment_check(current_user.id, data.num)):return render_template('alert.html', msg="你已经评价过该课程！")
    return render_template('publish_assessment.html', url=data.id, name=data.lessonname, num=data.num, teacher=data.teacher)
#课程评价上传
@app.route('/api/upload/assessment',methods=['POST'])
@login_required
def upload_assessment():
    lesson_id = request.form.get("url")
    num = request.form.get("num")
    if(datasys.Assessment.assessment_check(current_user.id, num)):return render_template('alert.html', msg="你已经评价过该课程！")
    teacher = request.form.get("teacher")
    scoring_s = int(request.form.get("scoring_s"))
    useful_s = int(request.form.get("useful_s"))
    easy_s = int(request.form.get("easy_s"))
    if(not(lesson_id and num and teacher and scoring_s and useful_s and easy_s)):return render_template('alert.html', msg = "发布评价失败，检查你的内容...")
    assessed = datasys.Assessment.get_user_assessment(current_user.id,lesson_id_only=1)
    if(lesson_id in assessed):return render_template('alert.html', msg="你已经评价过该课程！")

    abstract = request.form.get("abstract")
    abstract.replace('\n','。')
    abstract.replace('\r','')
    content = request.form.get("content")
    if(not abstract):
        abstract=''
        content=''
    if(not content):content=''

    #id, lesson_id, pubdate, author_id, lesson_num, teacher, scoring, useful, easy, whole, content, abstract
    datasys.Assessment.new_assessment(datasys.Assessment(id=str(uuid.uuid1()), lesson_id=lesson_id, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
author_id=current_user.id, lesson_num=num, teacher=teacher, scoring=scoring_s, useful=useful_s, easy=easy_s, whole=int(scoring_s*0.2 + useful_s*0.4 + easy_s*0.4), content=content, abstract=abstract))
    return render_template('alert.html', msg = "发布评价成功!")
@app.route('/assessment/content',methods=['GET'])
@login_required
def assessment_content():
    url = request.args.get("url")
    data = datasys.Assessment.get_from_id(url)
    if(not data):return render_template("alert.html", msg="内容不存在...")
    num = data.lesson_num
    name = datasys.Lesson.get_from_id(data.lesson_id).lessonname
    teacher = data.teacher
    pubdate = data.pubdate
    scoring = data.scoring
    useful = data.useful
    easy = data.easy
    author = datasys.User.get_name(data.author_id)
    content = data.content   
    return render_template('assessment_content.html', name=name, num=num, pubdate=pubdate, teacher=teacher, author=author, content=content, scoring=scoring, useful=useful, easy=easy, abstract=data.abstract, auth=((current_user.authority == 'root') or (current_user.authority == 'admin') or (current_user.id == data.author_id)), url=url)

#验证码
@app.route('/api/v_code', methods=['POST','GET'])
def generate_v_code():
    t = getcode()
    id = request.form.get('id')
    check(verification_codes_random, 'hour')
    
    if((id == 'anonymous') or (not current_user.is_authenticated)):
        push(t[1].upper(), verification_codes_random, 'hour')
    else:
        verification_code_set(current_user.id, t[1].upper())

    return jsonify('data:image/png;base64,'+t[0])

#上传文件或写博客
@app.route('/blog/publish')
@login_required
def uploadblog_page():
    return render_template('publish_blog.html')
#博客上传
@app.route('/api/upload/blog',methods=['POST'])
@login_required
def upload_blog():
    v = request.form.get("v_in").upper()

    if((verification_code_get(current_user.id) != v)):
        return render_template('alert_p.html', title='验证码不正确', msg = "*注：错误的验证码会导致提交失败，直接后退回到本页面时，请重新上传图片内容（即使图片在编辑框中正常显示），否则图片会丢失")
    verification_code_set(current_user.id, 0)

    data = request.files.getlist("file")
    cover = request.files.getlist("cover")
    title = request.form.get("title")
    abstract = request.form.get("abstract")
    keyword = request.form.get("keyword")
    content = request.form.get("content")
    if(not(cover and title and abstract and keyword and content)):return render_template('alert_p.html', title = "内容空缺! ", msg = "*注：错误的验证码会导致提交失败，直接后退回到本页面时，请重新上传图片内容（即使图片在编辑框中正常显示），否则图片会丢失")
    files_input = ''
    coverid = 0
    abstract.replace('\n','。')
    abstract.replace('\r','')
    if(cover):
        if(cover[0].filename):
            coverid = str(uuid.uuid1()) + cover[0].filename[(cover[0].filename.rfind('.')):]
            cover[0].save(datasys.blog_cover_path + coverid)
            cover[0].close()
    if(data[0].filename):
        for i in data:
            id = str(uuid.uuid1())
            path = datasys.blog_file_path + id + '_' + secure_filename(i.filename)
            i.save(path)
            #new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_lawsuit', path=path, abstract='《' + title + '》案件下的文件'))
            datasys.File.new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_blog', path=path, abstract='《' + title + '》博客下的文件'))
            files_input += (id + ',')
            i.close()
            #datetime格式相当于字符串'2020-09-14 23:18:17'
            #id, title, pubdate, author_id, keyword, abstract, cover, content, files
        datasys.Article.new_blog(datasys.Article(id=str(uuid.uuid1()), title=title, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword=keyword, abstract=abstract, cover=coverid, content=content, files=files_input[:-1]))
    else:
        datasys.Article.new_blog(datasys.Article(id=str(uuid.uuid1()), title=title, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword=keyword, abstract=abstract, cover=coverid, content=content, files=''))
    return render_template('alert.html', msg = "发布博客成功!")
#博客
@app.route('/blog/page',methods=['GET'])
@login_required
def blog_page():
    psum = datasys.Article.get_blog_count()
    pn = request.args.get("pn", 1, type=int)
    psum = pagenum(psum,pn)

    result = []
    cc = 0
    blogs = datasys.Article.get_blog_10(pn)
    for i in blogs:
        result.append({})
        result[cc]['url'] = '/blog/content?url=' + i.id
        result[cc]['title'] = i.title
        result[cc]['sign'] = datasys.User.get_name(i.author_id)
        result[cc]['pubdate'] = i.pubdate
        result[cc]['abstract'] = i.abstract + '...'
        result[cc]['keyword'] = i.keyword
        result[cc]['cover'] = '/api/cover?url=' + i.cover

        cc += 1
    
    return render_template('page.html', psum=psum, content=result, count=cc, pn=pn, type='blog', title_type='博客')
@app.route('/blog/content',methods=['GET'])
def blog_content():
    url = request.args.get("url")
    data = datasys.Article.get_blog(url)
    if(not data):return render_template("alert.html", msg="内容不存在...")
    files = []
    title = data.title
    keyword = data.keyword
    pubdate = data.pubdate
    cover = data.cover
    author = datasys.User.get_name(data.author_id)
    content = data.content
    filecc = 0
    if(data.files):
        
        ids = data.files.split(',')
        for i in ids:
            if(i):
                result = {}
                f = datasys.File.get_file(i)
                if(not f):
                    files.append(0)
                    filecc += 1
                    continue
                result['url'] = i
                result['title'] = f.title
                result['type'] = filetype(f.title[(f.title.rfind('.')+1):])
                files.append(result)
                filecc += 1
    else:
        files.append(0)

    files.append({'cover':cover})
    is_self=0
    if(current_user.id == data.author_id):is_self=('/api/delete?type=blog&url=' + data.id)
    return render_template('blog_content.html', filecc=filecc, file=files, title=title, pubdate=pubdate, keyword=keyword, author=author, content=content, is_self=is_self)
@app.route('/api/cover',methods=['GET'])
def blog_cover():
    url = request.args.get("url")
    path = datasys.blog_cover_path + url
    return send_file(path)

@app.route('/api/random',methods=['POST']) #推荐博客
def random_content():
    data = json.loads(request.form.get('data'))
    art_list = datasys.random_content(data['type'], data['amount'])
    amount = len(art_list)
    #id,cover,abstract,title
    result = {}
    result['amount'] = amount
    result['data'] = []

    for i in art_list:
        result['data'].append({'id':i.id,'title':i.title,'abstract':i.abstract,'cover':i.cover})

    return jsonify(result)

@app.route('/api/random_pic')
def random_pic():
    path = datasys.File.get_random_file(datasys.random_pic_path)
    return send_file(path)

#公告
#公告对应的网址是公告id去掉连字符
@app.route('/notice/page',methods=['GET'])
@login_required
def notice_page():
    psum = datasys.Notice.get_notice_count()
    pn = request.args.get("pn", 1, type=int)
    psum = pagenum(psum,pn)

    result = []
    cc = 0
    notices = datasys.Notice.get_notice_10(pn)
    for i in notices:
        result.append({})
        result[cc]['url'] = '/notice/content?url=' + i.id
        result[cc]['title'] = i.title
        result[cc]['sign'] = i.sign
        result[cc]['pubdate'] = i.pubdate
        result[cc]['abstract'] = i.content[:300] + '...'

        cc += 1
    
    return render_template('page.html', psum=psum, content=result, count=cc, pn=pn, type='notice', title_type='公告')
@app.route('/notice/content',methods=['GET'])
def notice_content():
    url = request.args.get("url")
    data = datasys.Notice.get_notice(url)
    if(not data):return render_template("alert.html", msg="内容不存在...")
    files = []
    title = data.title
    sign = data.sign
    pubdate = data.pubdate
    author = datasys.User.get_name(data.author_id)
    content = data.content
    if(data.files):
        filecc = 0
        ids = data.files.split(',')
        for i in ids:
            if(i):
                result = {}
                f = datasys.File.get_file(i)
                result['url'] = i
                result['title'] = f.title
                result['type'] = filetype(f.title[(f.title.find('.')+1):])
                files.append(result)
                filecc += 1
    else:
        files.append(0)
    
    return render_template('notice_content.html', filecc=filecc, file=files, title=title, pubdate=pubdate, sign=sign, author=author, content=content)
@app.route('/notice/publish')
@login_required
def notice_publish_page():
    if(current_user.authority != 'root' and current_user.authority != 'admin'):return render_template('alert.html', msg = "权限不足!")
    return render_template('publish_notice.html')
@app.route('/api/upload/notice',methods=['POST'])
@login_required
def notice_publish():
    if(current_user.authority != 'root' and current_user.authority != 'admin'):return render_template('alert.html', msg = "权限不足!")
    data = request.files.getlist("file")
    title = request.form.get("title")
    sign = request.form.get("sign")
    content = request.form.get("content")
    if(not(title and sign and content)):return render_template('alert.html', msg = "内容空缺!")
    files_input = ''
    content.replace('\n','。')
    content.replace('\r','')
    if(data[0].filename):
        for i in data:
            id = str(uuid.uuid1())
            path = datasys.notice_file_path + id + '_' + secure_filename(i.filename)
            i.save(path)
            #new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_lawsuit', path=path, abstract='《' + title + '》案件下的文件'))
            datasys.File.new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_notice', path=path, abstract='《' + title + '》公告下的文件'))
            files_input += (id + ',')
            i.close()
            #datetime格式相当于字符串'2020-09-14 23:18:17'
            #id, title, pubdate, author_id, content, sign, files
            datasys.Notice.new_notice(datasys.Notice(id=str(uuid.uuid1()), title=title, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, content=content, sign=sign, files=files_input[:-1]))
    else:
        datasys.Notice.new_notice(datasys.Notice(id=str(uuid.uuid1()), title=title, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, content=content, sign=sign, files=''))
    return render_template('alert.html', msg = "发布公告成功!")

#待办内容
@app.route('/task/content',methods=['GET'])
@login_required
def task_content():
    url = request.args.get("url")
    data = datasys.Task.get_task(url)
    if(not data):return render_template("alert.html", msg="内容不存在...")
    files = []
    title = data.title
    subdate = data.subdate
    pubdate = data.pubdate
    status = data.status
    abstract = data.abstract
    quota = data.get_for_quota(url)
    from_to = datasys.Task.from_to(data.id)
    filecc = 0
    if(data.file):
        
        ids = data.file.split(',')
        for i in ids:
            if(i):
                result = {}
                f = datasys.File.get_file(i)
                result['url'] = i
                result['title'] = f.title
                result['type'] = filetype(f.title[(f.title.find('.')+1):])
                files.append(result)
                filecc += 1
    else:
        files.append(0)  
    return render_template('task_content.html', id=url, from_to=from_to, quota=quota, abstract=abstract, filecc=filecc, file=files, title=title, pubdate=pubdate, subdate=subdate, status=status)
#创建待办_网页
@app.route('/task/publish')
@login_required
def task_publish():
    if((current_user.authority == 'norm') or (current_user.authority == 'block')):return render_template('alert.html', msg='权限不足！')
    data={'from':[[current_user.id, current_user.realname, current_user.email]],
        'to':datasys.User.get_lawsuit_today(for_html=1)
        }
        #id,realname,email
    return render_template('publish_task.html', data=data, type='publish', quota=[])
#待办列表_网页
@app.route('/task/list')
@login_required
def task_list():
    if((current_user.authority == 'norm') or (current_user.authority == 'block')):return render_template('alert.html', msg='权限不足！')
    data=datasys.Task.get_for_table(0,'all')
        #id,realname,email
    return render_template('task_list.html', data=data)
#回复待办_网页
@app.route('/task/reply',methods=['GET'])
@login_required
def task_reply():
    url = request.args.get("url")
    from_to = datasys.Task.from_to(url)
    task = datasys.Task.get_task(url).get_attr_tuple()
    id_allow = []
    for i in from_to['from']:
        id_allow.append(i[0])
    for i in from_to['to']:
        id_allow.append(i[0])
    if(current_user.id not in id_allow):return render_template('alert.html', msg='办理人员错误')

    data={'from':from_to['to'],
        'to':from_to['from'],
        'quota':datasys.Task.get_for_quota(url, need_self=1),
        'task':task
        }
    
    if(task[8] == 'done'):return render_template('alert.html', msg='该任务已完成')

    return render_template('publish_task.html', data=data, type='reply')
#上传待审核文书，并推送给诉讼部，todo
@app.route('/api/task/publish',methods=['POST','GET'])
@login_required
def task_publish_api():
    flag_self = 0
    
    api_type = request.args.get('type')
    self_id = request.args.get('url')
    abstract = request.form.get("abstract")
    abstract.replace('\n','。')
    abstract.replace('\r','')
    title = request.form.get("title")
    email = request.form.get("email")
    if(not (title and abstract and email)):return render_template('alert.html', msg = "信息有误!")

    if(api_type == 'finish'):
        t=datasys.Task.get_task(self_id)
        if(t):
            t.finish(finish_all=1, abstract=abstract)
            return render_template('alert.html', msg = "结案成功!")
        else:
            return render_template('alert.html', msg = "结案失败!")
    else:
        data = request.files.getlist("file")
        
        quota_id = request.form.get("quota_id")
        to = request.form.get("to")
        if(not quota_id):quota_id=datasys.DEFAULTUUID
        
        #获取诉讼部成员
        #t=datasys.User.get_lawsuit_today()
        #to_id=t[0].id + ',' + t[1].id
        to_id=to
        to=to_id.split(',')
        if(current_user.id in to):flag_self = 1
        from_t=email.split(',')
        from_id=''
        for i in from_t:
            if(not i):break
            t=datasys.User.get_from_email(i)
            if(t==-1):return render_template('alert.html', msg = "信息有误!")
            t=t.id
            if(t == current_user.id):flag_self = 1
            from_id+=t
            from_id+=','
        from_id=from_id[:-1]

        if(not flag_self):return render_template('alert.html', msg = "信息有误!")

        task_id = str(uuid.uuid1())
        files_input = ''
        savepath = datasys.lawsuit_file_path + str(datetime.datetime.now().year) + '.' + str(datetime.datetime.now().month) + '/'

        if(data[0].filename):
            if(not os.path.isdir(savepath)):os.mkdir(savepath)
            for i in data:
                id = str(uuid.uuid1())
                path = savepath + id + '_' + secure_filename(i.filename)
                #id, title, pubdate, author_id, keyword, path, abstract
                i.save(path)
                datasys.File.new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_lawsuit', path=path, abstract='《' + title + '》案件下的文件'))
                files_input += (id + ',')
                i.close()
                #datetime格式相当于字符串'2020-09-14 23:18:17'
                #id, from_id, to_id, title, abstract, file, pubdate, subdate, status, quota_id
        
        pubdate = datetime.datetime.now()
        if(api_type == 'reply'):
            t=datasys.Task.get_task(self_id)
            #from_id, to_id, abstract, file, pubdate, subdate
            a=t.reply(from_id=from_id, to_id=to_id, abstract=abstract, file=files_input[:-1], pubdate=pubdate.strftime("%Y-%m-%d %H:%M:%S"), subdate=(pubdate+datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"))
            if(a==-1):return render_template('alert.html', msg = "回复失败!")
            else:return render_template('alert.html', msg = "回复成功!")
        else:
            a=datasys.Task.new_task(datasys.Task(id=task_id, from_id=from_id, to_id=to_id, title=title, abstract=abstract, file=files_input[:-1], pubdate=pubdate.strftime("%Y-%m-%d %H:%M:%S"), subdate=(pubdate+datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), status='to-do', quota_id=datasys.DEFAULTUUID))
            if(a==-1):return render_template('alert.html', msg = "发布任务失败!")
            return render_template('alert.html', msg = "发布任务成功!") 

@app.route('/arrangement')
@login_required
def arrange_change_page():
    f = open(datasys.arrange_path + "lawsuit_department.dat",'r',encoding='utf-8')
    lawsuit_department = f.read()
    f.close()
    #lawsuit_department = "1_id,2_id;3_id,4_id;5_id,6_id;7_id,8_id;9_id,10_id;11_id,12_id;13_id,14_id"
    lawsuit_department = lawsuit_department.split(";")
    lawsuit = []
    for i in lawsuit_department:
        temp = i.split(',')
        temp1 = []
        for j in temp:
            temp1.append(j.split('_'))
        lawsuit.append(temp1)

    level = current_user.authority

    return render_template("arrangement_change.html" , lawsuit=lawsuit, member=datasys.User.get_volunteer(), level=level, curid=current_user.id)

#下载文件
@app.route('/api/download/file',methods=['GET'])
def downloadfile():
    id = request.args.get("url")

    templates = ['general.pdf', 'lessontable.xls', 'arrange.xls', 'horo.xls', 'quota.xls', 'lawsuit.xls']
    if(id in templates):
        if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
            return render_template('alert.html', msg='权限不足')
        return send_file(datasys.File.get_template(id), as_attachment=True)

    file = datasys.File.get_file(id)
    if(not file):return render_template('alert.html', msg='文件不存在！')
    if(file.keyword[:1] != '_'):
        if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
            return render_template('alert.html', msg='权限不足')
    path = file.path
    return send_file(path, as_attachment=True, download_name=file.title)

#下载文件列表
@app.route('/api/download/list',methods=['POST'])
@login_required
def downloadlist():
    if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
        return render_template('alert.html', msg='权限不足')
    
    idlist = json.loads(request.form.get('urllist'))
    query = request.form.get('query')
    
    if(indexlist(0, tempfile_list) != datetime.datetime.today()):
        file_to_del = getlist(tempfile_list)[1:]
        for i in file_to_del:
            os.remove(i)
        check(tempfile_list)

    file = datasys.File.get_zip(idlist)
    
    if(not file):return render_template('alert.html', msg='文件不存在！')
    push(file, tempfile_list)

    return send_file(file, as_attachment=True, download_name=f'_{query}_的搜索结果.zip', mimetype='application/zip')

@app.route('/api/search',methods=['post'])
@login_required
def searchlist():
    query = request.form.get('query')

    if(not query):return redirect("/search")

    data = datasys.search(query,type='all',authority=current_user.authority)
    result = {'lessons':[],'articles':[],'notices':[]}
    for i in data['lessons']:
        result['lessons'].append(datasys.Lesson.get_for_table(i))
    for i in data['articles']:
        result['articles'].append(datasys.Article.get_for_table(i))
    for i in data['notices']:
        result['notices'].append(datasys.Notice.get_for_table(i))
    return render_template('search_list.html', data=result, type='all')
@app.route('/search')
@login_required
def searchpage():
    return render_template('search_list.html', data=-1)

@app.route('/backstage')
@login_required
def backstage_page():
    if((current_user.authority != 'root') and (current_user.authority != 'admin')):return render_template('alert.html', msg = "权限不足!")

    result = {'lessons':[],'articles':[],'notices':[],'users':[],'assessments':[],'files':[],'tip_l':[],'tip_a':[]}
    i=0
    result['lessons'].extend(datasys.Lesson.get_for_table(i ,t='all'))
    result['articles'].extend(datasys.Article.get_for_table(i ,t='all'))
    result['notices'].extend(datasys.Notice.get_for_table(i ,t='all'))
    result['users'].extend(datasys.User.get_for_table(i ,t='all'))
    result['assessments'].extend(datasys.Assessment.get_for_table(i ,t='all'))
    result['files'].extend(datasys.File.get_netdisk('netdisk'))

    tipl0={'url':'lessontable.xls','title':'选课汇总表_示例.xls','type':'excel'}
    tipl1={'url':'general.pdf','title':'通识教育课程一览表_示例.pdf','type':'pdf'}
    result['tip_l'].append(tipl0)
    result['tip_l'].append(tipl1)

    return render_template('backstage_setting.html', data=result)

#删除
@app.route('/api/delete',methods=['GET'])
@login_required
def delete_api():
    id = request.args.get("url")
    type = request.args.get("type")
    if(type == 'blog'):
        t = datasys.Article.get_blog(id)
        if(t):
            if(t.self_check(current_user.id) or (current_user.authority == "root") or (current_user.authority == "admin")):
                datasys.Article.del_blog(id)
                return render_template('alert.html', msg = "删除博客成功!")
    elif(type == 'notice'):
        t = datasys.Notice.get_notice(id)
        if(t):
            if((current_user.authority == "root") or (current_user.authority == "admin")):
                datasys.Notice.del_notice(id)
                return render_template('alert.html', msg = "删除公告成功!")
    elif(type == 'assessment'):
        t = datasys.Assessment.get_from_id(id)
        if(t):
            if((t.self_check(current_user.id) or current_user.authority == "root") or (current_user.authority == "admin")):
                datasys.Assessment.del_assessment(id)
                return render_template('alert.html', msg = "删除评价成功!")
    elif(type == 'user'):
        t = datasys.User.get(id)
        if(t):
            if((t.self_check(current_user.id) or current_user.authority == "root")):
                datasys.User.del_user(id)
                return render_template('alert.html', msg = "删除用户成功!")
    elif(type == 'lesson'):
        t = datasys.Lesson.get_from_id(id)
        if(t):
            if(current_user.authority == "root"):
                datasys.Lesson.del_lesson(id)
                return render_template('alert.html', msg = "删除课程成功!")
    elif(type == 'file'):
        t = datasys.File.get_file(id)
        if(t):
            if((current_user.authority == "root") or (current_user.authority == "admin")):
                datasys.File.del_file(id)
                return render_template('alert.html', msg = "删除文件成功!")

    return render_template('alert.html', msg = "操作无效!")

#更新数据
@app.route('/api/upload/lesson',methods=['POST'])
@login_required
def upload_lesson():
    if(current_user.authority != 'root'):return render_template('alert.html', msg='权限不足！')
    xls = request.files.get("xls")
    pdf = request.files.get("pdf")
    if((not xls.filename) or (not pdf.filename)):return render_template('alert.html', msg='缺少文件')
    
    path_x = datasys.data_file_path + '_' + secure_filename(xls.filename)
    xls.save(path_x)
    xls.close()

    path_p = datasys.data_file_path + '_' + secure_filename(pdf.filename)
    pdf.save(path_p)
    pdf.close()
    l = mix(path_x, path_p)

    t = datasys.Lesson.batch_update(l)
    os.remove(path_x)
    os.remove(path_p)
    
    if(t==-1):
        return render_template('alert.html', msg='权限不足！')
    else:
        return render_template('alert_p.html', title='更新成功', msg=t)

#更新人员
@app.route('/api/upload/arrange',methods=['POST'])
@login_required
def upload_arrange():
    if(current_user.authority != 'root'):return render_template('alert.html', msg='权限不足！')
    xls = request.files.get("xls")
    if(not xls.filename):return render_template('alert.html', msg='缺少文件')
    
    path_x = datasys.data_file_path + '_' + secure_filename(xls.filename)
    xls.save(path_x)
    xls.close()

    l = read_arrange(path_x)

    t = datasys.User.batch_update(l)

    os.remove(path_x)
    
    if(t==-1):
        return render_template('alert.html', msg='权限不足！')
    else:
        return render_template('alert.html', msg=f'更新成功，共修改{str(t)}条记录！')
    
#更新黄历
@app.route('/api/upload/horo',methods=['POST'])
@login_required
def upload_horo():
    if((current_user.authority != 'root') and (current_user.authority != 'admin')):return render_template('alert.html', msg='权限不足！')
    xls = request.files.get("xls")
    if(not xls.filename):return render_template('alert.html', msg='缺少文件')
    
    path_x = datasys.data_file_path + '_' + secure_filename(xls.filename)
    xls.save(path_x)
    xls.close()

    l = read_horo(path_x)

    t = datasys.Horoscope.batch_update(l)

    os.remove(path_x)
    
    if(t==-1):
        return render_template('alert.html', msg='权限不足！')
    else:
        return render_template('alert.html', msg=f'更新成功，共修改{str(t)}条记录！')
    
#更新名人名言
@app.route('/api/upload/quota',methods=['POST'])
@login_required
def upload_quota():
    if((current_user.authority != 'root') and (current_user.authority != 'admin')):return render_template('alert.html', msg='权限不足！')
    xls = request.files.get("xls")
    if(not xls.filename):return render_template('alert.html', msg='缺少文件')
    
    path_x = datasys.data_file_path + '_' + secure_filename(xls.filename)
    xls.save(path_x)
    xls.close()

    l = read_quota(path_x)

    t = datasys.Quota.batch_update(l)

    os.remove(path_x)
    
    if(t==-1):
        return render_template('alert.html', msg='权限不足！')
    else:
        return render_template('alert.html', msg=f'更新成功，共修改{str(t)}条记录！')

#更新横幅图片
@app.route('/api/upload/image',methods=['POST'])
@login_required
def upload_image():
    if((current_user.authority != 'root') and (current_user.authority != 'admin')):return render_template('alert.html', msg='权限不足！')

    data = request.files.getlist("file")
    cc = 0

    if(data[0].filename):
        for i in data:
            id = str(uuid.uuid1()) + i.filename[(i.filename.rfind('.')):]
            i.save(datasys.random_pic_path + id)
            i.close()
            cc+=1
    else:return render_template('alert.html', msg='缺少文件')

    return render_template('alert.html', msg=f'更新成功，共修改{str(cc)}条记录！')

#更新诉讼部值班表
@app.route('/api/upload/lawsuit',methods=['POST'])
@login_required
def upload_lawsuit():
    if(current_user.authority != 'root'):return render_template('alert.html', msg='权限不足！')
    xls = request.files.get("xls")
    if(not xls.filename):return render_template('alert.html', msg='缺少文件')
    
    path_x = datasys.data_file_path + '_' + secure_filename(xls.filename)
    xls.save(path_x)
    xls.close()

    l = read_lawsuit(path_x)
    l2 = []
    for i in l:
        u1 = datasys.User.get_from_email(i[1])
        u2 = datasys.User.get_from_email(i[3])
        l2.append([(str(u1.realname) + '_' + str(u1.id)), (str(u2.realname) + '_' + str(u2.id))])

    t = datasys.User.update_lawsuit(l2)

    os.remove(path_x)
    
    if(t==-1):
        return render_template('alert.html', msg='权限不足！')
    else:
        return render_template('alert.html', msg=f'更新成功，共修改{str(t)}条记录！')

@app.route('/elements')
def element():
    return render_template('elements.html')

@app.route('/about')
def generic():
    return render_template('about.html')

#网盘
@app.route('/netdisk')
@login_required
def netdisk():
    t = request.args.get('type')
    if(not t):t = 'netdisk'
    q = request.args.get('query')
    if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
        return render_template('alert.html', msg='权限不足')

    data = datasys.File.get_netdisk(t,q)
    return render_template('netdisk.html', data=data, type=t, query=q)

#网盘上传文件
@app.route('/netdisk/upload')
@login_required
def uploadfile_page():
    if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
        return render_template('alert.html', msg='权限不足')

    return render_template('netdisk_upload.html')

#清理文件数据库冗余
@app.route('/api/clear_redundancy')
@login_required
def clear_redundancy():
    if((current_user.authority != 'root') and (current_user.authority != 'admin')):
        return render_template('alert.html', msg='权限不足')

    return render_template('alert_p.html', title='清除成功！', msg=datasys.File.clear_redundancy())

#网盘文件上传
@app.route('/api/upload/file',methods=['POST'])
@login_required
def upload_file():
    v = request.form.get("v_in").upper()

    if(verification_code_get(current_user.id) != v):
        return render_template('alert_p.html', title='验证码不正确', msg = "*注：错误的验证码会导致提交失败，直接后退回到本页面时，请重新上传文件")
    verification_code_set(current_user.id)

    if((current_user.authority != 'root') and (current_user.authority != 'admin') and (current_user.authority != 'volunteer')):
        return render_template('alert.html', msg='权限不足')

    data = request.files.getlist("file")
    abstract = request.form.get("abstract")
    abstract.replace('\n','。')
    abstract.replace('\r','')
    keyword = request.form.get("keyword")

    if(not(abstract and keyword)):return render_template('alert.html', msg = "内容空缺!")

    if(data[0].filename):
        for i in data:
            id = str(uuid.uuid1())
            path = datasys.netdisk_path + id + '_' + secure_filename(i.filename)
            i.save(path)
            #new_file(datasys.File(id=id, title=i.filename, pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword='_lawsuit', path=path, abstract='《' + title + '》案件下的文件'))
            datasys.File.new_file(datasys.File(id=id, title=secure_filename(i.filename), pubdate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), author_id=current_user.id, keyword=keyword, path=path, abstract=abstract))
            i.close()
            #datetime格式相当于字符串'2020-09-14 23:18:17'
            #id, title, pubdate, author_id, keyword, abstract, cover, content, files

    return render_template('alert.html', msg = "上传文件成功!")

if __name__ == '__main__':
    #app.run(debug=False, host='0.0.0.0', port=443, ssl_context=('zhongnandata.top_bundle.pem','zhongnandata.top.key')) 
    # 运行这个flask项目
    app.run(debug=False, host='0.0.0.0', port=8080)
    #http_server = HTTPServer(WSGIContainer(app))
    #http_server.listen(5000)  #flask默认的端口
    print('run...')
    #IOLoop.current().start()
