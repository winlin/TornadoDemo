#!/usr/bin/env python
## -*- coding: utf-8 -*-
import os
import tornado.ioloop
import tornado.web
from tornado import httpclient
from tornado.web import RequestHandler
import subprocess 
import tornado.gen
from shutil import copyfile

root = os.path.dirname(__file__)
template_root = os.path.join(root, 'templates')
blacklist_templates = ('layouts',)

####################################################
# self-definate handler

class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class LoginHandler(BaseHandler):
    def get(self):
        self.render('templates/login.html')

    def post(self):
        if self.get_argument("password") == '1234.asd':
            self.set_secure_cookie("user", self.get_argument("username"))
            self.redirect("/")
            return
        return self.write('<html><script type="text/javascript">alert("密码错误");</script></html>')

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if not self.current_user:
            self.redirect("templates/login.html")
            return
        user_name = tornado.escape.xhtml_escape(self.current_user)
        print 'current user:%s' % user_name
        self.render('templates/upload_db.html')


class ResultHandler(BaseHandler):
    @tornado.web.authenticated
    def initialize(self, message):
        self.message = message

    def get(self):
        self.render('templates/result.html', message=self.message)

class UpdateCodeHandler(BaseHandler):
    @tornado.web.authenticated
    def do_codeupdate(self):
        # shutdown the cxxt service
        result = subprocess.call('cd /home/cycle/cxxt && /bin/bash main.sh stop', shell=True)
        if result != 0:
            print 'do_codeupdate  main.sh stop result=%d' % result
            return result
        # replace the cxxt db
        result = subprocess.call('cd /home/cycle/cxxt && git pull origin develop', shell=True)
        if result != 0:
            print 'do_codeupdate  git pull result=%d' % result
            return result
        # start the cxxt service 
        result = subprocess.call('cd /home/cycle/cxxt && /bin/bash main.sh start', shell=True)
        print 'do_codeupdate  main.sh start result=%d' % result
        return result

    def post(self):
        ret = self.do_codeupdate()
        if ret:
            self.write('<html><script type="text/javascript">alert("代码更新失败");</script></html>')
        else:
            self.write('<html><script type="text/javascript">alert("代码更新成功");</script></html>')


class UploadDBHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('templates/upload_db.html');

    def do_dbdeploy(self):
        if 'db_file' not in self.request.files:
            print 'DB file is empty'
            return 1

        file_dict = self.request.files['db_file'][0]
        file_name = file_dict['filename']
        cont_type = file_dict['content_type']
        print 'Get File Name:%s   Content Type: %s' % (file_name, cont_type)
        # save the db file
        fh = open('dbfiles/server.db', 'w')
        fh.write(file_dict['body'])
        fh.close()   

        # shutdown the cxxt service
        result = subprocess.call('cd /home/cycle/cxxt && /bin/bash main.sh stop', shell=True)
        if result != 0:
            print 'do_codeupdate  main.sh stop result=%d' % result
            return result
        # replace the cxxt db and delete the tmp db file
        try:
            copyfile('dbfiles/server.db', '/dev/shm/server.db')
        except IOError, e:
            print 'do_codeupdate  copyfile failed:', e
            return 1
    
        result = subprocess.call('rm -rf dbfiles/server.db', shell=True)
        if result != 0:
            print 'do_codeupdate  rm db files result=%d' % result
            return result        # start the cxxt service 
        result = subprocess.call('cd /home/cycle/cxxt && /bin/bash main.sh start', shell=True)
        print 'do_dbdeploy  main.sh start result=%d' % result
        return result
        

    def post(self):
        ret = self.do_dbdeploy()
        if ret:
            self.write('<html><script type="text/javascript">alert("DB升级失败");</script></html>')
        else:
            self.write('<html><script type="text/javascript">alert("DB升级成功");</script></html>')

# self-definate handler
####################################################
settings = {
    "cookie_secret": "61oETzKXQAGaYdkLAGSDFAWEJJFuYh7EQnp2XdTP1o/Vo=",
    "login_url": "/login",
    "debug": True, 
    "static_path": os.path.join(root, 'static'), 
    # "xsrf_cookies": True,
}

application = tornado.web.Application([
    (r'^/$', MainHandler),
    (r'^/login$', LoginHandler),
    (r'^/update_code$', UpdateCodeHandler),
    (r'^/result$', ResultHandler, dict(message="Uplaod Success")),
    (r'^/upload_db$', UploadDBHandler),
], **settings)

if __name__ == '__main__':
    application.listen(12345)
    tornado.ioloop.IOLoop.instance().start()
