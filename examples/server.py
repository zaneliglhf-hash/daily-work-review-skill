"""Local synthetic native-select fixture. No credentials or external calls."""
import argparse
import html
import json
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA = json.loads(Path(__file__).with_name('fixture.json').read_text(encoding='utf-8'))
STATE = {day: {name: ('✅' if day == '2026-10-27' else '') for name in DATA['roster']} for day in ['2026-10-27','2026-10-28']}
RUN = tempfile.TemporaryDirectory(prefix='daily-review-fixture-')
LOG = Path(RUN.name) / 'state.json'
def esc(s): return html.escape(str(s), quote=True)
def persist(): LOG.write_text(json.dumps(STATE, ensure_ascii=False),encoding='utf-8')
persist()
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self, text, status=200, content_type='text/html; charset=utf-8'):
        body=text.encode('utf-8'); self.send_response(status); self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def page(self,title,body,status=200):
        self.send('<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+esc(title)+'</title><style>body{max-width:980px;margin:40px auto;font:18px system-ui;line-height:1.7;padding:0 20px;color:#183a30}td,th{padding:8px 16px;border:1px solid #cddad1}table{border-collapse:collapse}select{font-size:18px}aside{background:#f2f4ed;padding:14px}a{color:#267458}</style><aside>虚构测试资料 · 只用于技能验证，不是真实提交或微信文档</aside><nav><a href="/audit">审核表</a> · <a href="/submissions">作品提交表</a></nav><h1>'+esc(title)+'</h1>'+body+'</html>',status)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/state': self.send(json.dumps(STATE,ensure_ascii=False),content_type='application/json; charset=utf-8');return
        if p in ['/','/audit']:
            rows=[]
            for name in DATA['roster']:
                cells=[]
                for day in STATE:
                    options=''.join('<option value="'+esc(v)+'"'+(' selected' if STATE[day][name]==v else '')+'>'+esc(v or '未填写')+'</option>' for v in ['', '✅','❌'])
                    cells.append('<td><form method="post" action="/mark"><input type="hidden" name="name" value="'+name+'"><input type="hidden" name="date" value="'+day+'"><select aria-label="'+name+' '+day+'" name="value" onchange="this.form.submit()">'+options+'</select><noscript><button>保存</button></noscript></form></td>')
                rows.append('<tr><th>'+name+'</th>'+''.join(cells)+'</tr>')
            self.page('审核表','<p>完整名册共8人。轮值顺序就是下表从上到下；末尾不自动循环。所有修改经服务端保存，刷新后保留。</p><table><thead><tr><th>姓名 / 轮值顺序</th><th>2026-10-27</th><th>2026-10-28</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>');return
        if p=='/submissions':
            rows=[]
            for row in DATA['submissions']:
                work='<a href="/work/'+esc(row['work'])+'">打开作品</a>' if 'work' in row else esc(row['note'])
                rows.append('<tr><td>'+row['name']+'</td><td>'+row['date']+'</td><td>'+work+'</td></tr>')
            self.page('作品提交表','<p>以下为全部记录，无分页，无隐藏记录。按行顺序展示。</p><table><tr><th>姓名</th><th>作品日期</th><th>提交内容</th></tr>'+''.join(rows)+'</table>');return
        if p.startswith('/work/'):
            work=next((w for w in DATA['works'] if w['id']==p.rsplit('/',1)[-1]),None)
            if work:self.page(work['title'],'<p>作者：'+work['author']+'</p><article>'+esc(work['body'])+'</article><p>全文结束，无图片或附件。</p>');return
        self.page('无法访问','<p>这条作品链接已失效。不可推断未提交。</p>',404)
    def do_POST(self):
        if self.path!='/mark':self.send('Not found',404);return
        n=int(self.headers.get('Content-Length','0'))
        if n>2048:self.send('Too large',413);return
        f=parse_qs(self.rfile.read(n).decode('utf-8'),keep_blank_values=True)
        name=f.get('name',[''])[0];day=f.get('date',[''])[0];value=f.get('value',[''])[0]
        if day not in STATE or name not in STATE[day] or value not in ['', '✅','❌']:self.send('Invalid mark',400);return
        STATE[day][name]=value;persist();self.send_response(303);self.send_header('Location','/audit');self.send_header('Content-Length','0');self.end_headers()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8877);a=p.parse_args()
    print('Synthetic fixture: http://127.0.0.1:'+str(a.port)+'/audit',flush=True)
    HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
