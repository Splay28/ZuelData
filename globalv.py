import datetime

global pwd_change_today
pwd_change_today = []
global pwd_change_rege
pwd_change_rege = []
global pwd_today
pwd_today = [datetime.datetime.today()]
global pwd_salt
pwd_salt = 'koizumimoekadaisuki'
global verification_codes
verification_codes = {'user':'code'}
#检查每小时清空一次
global tempfile_list
tempfile_list = [datetime.datetime.today()]
global verification_codes_random
verification_codes_random = [datetime.datetime.now().hour]

global match_id
match_id = r'"/user/base\?url=(.*?)"'
global match_name
match_name = r'>(.*?)</a>'