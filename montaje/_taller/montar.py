#!/usr/bin/env python3
"""
CV Vivo · montaje automático del video (sin avatar).
Uso:  python3 montar.py montaje/<token>        (desde la raíz del repo portafolios-postules)
Lee:  voz.wav (o voz.mp3), version.json, video.json opcional (textos de la gráfica)
Deja: v/<token>.mp4, v/<token>.jpg, v/<token>.json  → la página los toma sola por el token.
"""
import json, os, re, subprocess, sys, asyncio, shutil, tempfile, math, struct, wave, signal

TALLER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(TALLER, '..', '..'))
OFF = 1.37            # la voz entra después del primer golpe
FPS = 30

def sh(*a, **k): subprocess.run(a, check=True, **k)

def cargar(dir_):
    V = json.load(open(os.path.join(dir_, 'version.json')))
    voz = next((os.path.join(dir_, n) for n in ('voz.wav', 'voz.mp3', 'voz.m4a') if os.path.exists(os.path.join(dir_, n))), None)
    if not voz: sys.exit('No hay voz.wav ni voz.mp3 en ' + dir_)
    extra = json.load(open(os.path.join(dir_, 'video.json'))) if os.path.exists(os.path.join(dir_, 'video.json')) else {}
    return V, voz, {**(V.get('video') or {}), **extra}

def pcm24(voz, tmp):
    out = os.path.join(tmp, 'voz24.wav')
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', voz, '-ac', '1', '-ar', '24000', '-sample_fmt', 's16', out)
    w = wave.open(out); n = w.getnframes(); data = w.readframes(n); w.close()
    return out, data, n / 24000.0

def cortes(data, escenas):
    F = 480; rms = []
    for i in range(0, len(data) - 2 * F, 2 * F):
        v = struct.unpack('<%dh' % F, data[i:i + 2 * F]); rms.append(math.sqrt(sum(x * x for x in v) / F) / 32768)
    palabras = [len(str(e.get('locucion', '')).split()) for e in escenas]
    js = open(os.path.join(TALLER, 'segmentar.js')).read() + '\nconsole.log(JSON.stringify(segmentarVoz(%s, 0.02, %s)));' % (json.dumps(rms), json.dumps(palabras))
    r = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
    return json.loads(r.stdout.strip().splitlines()[-1])

def frases(t, maxp=7):
    partes, act = [], []
    for w in t.replace('—', ' — ').split():
        act.append(w)
        if len(act) >= maxp or (re.search(r'[,;:.?!…]$', w) and len(act) >= 3): partes.append(' '.join(act)); act = []
    if act: partes.append(' '.join(act))
    return [re.sub(r'\s+—\s+', ' — ', p).strip() for p in partes]

def datos(V, cuts, dur_voz, extra):
    esc = V['guion']['escenas']; beats = json.load(open(os.path.join(TALLER, 'beats.json')))['beats']
    def snap(t):
        b = min(beats, key=lambda x: abs(x - t)); return b if abs(b - t) < 0.35 else t
    habla_fin = cuts[-1][1] + OFF
    DUR = round(min(60.0, max(56.0, habla_fin + 3.4)), 2)
    lim = [0.0] + [round(snap(cuts[i][1] + OFF + 0.1), 3) for i in range(len(esc) - 1)] + [DUR]
    D = {'empresa': V.get('empresa', ''), 'beat0': beats[0], 'habla_fin': habla_fin,
         'cita': (V.get('guion_inputs') or {}).get('cita_ficha') or esc[2].get('en_pantalla', '').strip('“”…'),
         'escenas': []}
    for i, e in enumerate(esc):
        d = {'rol': e['rol'], 'a': lim[i], 'b': lim[i + 1], 'pantalla': e.get('en_pantalla', ''), 'subs': frases(e.get('locucion', ''))}
        if i == 0: d['sa'] = OFF
        D['escenas'].append(d)
    D.update(extra)
    if len(D['cita']) > 170: D['cita'] = D['cita'][:167].rsplit(' ', 1)[0] + '…'
    return D, DUR

async def capturas(V, tmp):
    from playwright.async_api import async_playwright
    srv = subprocess.Popen(['python3', '-m', 'http.server', '8799'], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1.2)
    horas = [{'d': d, 'h': h, 'i': i * 3 + j} for i, d in enumerate(['lun', 'mar', 'mié']) for j, h in enumerate(['10:00', '12:30', '16:00'])]
    Vs = dict(V); Vs.pop('video_url', None)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1280, 'height': 720}, color_scheme='dark')
            async def h(route):
                u = route.request.url; d = route.request.post_data or ''
                if u.endswith('app.txt'): await route.fulfill(body='https://script.google.com/macros/s/X/exec')
                elif 'script.google.com' in u:
                    if 'horarios' in d: r = horas
                    elif 'preguntar' in d: r = {'texto': (V.get('hilo') or {}).get('prueba', ''), 'fuentes': [c['id'] for c in (V.get('casos') or [])[:1]], 'siguientes': ((V.get('chat') or {}).get('sugeridas') or [])[1:3]}
                    elif 'version' in d: r = {'V': Vs, 'data': {'token': V.get('token'), 'min_s': 99}}
                    else: r = {}
                    await route.fulfill(body=json.dumps({'ok': True, 'r': r}), content_type='application/json')
                else: await route.continue_()
            await pg.route('**/*', h)
            await pg.goto('http://localhost:8799/?v=' + V.get('token', '') + '&preview=1'); await pg.wait_for_timeout(2500)
            async def foto(sel, nombre, antes=None):
                if antes: await pg.evaluate(antes); await pg.wait_for_timeout(1500)
                await pg.evaluate("s=>{const e=document.querySelector(s); if(e) e.scrollIntoView({block:'start'}); window.scrollBy(0,-20)}", sel)
                await pg.wait_for_timeout(500); await pg.screenshot(path=os.path.join(tmp, nombre + '.jpg'), type='jpeg', quality=90)
            await foto('#casos', 'p1-casos')
            q = ((V.get('chat') or {}).get('sugeridas') or ['¿Qué ha hecho Paul?'])[0]
            await foto('#casos', 'p2-chat', "(()=>{const i=document.getElementById('askInput'); if(!i) return; i.value=%s; i.form ? i.form.requestSubmit() : i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))})()" % json.dumps(q))
            await foto('.callTop', 'p3-agenda', "document.getElementById('callBtn') && document.getElementById('callBtn').click()")
            await b.close()
    finally:
        srv.send_signal(signal.SIGTERM)

async def recuadro_pdf(V, tmp):
    sys.path.insert(0, TALLER); import print_safe as P
    P.LANG = V.get('idioma_documentos', 'es')
    url = 'https://etiennepaulandre-07.github.io/portafolios-postules/?v=' + V.get('token', '')
    d = {'nombre': V.get('nombre', ''), 'nombre_corto': V.get('nombre_corto', ''), 'titular': V.get('titular', '').replace(' | ', ' · '),
         'contacto': '', 'empresa_corta': V.get('empresa', ''), 'url': url}
    cab = (f'<p style="font-size:22pt;font-weight:bold;margin:0">{d["nombre"]}</p>'
           f'<p style="font-size:11.5pt;font-weight:bold;margin:3px 0 10px">{d["titular"]}</p>')          # sin teléfono ni correo: el video es público
    html = f'<html><head><meta charset="utf-8"></head><body style="{P.BODY};background:#fff"><div id="c" style="width:760px;padding:28px 34px;background:#fff">{cab}{P.recuadro(d)}</div></body></html>'
    f = os.path.join(tmp, 'box.html'); open(f, 'w').write(html)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(device_scale_factor=2)
        await pg.goto('file://' + f); await (await pg.query_selector('#c')).screenshot(path=os.path.join(tmp, 'p0-pdf.jpg'), type='jpeg', quality=95)
        await b.close()

async def render(tmp, DUR, salida):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1280, 'height': 720})
        await pg.goto('file://' + os.path.join(tmp, 'plantilla.html')); await pg.wait_for_function('ready()')
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', salida], stdin=subprocess.PIPE)
        for i in range(int(FPS * DUR)):
            await pg.evaluate(f'draw({i / FPS})'); ff.stdin.write(await pg.screenshot(type='jpeg', quality=92))
        ff.stdin.close(); ff.wait(); await b.close()

def mezcla(mudo, voz, D, DUR, salida):
    sfx = [('bass', D['beat0'], 0.6), ('bass', D['escenas'][1]['a'] + 3.6, 0.5)]
    sfx += [('swipe', e['a'] - 0.15, 1.0) for e in D['escenas'][1:]]
    ev = next((e for e in D['escenas'] if e['rol'] == 'evidencia'), None)
    if ev:
        paso = (ev['b'] - ev['a'] - 3) / 4
        sfx += [('ui', ev['a'] + 0.8 + i * paso, 0.3) for i in range(4)]
    cafe = D['escenas'][-1]; sfx.append(('ui', cafe['a'] + 1.6, 0.35))
    ins = ['-i', mudo, '-i', voz, '-i', os.path.join(TALLER, 'musica.mp3')]
    fil = [f'[1:a]adelay={int(OFF * 1000)}|{int(OFF * 1000)},apad,atrim=0:{DUR},asplit=2[v][vk]',
           f'[2:a]atrim=0:{DUR},volume=0.30,afade=t=out:st={DUR - 2.2}:d=2.2[m0]',
           '[m0][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[m]']
    tags = ['[v]', '[m]']
    for k, (n, t, vol) in enumerate(sfx):
        ins += ['-i', os.path.join(TALLER, f'sfx-{n}.mp3')]; idx = 3 + k
        fil.append(f'[{idx}:a]adelay={max(0, int(t * 1000))}|{max(0, int(t * 1000))},volume={vol}[s{k}]'); tags.append(f'[s{k}]')
    fil.append(''.join(tags) + f'amix=inputs={len(tags)}:normalize=0:duration=first,atrim=0:{DUR},alimiter=limit=0.89[a]')
    sh('ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(fil), '-map', '0:v', '-map', '[a]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', salida)

def main():
    dir_ = os.path.abspath(sys.argv[1]); V, voz, extra = cargar(dir_); tok = V['token']
    tmp = tempfile.mkdtemp(prefix='montaje-')
    wav, data, dur = pcm24(voz, tmp)
    cuts = cortes(data, V['guion']['escenas'])
    D, DUR = datos(V, cuts, dur, extra)
    open(os.path.join(tmp, 'data.js'), 'w').write('window.D=' + json.dumps(D, ensure_ascii=False) + ';')
    shutil.copy(os.path.join(TALLER, 'plantilla.html'), tmp)
    asyncio.run(capturas(V, tmp)); asyncio.run(recuadro_pdf(V, tmp))
    if '--solo-cuadros' in sys.argv:
        print(tmp); return
    mudo = os.path.join(tmp, 'mudo.mp4'); asyncio.run(render(tmp, DUR, mudo))
    os.makedirs(os.path.join(REPO, 'v'), exist_ok=True)
    out = os.path.join(REPO, 'v', tok + '.mp4'); mezcla(mudo, wav, D, DUR, out)
    sh('ffmpeg', '-y', '-loglevel', 'error', '-ss', '12', '-i', out, '-frames:v', '1', '-vf', 'scale=960:-1', '-q:v', '4', os.path.join(REPO, 'v', tok + '.jpg'))
    json.dump({'escenas': [{'a': e['a'], 'b': e['b']} for e in D['escenas']]}, open(os.path.join(REPO, 'v', tok + '.json'), 'w'))
    p = os.path.join(dir_, 'pedido.json'); pe = json.load(open(p)) if os.path.exists(p) else {}
    pe.update(estado='listo', video='v/' + tok + '.mp4', duracion_s=DUR); json.dump(pe, open(p, 'w'), ensure_ascii=False, indent=1)
    print('OK', out, DUR)

if __name__ == '__main__': main()
