from flask import Flask, render_template, redirect, url_for, request,session
import requests,bs4,re
from wtforms import Form, StringField, SelectField
from flask_session import Session
from threading import Thread
from multiprocess import Queue, Process, Pool, Manager
import numpy as np
app=Flask(__name__)
app.config['SESSION_PERMANENT']=False
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='thuhienluuthi'
@app.route('/')
def home():
    session['n']=None
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    error=None
    if request.method == 'POST':
        session['username']=request.form['username']
        session['password']=request.form['password']
        with requests.Session() as s:#Login khong dung selenium
            site=s.get('https://vinabiz.org/account/login')
            bs_content=bs4.BeautifulSoup(site.content,features="html.parser")
            token=bs_content.find('input',{'name':'__RequestVerificationToken'})['value']
            login_data={'email': session['username'],'password': session['password'],
                        'rememberMe': 'true','rememberMe': 'false',
                        '__RequestVerificationToken': token}
            s.post('https://vinabiz.org/account/login',data=login_data)
            if 'Tài khoản' in s.get('https://vinabiz.org').text:
                session['s']=s
                session['n']=1
                return redirect(url_for('search'))
            else:
                error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)
@app.route('/search', methods=['GET', 'POST'])
def search():
    error = None
    if request.method == 'POST':
        session['tinh']=request.form['tinh']
        session['quan']=request.form['quan']
        session['xa']=request.form['xa']
        session['nganhnghe']=request.form['nganhnghe']
        return redirect(url_for('searchpage'))
    return render_template('search.html')
def get_elems(url,s):
    res=s.get(url)
    soup=bs4.BeautifulSoup(res.text,features="html.parser")
    elems=soup.select('div a')
    return elems
def search_place(a,b,v):
    url_1=''
    for i in range(len(a)):
        if a[i].get('class')==v:
            if b.lower() in a[i].getText(' ').lower():
                url_1='https://vinabiz.org'+a[i].get('href')
                return url_1
def numPage(url_xa):
    res=requests.get(url_xa)
    soup=bs4.BeautifulSoup(res.text,features="html.parser")
    elems=soup.select('li a')
    regex=re.compile(r'1 of (\d+)')
    mo=regex.search(elems[15].getText())
    num=mo.group(1)
    return num
@app.route('/searchpage', methods=['GET', 'POST'])
def searchpage():
    error = None
    num=''
    url='https://vinabiz.org/categories/tinhthanh'
    v=['btn','btn-labeled', 'btn-default', 'btn-block']
    s=session.get('s')
    tinh=session['tinh']
    quan=session['quan']
    xa=session['xa']
    if s!=None:
    #tim tinh
    # elems_tinh
        elems_tinh=get_elems(url,s)
        url_tinh=search_place(elems_tinh,tinh,v) 
    #tim quan
        elems_quan=get_elems(url_tinh,s)
        url_quan=search_place(elems_quan,quan,v)    
    #tim xa
        elems_xa=get_elems(url_quan,s)
        url_xa=search_place(elems_xa,xa,v)    
    #tim so trang
        session['url_xa']=url_xa
        session['num']=numPage(url_xa)
        if request.method == 'POST':
            session['listPage']=request.form['listPage']
            return redirect(url_for('result'))
    else:
        error='Please login to see the result'
    return render_template('searchpage.html',num=session.get('num'),error=error)   
def content_page(y,url_xa,s,queue,c):#Get information
    content=queue.get()
    url_cty=url_xa+'/'+str(y)
    res=s.get(url_cty)
    soup=bs4.BeautifulSoup(res.text,features="html.parser")
    elems=soup.select('h4 a')
    for i in range (len(elems)):
        e=[]
        linkCompany='http://vinabiz.org'+elems[i].get('href')
        res1=s.get(linkCompany)
        soup1=bs4.BeautifulSoup(res1.text,features="html.parser")
        elems1=soup1.select('td')
        if 'NNT đang hoạt động (đã được cấp GCN ĐKT)' in elems1[14].getText():
            nganhnghe=elems1[48].getText().lstrip('\n').split(' ')
            for i in c:
                if i=='0':
                    break
                if i in nganhnghe:
                    e.append(i in nganhnghe)
            if len(e)>=len(c)-1 or e==[]: 
                c1=elems1[2].getText()+' - '+elems1[6].getText().lstrip(' \n')+' - '+elems1[12].getText()+' - '+elems1[48].getText().lstrip('\n')+' - '+'Phone: '+elems1[20].getText().lstrip('\n')+'\n' #Get phoneNum
                content.append(c1)
    queue.put(content)
def totalPage(listPage,num):
    totalPage=[]
    if listPage==[0,0]:
        totalPage=np.arange(1,num+1)
    else:
        for i in range(1,num+1):
            if i in listPage:
                totalPage.append(i)
    return totalPage
@app.route('/result',methods=['GET', 'POST'])
def result():
    error=None
    listPage='0'
    num=session.get('num')
    if session['n']!=None: 
        s=session.get('s')
        num=int(num)
        url_xa=session.get('url_xa')
        session['content']=[]
        c=session['nganhnghe'].split(' ')
        listPage=list(eval(listPage+','+session['listPage']))
        totalPage_=totalPage(listPage,num)
        m=Manager()
        q=m.Queue()
        q.put(session['content'])
        p={}
        for y in totalPage_:
            p[y]=Thread(target=content_page,args=(y,url_xa,s,q,c))
            p[y].start()
        for y in totalPage_:
            p[y].join()
        if not q.empty():
            session['content']=q.get()
    if session['n']==None:
        error='Nothing to see. Please login and search'
    if request.method == 'POST':
        returnObj=request.form['username'].lower()
        if returnObj=='yes':
            return redirect(url_for('search'))
    return render_template('content.html',content=session.get('content'),listPage=listPage,error=error,num=num)
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('password',None)
    session.pop('s',None)
    return redirect(url_for('home'))
if __name__=='__main__':
    app.run(debug=True)
