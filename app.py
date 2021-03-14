from flask import Flask, render_template, redirect, url_for, request,session
import requests,bs4
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
        session['page1']=request.form['page1']
        session['page2']=request.form['page2']
        session['listPage']=request.form['listPage']
        return redirect(url_for('result'))
    return render_template('search.html')
@app.route('/result',methods=['GET', 'POST'])
def result():
    content=[]
    error=None
    s=session.get('s')
    tinh=session['tinh']
    quan=session['quan']
    xa=session['xa']
    page1=session['page1']
    page2=session['page2']
    listPage=session['listPage']+',0'
    listPage=list(eval(listPage))
    if s!=None:
        for y in range(int(page1),int(page2)+1):#Get information
            if y in listPage:
                pass
            else:
                    url='https://vinabiz.org/company/'+str(y)
                    res=s.get(url)
                    soup=bs4.BeautifulSoup(res.text,features="html.parser")
                    elems=soup.select('h4 a')
                    for i in range(len(elems)):
                        linkCompany='http://vinabiz.org'+elems[i].get('href')
                        res1=s.get(linkCompany)
                        soup1=bs4.BeautifulSoup(res1.text,features="html.parser")
                        elems1=soup1.select('td')
                        if elems1[20].getText()!='\n':
                            c2=elems1[2].getText()+' - '+elems1[6].getText().lstrip(' \n')+' - '+elems1[12].getText()+' - '+elems1[48].getText().lstrip('\n')+' - '+'Phone: '+elems1[20].getText().lstrip('\n') #Get phoneNum
                        else:
                            c2=elems1[2].getText()+' - '+elems1[6].getText().lstrip(' \n')+' - '+elems1[12].getText()+' - '+elems1[48].getText().lstrip('\n')+'Phone: 0'
                        if tinh==''and quan=='' and xa=='':
                            content.append(c2)
                        if quan!='' and xa!='' and tinh!='':
                            if tinh.lower() and quan.lower() and xa.lower() in elems1[18].getText().lstrip('\n').lower():
                                content.append(c2)
                        if xa==''and quan!='' and tinh!='':
                            if tinh.lower() and quan.lower() in elems1[18].getText().lstrip('\n').lower():
                                content.append(c2)
                        if xa=='' and quan =='' and tinh!='':
                            if tinh.lower() in elems1[18].getText().lstrip('\n').lower():
                                content.append(c2)
    else:
        error='Please login to see the result'
    if request.method == 'POST':
        returnObj=request.form['username'].lower()
        if returnObj=='yes':
            return redirect(url_for('search'))
    return render_template('content.html',content=content,error=error,listPage=listPage)
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('password',None)
    session.pop('s',None)
    return redirect(url_for('home'))
if __name__=='__main__':
    app.run(debug=True)
