from flask import Flask, render_template, redirect, url_for, request,session
import requests,bs4,re
from wtforms import Form, StringField, SelectField
from flask_session import Session
app=Flask(__name__)
app.config['SESSION_PERMANENT']=False
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='thuhienluuthi'
@app.route('/')
def home():
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
            session['s']=s
            if 'Tài khoản' in s.get('https://vinabiz.org').text:
                session['s']=s
                return redirect(url_for('home'))
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
        return redirect(url_for('searchpage'))
    return render_template('search.html')
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
        res_tinh=s.get(url)
        soup_tinh=bs4.BeautifulSoup(res_tinh.text,features="html.parser")
        elems_tinh=soup_tinh.select('div a')
    # url_tinh=search_place(elems_tinh,tinh,v)
        for x in range(len(elems_tinh)):
            if elems_tinh[x].get('class')==v:
                if tinh.lower() in elems_tinh[x].getText(' ').lower():
                    url_tinh='https://vinabiz.org'+elems_tinh[x].get('href')
                    break
    #tim quan
    # elems_quan
        res_quan=s.get(url_tinh)
        soup_quan=bs4.BeautifulSoup(res_quan.text,features="html.parser")
        elems_quan=soup_quan.select('div a')
    # url_quan=search_place(elems_quan,quan,v)
        for y in range(len(elems_quan)):
            if elems_quan[y].get('class')==v:
                if quan.lower() in elems_quan[y].getText(' ').lower():
                    url_quan='https://vinabiz.org'+elems_quan[y].get('href')
                    break
    #tim xa
    # elems_xa
        res_xa=s.get(url_quan)
        soup_xa=bs4.BeautifulSoup(res_xa.text,features="html.parser")
        elems_xa=soup_xa.select('div a')
    # url_xa=search_place(elems_xa,xa,v)
        for z in range(len(elems_xa)):
            if elems_xa[z].get('class')==v:
                if xa.lower() in elems_xa[z].getText(' ').lower():
                    session['url_xa']='https://vinabiz.org'+elems_xa[z].get('href')
                    break
    #tim so trang
        url_xa=session.get('url_xa')
        res=requests.get(url_xa)
        soup=bs4.BeautifulSoup(res.text,features="html.parser")
        elems=soup.select('li a')
        regex=re.compile(r'1 of (\d+)')
        mo=regex.search(elems[15].getText())
        session['num']=mo.group(1)
        if request.method == 'POST':
            session['listPage']=request.form['listPage']
            return redirect(url_for('result'))
    else:
        error='Please login to see the result'
    return render_template('searchpage.html',num=session['num'],error=error)   
@app.route('/result',methods=['GET', 'POST'])
def result():
    content=[]
    error=None
    s=session.get('s')
    url_xa=session.get('url_xa')
    listPage=session['listPage']+',0'
    listPage=list(eval(listPage))
    num=int(session.get('num'))
    if s!=None:
        for y in range(1,num+1):#Get information
            if y in listPage:
                url_cty=url_xa+'/'+str(y)
                res=s.get(url_cty)
                soup=bs4.BeautifulSoup(res.text,features="html.parser")
                elems=soup.select('h4 a')
                for i in range(len(elems)):
                    linkCompany='http://vinabiz.org'+elems[i].get('href')
                    res1=s.get(linkCompany)
                    soup1=bs4.BeautifulSoup(res1.text,features="html.parser")
                    elems1=soup1.select('td')
                    if 'NNT đang hoạt động (đã được cấp GCN ĐKT)' in elems1[14].getText():
                        if elems1[20].getText()!='\n':
                            c1=elems1[2].getText()+' - '+elems1[6].getText().lstrip(' \n')+' - '+elems1[12].getText()+' - '+elems1[48].getText().lstrip('\n')+' - '+'Phone: '+elems1[20].getText().lstrip('\n') #Get phoneNum
                            content.append(c1)
                        else:
                            c1=elems1[2].getText()+' - '+elems1[6].getText().lstrip(' \n')+' - '+elems1[12].getText()+' - '+elems1[48].getText().lstrip('\n')+' - '+'Phone: 0'
                            content.append(c1)
                else:
                    pass
    else:
        error='Nothing to see. Please login and search'
    if request.method == 'POST':
        returnObj=request.form['username'].lower()
        if returnObj=='yes':
            return redirect(url_for('search'))
    return render_template('content.html',content=content,listPage=listPage,error=error,num=int(session.get('num')))
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('password',None)
    session.pop('s',None)
    return redirect(url_for('home'))
if __name__=='__main__':
    app.run(debug=True)
