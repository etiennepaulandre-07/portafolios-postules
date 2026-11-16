"""CV y carta en HTML 'seguro' para el convertidor HTML→PDF de Apps Script:
tablas (sin flex/grid), Arial, estilos inline, QR como PNG base64. Uso: python3 print_safe.py datos.json salida_dir"""
import json, sys, html, base64, io, qrcode
E = html.escape
def qr_png(url):
    q = qrcode.QRCode(box_size=4, border=1); q.add_data(url); q.make(fit=True)
    b = io.BytesIO(); q.make_image(fill_color='black', back_color='white').save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
INK, MUT, LIN = '#1a1a1a', '#5f5f5c', '#d0d0cc'
BODY = f'font-family:Arial,Helvetica,sans-serif;font-size:10pt;line-height:1.4;color:{INK};margin:0'
def h2(t): return f'<p style="font-size:12pt;font-weight:bold;margin:14px 0 5px;padding-bottom:3px;border-bottom:1px solid {LIN}">{E(t)}</p>'
def cabecera(d):
    c = d['contacto']
    return (f'<p style="font-size:22pt;font-weight:bold;margin:0">{E(d["nombre"])}</p>'
            f'<p style="font-size:11.5pt;font-weight:bold;margin:3px 0 0">{E(d["titular"])}</p>'
            f'<p style="font-size:9pt;color:{MUT};margin:3px 0 0">{E(c["ubicacion"])} · {E(c["email"])} · {E(c["tel"])} · '
            f'<a href="{c["linkedin"]}" style="color:{INK}">{E(c["linkedin"].replace("https://www.",""))}</a></p>'
            f'<hr style="border:0;border-top:2px solid {INK};margin:8px 0 10px">')
def recuadro(d, src='cv'):
    url = d['url'] + ('&' if '?' in d['url'] else '?') + 'src=' + src
    qr = d['url'] + ('&' if '?' in d['url'] else '?') + 'src=qr'
    return (f'<table cellpadding="0" cellspacing="0" style="width:100%;border:2px solid {INK};border-collapse:collapse;margin:6px 0 4px"><tr>'
            f'<td style="width:96px;padding:8px;vertical-align:middle"><img src="{qr_png(qr)}" width="88" height="88" alt="QR"></td>'
            f'<td style="padding:8px 10px 8px 4px;vertical-align:middle">'
            f'<p style="font-size:8pt;letter-spacing:1px;margin:0;color:{MUT}">{T('PARA UNA MEJOR EXPERIENCIA, ENTRA AQUÍ')}</p>'
            f'<p style="font-size:13pt;font-weight:bold;margin:2px 0">{T('Mi CV interactivo, hecho para ')}{E(d["empresa_corta"])}</p>'
            f'<p style="font-size:9pt;margin:0 0 5px">{T('Un video de 1 minuto, la evidencia requisito por requisito, un chat para preguntarle lo que quieras y mi agenda para una llamada de 20 minutos.')}</p>'
            f'<p style="margin:0"><a href="{url}" style="font-size:10.5pt;font-weight:bold;color:{INK}">{T('Abrir mi CV interactivo →')}</a>'
            f' <span style="font-size:8.5pt;color:{MUT}">{T('o escanea el código con tu celular')}</span></p></td></tr></table>')
LANG = 'es'
EN = {'PARA UNA MEJOR EXPERIENCIA, ENTRA AQUÍ': 'FOR A BETTER EXPERIENCE, START HERE', 'Mi CV interactivo, hecho para ': 'My interactive CV, built for ', 'Un video de 1 minuto, la evidencia requisito por requisito, un chat para preguntarle lo que quieras y mi agenda para una llamada de 20 minutos.': 'A 1-minute video, evidence requirement by requirement, a chat to ask anything about my experience, and my calendar for a 20-minute call.', 'Abrir mi CV interactivo →': 'Open my interactive CV →', 'o escanea el código con tu celular': 'or scan the code with your phone', 'Perfil': 'Profile', 'Lo que pide el cargo y dónde lo he hecho': 'What the role asks for and where I have done it', 'Experiencia': 'Experience', 'Casos con números': 'Results by case', 'Habilidades': 'Skills', 'Formación': 'Education', 'Certificaciones': 'Certifications', 'Idiomas': 'Languages', 'Actividades adicionales': 'Additional activities', 'Referencias': 'References', 'Disponibles a solicitud.': 'Available upon request.', 'Versión para ': 'Version for ', 'Ver la versión interactiva': 'See the interactive version', 'mi CV interactivo': 'my interactive CV', 'Carta': 'Letter'}
def T(x): return EN.get(x, x) if LANG == 'en' else x
def cv(d):
    o = [f'<html><head><meta charset="utf-8"><title>{E(d["nombre_corto"])} – CV – {E(d["cargo"])} – {E(d["empresa_corta"])}</title></head><body style="{BODY}">', cabecera(d), recuadro(d)]
    o += [h2(T('Perfil')), f'<p style="margin:0">{E(d["perfil_cv"])}</p>', h2(T('Lo que pide el cargo y dónde lo he hecho')),
          f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:9.3pt">']
    for req, ev, aj in d['fit']:
        o.append(f'<tr><td style="width:34%;padding:4px 6px 4px 0;border-bottom:1px solid {LIN};font-weight:bold;vertical-align:top">{E(req)}</td>'
                 f'<td style="padding:4px 6px;border-bottom:1px solid {LIN};vertical-align:top">{E(ev)}</td>'
                 f'<td style="width:9%;padding:4px 0;border-bottom:1px solid {LIN};text-align:right;vertical-align:top;font-weight:bold">{E(aj)}</td></tr>')
    o += ['</table>', h2(T('Experiencia'))]
    for j in d['experiencia']:
        o.append(f'<table cellpadding="0" cellspacing="0" style="width:100%;margin:6px 0 2px"><tr><td style="font-size:10.5pt;font-weight:bold">{E(j["cargo"])} · {E(j["empresa"])}</td>'
                 f'<td style="text-align:right;font-size:9pt;color:{MUT};white-space:nowrap">{E(j["periodo"])}</td></tr></table><ul style="margin:2px 0 4px 16px;padding:0">')
        o += [f'<li style="margin:0 0 2px;font-size:9.5pt">{E(b)}</li>' for b in j['bullets']]
        o.append('</ul>')
    o.append(h2(T('Casos con números')) + '<table cellpadding="0" cellspacing="6" style="width:100%;margin:0 -6px">')
    cs = d['casos']
    for i in range(0, len(cs), 2):
        o.append('<tr>')
        for c in cs[i:i+2]:
            o.append(f'<td style="width:50%;border:1px solid {LIN};padding:7px 9px;vertical-align:top">'
                     f'<p style="font-size:8pt;color:{MUT};margin:0">{E(c["lbl"].upper())}</p><p style="font-weight:bold;margin:2px 0">{E(c["titulo"])}</p>'
                     f'<p style="font-size:8.8pt;color:{MUT};margin:0">{E(c["texto"])}</p><p style="font-size:13pt;font-weight:bold;margin:4px 0 0">{E(c["valor"])}</p>'
                     f'<p style="font-size:8.8pt;color:{MUT};margin:0">{E(c["que"])}</p></td>')
        o.append('</tr>')
    o.append('</table>')
    o.append(f'<table cellpadding="0" cellspacing="0" style="width:100%"><tr><td style="width:55%;vertical-align:top;padding-right:14px">{h2(T('Habilidades'))}')
    o += [f'<p style="margin:0 0 4px;font-size:9.3pt"><b>{E(g)}:</b> {E(t)}</p>' for g, t in d['habilidades']]
    o.append(f'</td><td style="vertical-align:top">{h2(T('Formación'))}')
    o += [f'<p style="margin:0 0 5px;font-size:9.3pt"><b>{E(t)}</b><br>{E(x)}</p>' for t, x in d['formacion']]
    o.append(h2(T('Certificaciones')) + '<p style="margin:0;font-size:9.3pt">' + '<br>'.join(E(x) for x in d['certificaciones']) + '</p>')
    o.append(h2(T('Idiomas')) + f'<p style="margin:0;font-size:9.3pt">{E(d["idiomas"])}</p></td></tr></table>')
    if d.get('actividades'):
        o.append(h2(T('Actividades adicionales')) + ''.join(f'<p style="margin:0 0 3px;font-size:9.3pt">{E(x)}</p>' for x in d['actividades']))
    refs = d.get('referencias') or []
    o.append(h2(T('Referencias')))
    if refs:
        o.append(f'<table cellpadding="0" cellspacing="0" style="width:100%;font-size:9.3pt">' + ''.join(
            f'<tr><td style="padding:2px 8px 2px 0;font-weight:bold;white-space:nowrap;vertical-align:top">{E(n)}</td><td style="padding:2px 8px 2px 0;vertical-align:top">{E(c)}</td><td style="padding:2px 0;vertical-align:top;color:{MUT}">{E(x)}</td></tr>' for n, c, x in refs) + '</table>')
    else:
        o.append(f'<p style="margin:0;font-size:9.3pt">{T("Disponibles a solicitud.")}</p>')
    o.append(f'<p style="margin-top:12px;padding-top:5px;border-top:1px solid {LIN};font-size:8.5pt;color:{MUT}">{T('Versión para ')}{E(d["empresa_corta"])} · <a href="{d["url"]}&src=cv" style="color:{INK}">{T('Ver la versión interactiva')}</a></p></body></html>')
    return ''.join(o)
def carta(d):
    ps = []
    for p in d['carta'].split('\n\n'):
        t = E(p).replace('\n', '<br>').replace(E(d['url']), f'<a href="{d["url"]}&src=carta" style="color:{INK};font-weight:bold">' + T('mi CV interactivo') + '</a>')
        ps.append(f'<p style="margin:0 0 11px;font-size:11pt;line-height:1.55">{t}</p>')
    return (f'<html><head><meta charset="utf-8"><title>{E(d["nombre_corto"])} – Carta – {E(d["empresa_corta"])}</title></head><body style="{BODY}">'
            + cabecera(d) + '<div style="margin-top:14px">' + ''.join(ps) + '</div>' + recuadro(d, 'carta') + '</body></html>')
if __name__ == '__main__':
    d = json.load(open(sys.argv[1])); out = sys.argv[2]; LANG = d.get('lang', 'es')
    open(f'{out}/{d["archivo_cv"]}', 'w').write(cv(d)); open(f'{out}/{d["archivo_carta"]}', 'w').write(carta(d))
