"""Command Ready Training Academy independent-platform pilot. Not production-ready."""
import os, json, sqlite3, secrets, hashlib, time, re, sys
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

BASE=Path(__file__).resolve().parent
DB=Path(os.environ.get('COMMAND_READY_DB_PATH',str(BASE/'data'/'academy.sqlite3')))
COURSE=json.loads((BASE/'data'/'course.json').read_text())
PH=PasswordHasher()
app=FastAPI(title='Command Ready Training Academy - Pilot')
# Only expose the original account interface after a separate production security review.
if os.environ.get('COMMAND_READY_PREVIEW_MODE', '1') != '1':
    app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

@app.middleware('http')
async def preview_guard(request: Request, call_next):
    if os.environ.get('COMMAND_READY_PREVIEW_MODE', '1') == '1' and request.url.path != '/':
        return JSONResponse({'detail': 'Unavailable in public preview mode'}, status_code=404)
    return await call_next(request)


@contextmanager
def db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=15)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try: yield c; c.commit()
    finally: c.close()

def init():
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('officer','admin')), active INTEGER NOT NULL DEFAULT 1, must_change_password INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS progress(user_id INTEGER NOT NULL REFERENCES users(id), module INTEGER NOT NULL, completed_at TEXT NOT NULL, PRIMARY KEY(user_id,module));
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), started_at TEXT NOT NULL, submitted_at TEXT, score INTEGER, total INTEGER, answers TEXT, question_order TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor_id INTEGER, action TEXT NOT NULL, target TEXT, at TEXT NOT NULL);''')
if os.environ.get('COMMAND_READY_PREVIEW_MODE', '1') != '1':
    init()

def now(): return datetime.now(timezone.utc).isoformat()
def audit(c,uid,action,target=''):c.execute('INSERT INTO audit(actor_id,action,target,at) VALUES(?,?,?,?)',(uid,action,str(target),now()))
def username_ok(x):return bool(re.fullmatch(r'[a-zA-Z0-9._-]{3,48}',x))
def password_ok(x):return len(x)>=12 and len(x)<=256
def who(request):
    token=request.cookies.get('command_ready_session','')
    if not token:return None
    digest=hashlib.sha256(token.encode()).hexdigest()
    with db() as c:
        row=c.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>? AND u.active=1',(digest,int(time.time()))).fetchone()
        return dict(row) if row else None

def auth(request,write=False,admin=False):
    u=who(request)
    if not u:raise HTTPException(401,'Sign in required')
    if admin and u['role']!='admin':raise HTTPException(403,'Administrator access required')
    if write and request.headers.get('x-csrf-token')!=u['csrf']:raise HTTPException(403,'CSRF token required')
    if write and u['must_change_password'] and request.url.path not in ('/api/change-password','/api/logout'):
        raise HTTPException(403,'Change temporary password first')
    return u

class Login(BaseModel): username:str;password:str
class ChangePassword(BaseModel):old_password:str;new_password:str
class NewUser(BaseModel):username:str;display_name:str;role:str='officer'
class ModuleComplete(BaseModel):module:int=Field(ge=0,le=6)
class AnswerSet(BaseModel):answers:dict[str,int]
class Toggle(BaseModel):active:bool

@app.get('/')
def index():
    if os.environ.get('COMMAND_READY_PREVIEW_MODE', '1') != '1':
        return FileResponse(BASE/'static'/'index.html')
    from html import escape
    cards = ''.join(
        '<article><span class="num">MODULE ' + str(i+1) + '</span><h3>' +
        escape(m['title']) + '</h3><p>' + escape(m['intro']) +
        '</p><small>' + escape(m.get('duration','')) + '</small></article>'
        for i,m in enumerate(COURSE['modules'])
    )
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Command Ready Training Academy | Preview</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1521;color:#edf3fa;font:16px/1.6 system-ui,Segoe UI,Arial,sans-serif}
header{background:linear-gradient(120deg,#102338,#24516e);padding:52px max(22px,calc((100vw - 1050px)/2));border-bottom:3px solid #c9a46a}
mark{background:#c9a46a;color:#102338;padding:5px 10px;border-radius:3px;font-size:12px;font-weight:800;letter-spacing:.12em}
h1{font-size:clamp(32px,5vw,54px);line-height:1.08;margin:18px 0 10px}
header p{max-width:700px;color:#d6e4ef}main{max-width:1100px;margin:auto;padding:35px 20px}
h2{font-size:25px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}
article{background:#15263a;border:1px solid #31485e;border-radius:12px;padding:22px}
article h3{margin:8px 0}article p{color:#c4d2df;font-size:14px}.num{font-size:12px;color:#d5b67d;font-weight:800;letter-spacing:.08em}
small{color:#b9c8d8}.note{margin-top:30px;padding:16px;border-left:3px solid #c9a46a;background:#192a3b}
footer{text-align:center;padding:28px;color:#93a9bc;font-size:13px}
</style></head><body><header><mark>INDEPENDENT LAW ENFORCEMENT EDUCATION</mark>
<h1>COMMAND READY<br>TRAINING ACADEMY</h1>
<p><strong>Knowledge. Judgment. Readiness.</strong></p>
<p>Scenario-driven training designed to strengthen lawful decisions, clear articulation, and professional confidence.</p></header>
<main><h2>Texas Arrest, Search &amp; Seizure Refresher</h2>
<p>Seven instructional modules • Practical scenarios • 40-question final assessment planned</p>
<div class="grid">''' + cards + '''</div>
<div class="note"><strong>Private-build preview:</strong> This page demonstrates the course catalog and brand only.
Accounts, exams, progress tracking, certificates and agency dashboards are intentionally disabled.
Course content requires independent legal review before commercial release. No TCOLE credit is implied.</div>
</main><footer>© Command Ready Training Academy • Independent training platform prototype</footer>
</body></html>'''
    return HTMLResponse(page)
@app.post('/api/login')
def login(body:Login,request:Request):
    # Pilot only: reverse-proxy rate limiting / lockout required before deployment.
    with db() as c:
        row=c.execute('SELECT * FROM users WHERE username=? AND active=1',(body.username.lower(),)).fetchone()
        try: valid=bool(row) and PH.verify(row['password_hash'],body.password)
        except (VerifyMismatchError,VerificationError):valid=False
        if not valid:raise HTTPException(401,'Invalid credentials')
        token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(24)
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],csrf,int(time.time())+8*3600))
        audit(c,row['id'],'login')
    resp=JSONResponse({'ok':True})
    resp.set_cookie('command_ready_session',token,httponly=True,secure=os.environ.get('COMMAND_READY_DEV_HTTP')!='1',samesite='strict',max_age=8*3600,path='/')
    return resp
@app.post('/api/logout')
def logout(request:Request):
    u=auth(request,write=True)
    token=request.cookies.get('command_ready_session','')
    with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),));audit(c,u['id'],'logout')
    resp=JSONResponse({'ok':True});resp.delete_cookie('command_ready_session',path='/');return resp
@app.get('/api/me')
def me(request:Request):
    u=auth(request)
    return {'id':u['id'],'username':u['username'],'name':u['display_name'],'role':u['role'],'must_change_password':bool(u['must_change_password']),'csrf':u['csrf']}
@app.post('/api/change-password')
def change_password(body:ChangePassword,request:Request):
    u=auth(request,write=True)
    try:PH.verify(u['password_hash'],body.old_password)
    except (VerifyMismatchError,VerificationError):raise HTTPException(400,'Current password incorrect')
    if not password_ok(body.new_password):raise HTTPException(400,'Use a password of 12–256 characters')
    with db() as c:
        c.execute('UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?',(PH.hash(body.new_password),u['id']))
        audit(c,u['id'],'password_change')
    return {'ok':True}
@app.get('/api/course')
def course(request:Request):
    auth(request)
    return {'modules':COURSE['modules'],'course_version':'1.1-curriculum / command-ready-2.0-pilot','exam_questions':40,'pass_score':32}
@app.get('/api/progress')
def progress(request:Request):
    u=auth(request)
    with db() as c:
        done=[r['module'] for r in c.execute('SELECT module FROM progress WHERE user_id=?',(u['id'],))]
        a=c.execute('SELECT id,score,total,submitted_at FROM attempts WHERE user_id=? AND submitted_at IS NOT NULL ORDER BY id DESC LIMIT 5',(u['id'],)).fetchall()
    return {'complete':done,'attempts':[dict(x) for x in a]}
@app.post('/api/complete')
def complete(body:ModuleComplete,request:Request):
    u=auth(request,write=True)
    with db() as c:
        c.execute('INSERT OR IGNORE INTO progress(user_id,module,completed_at) VALUES(?,?,?)',(u['id'],body.module,now()))
        audit(c,u['id'],'module_complete',body.module)
    return {'ok':True}
@app.post('/api/exam/start')
def start_exam(request:Request):
    u=auth(request,write=True)
    with db() as c:
        count=c.execute('SELECT COUNT(*) FROM progress WHERE user_id=?',(u['id'],)).fetchone()[0]
        if count<7:raise HTTPException(400,'Finish all modules first')
        pending=c.execute('SELECT id FROM attempts WHERE user_id=? AND submitted_at IS NULL ORDER BY id DESC LIMIT 1',(u['id'],)).fetchone()
        if pending:aid=pending['id']
        else:
            order=list(range(len(COURSE['bank'])))
            # Randomize question order per attempt, preserve answer keys only on server.
            import random
            secrets.SystemRandom().shuffle(order)
            cur=c.execute('INSERT INTO attempts(user_id,started_at,question_order) VALUES(?,?,?)',(u['id'],now(),json.dumps(order)))
            aid=cur.lastrowid;audit(c,u['id'],'exam_started',aid)
    return exam_questions(aid,u['id'])
def exam_questions(aid,uid):
    with db() as c:r=c.execute('SELECT * FROM attempts WHERE id=? AND user_id=?',(aid,uid)).fetchone()
    if not r:raise HTTPException(404,'Exam not found')
    order=json.loads(r['question_order'])
    return {'attempt_id':aid,'questions':[{'number':i+1,'question':COURSE['bank'][n]['q'],'options':COURSE['bank'][n]['a']} for i,n in enumerate(order)]}
@app.post('/api/exam/{attempt_id}/submit')
def submit(attempt_id:int,body:AnswerSet,request:Request):
    u=auth(request,write=True)
    with db() as c:
        r=c.execute('SELECT * FROM attempts WHERE id=? AND user_id=?',(attempt_id,u['id'])).fetchone()
        if not r:raise HTTPException(404,'Exam not found')
        if r['submitted_at']:raise HTTPException(409,'Already submitted')
        order=json.loads(r['question_order'])
        if set(body.answers)!={str(i) for i in range(len(order))}:raise HTTPException(400,'All questions required')
        if any(not isinstance(body.answers[str(i)],int) or body.answers[str(i)] not in range(3) for i in range(len(order))):raise HTTPException(400,'Invalid answers')
        score=sum(body.answers[str(i)]==COURSE['bank'][n]['c'] for i,n in enumerate(order))
        c.execute('UPDATE attempts SET submitted_at=?,score=?,total=?,answers=? WHERE id=?',(now(),score,len(order),json.dumps(body.answers),attempt_id))
        audit(c,u['id'],'exam_submitted',f'{attempt_id}:{score}/{len(order)}')
    return {'score':score,'total':len(order),'passed':score>=32,'review':[{'correct':COURSE['bank'][n]['c'],'explanation':COURSE['bank'][n]['why']} for n in order]}
@app.get('/api/admin/users')
def users(request:Request):
    auth(request,admin=True)
    with db() as c:
        rows=c.execute('''SELECT u.id,u.username,u.display_name,u.role,u.active,COUNT(DISTINCT p.module) completed,(SELECT score FROM attempts a WHERE a.user_id=u.id AND submitted_at IS NOT NULL ORDER BY id DESC LIMIT 1) latest_score,(SELECT COUNT(*) FROM attempts a WHERE a.user_id=u.id AND submitted_at IS NOT NULL) attempts FROM users u LEFT JOIN progress p ON p.user_id=u.id GROUP BY u.id ORDER BY u.display_name''').fetchall()
    return [dict(r) for r in rows]
@app.post('/api/admin/users')
def create_user(body:NewUser,request:Request):
    u=auth(request,write=True,admin=True)
    if not username_ok(body.username) or not body.display_name.strip() or len(body.display_name)>100 or body.role not in ('officer','admin'):
        raise HTTPException(400,'Invalid user details')
    password=secrets.token_urlsafe(18)
    try:
        with db() as c:
            cur=c.execute('INSERT INTO users(username,display_name,password_hash,role) VALUES(?,?,?,?)',(body.username.lower(),body.display_name.strip(),PH.hash(password),body.role))
            audit(c,u['id'],'user_created',cur.lastrowid)
    except sqlite3.IntegrityError:raise HTTPException(409,'Username already exists')
    return {'username':body.username.lower(),'temporary_password':password,'note':'Copy once; require password change at first login. Share privately.'}
@app.post('/api/admin/users/{user_id}/active')
def toggle(user_id:int,body:Toggle,request:Request):
    u=auth(request,write=True,admin=True)
    if user_id==u['id'] and not body.active:raise HTTPException(400,'Cannot disable own account')
    with db() as c:
        cur=c.execute('UPDATE users SET active=? WHERE id=?',(int(body.active),user_id))
        if not cur.rowcount:raise HTTPException(404,'User not found')
        if not body.active:c.execute('DELETE FROM sessions WHERE user_id=?',(user_id,))
        audit(c,u['id'],'account_status',f'{user_id}:{body.active}')
    return {'ok':True}
@app.get('/api/admin/export.csv')
def export(request:Request):
    from fastapi.responses import Response
    import csv,io
    auth(request,admin=True)
    with db() as c:rows=c.execute('''SELECT u.username,u.display_name,u.role,u.active,COUNT(DISTINCT p.module) completed,(SELECT MAX(score) FROM attempts a WHERE a.user_id=u.id AND submitted_at IS NOT NULL) best_score,(SELECT COUNT(*) FROM attempts a WHERE a.user_id=u.id AND submitted_at IS NOT NULL) attempts FROM users u LEFT JOIN progress p ON p.user_id=u.id GROUP BY u.id ORDER BY u.display_name''').fetchall()
    f=io.StringIO();w=csv.writer(f);w.writerow(['Username','Name','Role','Active','Modules Complete','Best Exam Score / 40','Exam Attempts','Course Version'])
    for r in rows:w.writerow([*list(r),'1.1-curriculum'])
    return Response(f.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="command-ready-training-report.csv"'})

if __name__=='__main__' and len(sys.argv)>=2 and sys.argv[1]=='bootstrap-admin':
    import getpass
    username=input('Admin username: ').strip().lower();name=input('Display name: ').strip();pw=getpass.getpass('Strong password (12+ chars): ')
    if not username_ok(username) or not name or not password_ok(pw):sys.exit('Invalid details')
    with db() as c:
        c.execute('INSERT INTO users(username,display_name,password_hash,role,must_change_password) VALUES(?,?,?,?,0)',(username,name,PH.hash(pw),'admin'))
    print('Administrator created. Do not share credentials.')
