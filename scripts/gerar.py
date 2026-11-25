"""Desenha os SVGs de assets/ no visual da Insurge (cromo e folha holográfica).

Uso: pip install fonttools brotli && python scripts/gerar.py
O texto vira contorno porque o GitHub não carrega fonte externa dentro de SVG.
"""
import math
import random
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ.parent / "assets"
FUNDO, TINTA = "#06040f", "#150c33"
FOLHA = ["#7df9ff", "#b895ff", "#ff8ad8", "#fff3a6", "#9dffcb", "#7df9ff"]
CROMO = [(0, "#fff"), (15, "#e6e0ff"), (33, "#a79ce0"), (48.5, "#3b2c7c"), (50, "#170e3d"),
         (57, "#6a4ce8"), (73, "#dbcbff"), (85, "#fff"), (100, "#b3aee6")]
PRATA = [(0, "#fbfaff"), (46, "#d6d0f2"), (54, "#b2a9dd"), (100, "#cfc8ee")]


def fonte(nome, peso):
    f = instantiateVariableFont(TTFont(RAIZ / "fonts" / f"{nome}.woff2"), {"wght": peso})
    return f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm


DISPLAY, NEGRO = fonte("unbounded", 700), fonte("unbounded", 900)
TEXTO, PIXEL = fonte("hanken-grotesk", 500), fonte("pixelify-sans", 500)


def largura(txt, f, tam, esp=0):
    _, gs, cmap, upm = f
    return sum(gs[cmap[ord(c)]].width * tam / upm + esp for c in txt) - esp


def letras(txt, f, x, y, tam, ancora="i", esp=0):
    """Contorno do texto (atributo d). ancora: i(nício), m(eio) ou f(im)."""
    _, gs, cmap, upm = f
    e = tam / upm
    x -= largura(txt, f, tam, esp) * {"i": 0, "m": 0.5, "f": 1}[ancora]
    pen = SVGPathPen(gs, ntos=lambda n: f"{n:.1f}".rstrip("0").rstrip("."))
    for c in txt:
        g = gs[cmap[ord(c)]]
        g.draw(TransformPen(pen, (e, 0, 0, -e, x, y)))
        x += g.width * e + esp
    return pen.getCommands()


def em_circulo(txt, f, r, tam):
    """Texto em volta de um círculo na origem."""
    _, gs, cmap, upm = f
    e, total, acc = tam / upm, largura(txt, f, tam), 0
    pen = SVGPathPen(gs, ntos=lambda n: f"{n:.1f}")
    for c in txt:
        g = gs[cmap[ord(c)]]
        w = g.width * e
        a = (acc + w / 2) / total * 2 * math.pi
        co, si = math.cos(a), math.sin(a)
        ox, oy = r * si - w / 2 * co, -r * co - w / 2 * si
        g.draw(TransformPen(pen, (e * co, e * si, e * si, -e * co, ox, oy)))
        acc += w
    return pen.getCommands()


def grad(id_, paradas, x2=0, y2=1, extra=""):
    s = "".join(f'<stop offset="{o}%" stop-color="{c}"/>' for o, c in paradas)
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}" {extra}>{s}</linearGradient>'


def folha_defs(w):
    """Folha que se repete a cada w: anda exatamente um período e não dá salto."""
    n = len(FOLHA) - 1
    return grad("folha", [(i * 100 / n, c) for i, c in enumerate(FOLHA)],
                extra=f'gradientUnits="userSpaceOnUse" spreadMethod="repeat"').replace(
                    'x1="0" y1="0" x2="0" y2="1"', f'x1="0" y1="0" x2="{w}" y2="0"')


def corre(w, h, dur=9, larg=None, x=0, y=0):
    """Retângulo de folha que anda um período (w) por baixo de um recorte de largura larg."""
    return (f'<rect class="corre" x="{x - w}" y="{y}" width="{w + (larg or w)}" height="{h}" fill="url(#folha)" '
            f'style="--w:{w}px;animation-duration:{dur}s"/>')


CSS = """.corre{animation:corre linear infinite}@keyframes corre{to{transform:translateX(var(--w))}}
.gira{animation:gira linear infinite}@keyframes gira{to{transform:rotate(360deg)}}
.pisca{animation:pisca 4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes pisca{0%,100%{opacity:.15;transform:scale(.5)}50%{opacity:1;transform:scale(1)}}
.boia{animation:boia 7s ease-in-out infinite}@keyframes boia{50%{transform:translateY(-10px)}}
.vira{animation:vira 16s linear infinite}@keyframes vira{0%{transform:scaleX(1)}25%{transform:scaleX(.71)}
50%{transform:scaleX(0)}75%{transform:scaleX(-.71)}100%{transform:scaleX(-1)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}"""


def svg(nome, w, h, titulo, defs, corpo):
    (SAIDA / f"{nome}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<title>{titulo}</title><style>{CSS}</style><defs>{defs}</defs>{corpo}</svg>\n",
        encoding="utf-8", newline="\n")


def estrela(x, y, r, cor, atraso=0, classe="pisca"):
    k = r * 0.16
    d = f"M{x} {y - r}L{x + k} {y - k}L{x + r} {y}L{x + k} {y + k}L{x} {y + r}L{x - k} {y + k}L{x - r} {y}L{x - k} {y - k}Z"
    return f'<path class="{classe}" style="animation-delay:-{atraso:.1f}s" d="{d}" fill="{cor}"/>'


def hero():
    w, h = 1200, 440
    rnd = random.Random(7)
    pontos = "".join(f'<circle cx="{rnd.randint(20, 1180)}" cy="{rnd.randint(15, 425)}" r="{rnd.choice([.8, 1.1, 1.6])}" '
                     f'fill="#f2eeff" opacity="{rnd.uniform(.15, .6):.2f}"/>' for _ in range(110))
    brilhos = "".join(estrela(x, y, r, c, i * .9) for i, (x, y, r, c) in enumerate([
        (110, 130, 13, "#7df9ff"), (250, 270, 8, "#ff8ad8"), (905, 300, 9, "#fff3a6"), (1110, 330, 14, "#9dffcb"),
        (800, 70, 10, "#b895ff"), (60, 330, 8, "#9dffcb"), (380, 60, 7, "#fff3a6"), (990, 395, 9, "#ff8ad8")]))
    # meridianos igualmente espaçados no tempo, para o globo parecer girar
    globo = "".join(f'<circle class="vira" style="animation-delay:-{i * 16 / 6:.2f}s" r="290" vector-effect="non-scaling-stroke"/>'
                    for i in range(6))
    globo += "".join(f'<ellipse cy="{y}" rx="{math.sqrt(290**2 - y**2):.0f}" ry="{math.sqrt(290**2 - y**2) * .12:.0f}"/>'
                     for y in (-200, -105, 0, 105, 200))
    anel = "M-270 0A270 88 0 1 0 270 0A270 88 0 1 0 -270 0ZM-186 -4A186 47 0 1 1 186 -4A186 47 0 1 1 -186 -4Z"
    pinta_anel = ('<g clip-path="url(#canel)"><rect x="-280" y="-100" width="560" height="200" fill="url(#metal)"/>'
                  '<g style="mix-blend-mode:color">' + corre(600, 200, 7, x=-300, y=-100) + "</g></g>"
                  '<path d="M-270 0A270 88 0 1 0 270 0A270 88 0 1 0 -270 0Z" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="2.5"/>'
                  '<path d="M-186 -4A186 47 0 1 1 186 -4A186 47 0 1 1 -186 -4Z" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="1.5"/>'
                  '<path d="M-232 8A236 64 0 0 0 60 60" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" opacity=".75"/>'
                  '<path d="M150 -50A236 66 0 0 1 236 -4" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".7"/>')
    tam = 100
    tam *= 740 / largura("RIZU", NEGRO, 100, -2)
    nome = letras("RIZU", NEGRO, 600, 402, tam, "m", -2)
    # o contorno real manda na caixa do degradê, então o horizonte do cromo cai no meio da letra
    defs = (grad("cromo", CROMO) + grad("metal", [(0, "#fff"), (25, "#bfb2f5"), (45, "#4a34a8"), (55, "#8a6cf0"), (75, "#fff"), (100, "#9d8be0")])
            + folha_defs(600)
            + f'<clipPath id="quadro"><rect width="{w}" height="{h}" rx="28"/></clipPath>'
            + f'<clipPath id="cnome"><path d="{nome}"/></clipPath><clipPath id="canel"><path clip-rule="evenodd" d="{anel}"/></clipPath>'
            '<clipPath id="frente"><rect x="-400" y="0" width="800" height="200"/></clipPath>'
            '<radialGradient id="roxo"><stop stop-color="#7224fb" stop-opacity=".6"/><stop offset="1" stop-color="#7224fb" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="rosa"><stop stop-color="#ff8ad8" stop-opacity=".22"/><stop offset="1" stop-color="#ff8ad8" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="buraco" cx=".5" cy=".5" r=".5"><stop offset=".7" stop-color="#030208"/><stop offset=".9" stop-color="#1d0a4d"/><stop offset="1" stop-color="#9b5cff"/></radialGradient>'
            '<filter id="aura" x="-30%" y="-40%" width="160%" height="180%"><feGaussianBlur stdDeviation="20"/></filter>')
    corpo = (f'<g clip-path="url(#quadro)"><rect width="{w}" height="{h}" fill="{FUNDO}"/>'
             '<ellipse cx="600" cy="200" rx="620" ry="300" fill="url(#roxo)"/><ellipse cx="1080" cy="80" rx="480" ry="330" fill="url(#rosa)"/>'
             f'{pontos}<g transform="translate(600 190) rotate(-18) scale(.85)" fill="none" stroke="#9dffcb" stroke-opacity=".26" stroke-width="1.2">{globo}</g>{brilhos}'
             f'<g transform="translate(600 142) rotate(-16) scale(.78)"><g class="boia">'
             f'<path d="{anel}" fill="#b06bff" fill-rule="evenodd" filter="url(#aura)" opacity=".9"/>'
             f'{pinta_anel}<circle r="122" fill="url(#buraco)" stroke="#d075ef" stroke-opacity=".6" stroke-width="1.5"/>'
             f'<g clip-path="url(#frente)">{pinta_anel}</g></g></g>'
             f'<g transform="translate(1085 105) scale(.85)"><circle r="88" fill="{FUNDO}" fill-opacity=".55"/><g class="gira" style="animation-duration:22s"><path d="{em_circulo("CONTRA O GENÉRICO * SOB MEDIDA * INSURGE * ", PIXEL, 64, 23)}" fill="#f2eeff"/></g>'
             + '<circle r="24" fill="#030208" stroke="#b895ff" stroke-width="3"/><ellipse rx="46" ry="10" transform="rotate(-18)" fill="none" stroke="#ff8ad8" stroke-width="4"/></g>'
             f'<path d="{nome}" fill="#7224fb" filter="url(#aura)" opacity=".9"/><path d="{nome}" fill="url(#cromo)"/>'
             f'<g clip-path="url(#cnome)" style="mix-blend-mode:color" opacity=".85">{corre(600, h, 9, larg=1200)}</g>'
             '</g>')
    svg("hero", w, h, "Rizu", defs, corpo)


def faixa():
    w, h = 1200, 60
    itens = ["SISTEMAS WEB", "INTEGRAÇÕES", "APPS", "AGENTES DE IA", "INFRA", "REDES"]
    x, d, est = 0, "", ""
    for t in itens:
        d += letras(t, DISPLAY, x, 9, 24)
        x += largura(t, DISPLAY, 24) + 36
        est += estrela(x, 0, 11, TINTA, classe="")
        x += 36
    bloco = f'<path d="{d}" fill="{TINTA}"/>{est}'
    defs = folha_defs(1200) + f'<clipPath id="q"><rect width="{w}" height="{h}" rx="18"/></clipPath>'
    copias = "".join(f'<g transform="translate({x * i:.1f} 0)">{bloco}</g>' for i in range(math.ceil(1300 / x) + 1))
    corpo = (f'<g clip-path="url(#q)"><rect width="{w}" height="{h}" fill="url(#folha)"/>'
             f'<g transform="translate(0 30)"><g style="--w:-{x:.1f}px;animation-duration:30s" class="corre">{copias}</g></g></g>')
    svg("faixa", w, h, ", ".join(itens), defs, corpo)


def titulo(nome, txt):
    w, h, tam = 400, 48, 21
    d = letras(txt, DISPLAY, w / 2, 32, tam, "m")
    m = largura(txt, DISPLAY, tam) / 2 + 26
    defs = folha_defs(400) + f'<clipPath id="t"><path d="{d}"/></clipPath>'
    corpo = (f'<rect width="{w}" height="{h}" rx="24" fill="{FUNDO}"/><g clip-path="url(#t)">{corre(400, h, 10)}</g>'
             + estrela(w / 2 - m, 24, 9, "#ff8ad8") + estrela(w / 2 + m, 24, 9, "#7df9ff", 2))
    svg(nome, w, h, txt, defs, corpo)


# Desenho de cada projeto, em volta da origem, raio de uns 70.
L = 'fill="none" stroke="url(#risco)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"'
EMBLEMAS = {
    "insurge": f'<circle r="38" fill="#030208" stroke="#b895ff" stroke-width="5"/><ellipse rx="72" ry="19" transform="rotate(-18)" {L}/>',
    "orbyta": f'<circle r="18" fill="url(#risco)"/><circle r="42" {L} stroke-opacity=".5"/><circle r="66" {L} stroke-opacity=".5"/>'
              '<g class="gira" style="animation-duration:9s"><circle cx="42" r="10" fill="#7df9ff"/></g><g class="gira" style="animation-duration:15s"><circle cy="66" r="12" fill="#ff8ad8"/></g>',
    "torque": f'<g class="gira" style="animation-duration:24s"><circle r="48" {L}/><circle r="17" {L}/>'
              + "".join(f'<path d="M0 -50V-66" transform="rotate({a})" stroke="#b895ff" stroke-width="16" stroke-linecap="round"/>' for a in range(0, 360, 45)) + "</g>",
    "rizu": f'<g class="gira" style="animation-duration:8s"><circle r="66" fill="#0d0920" stroke="url(#risco)" stroke-width="5"/><path d="M-46 0A46 46 0 0 1 0 -46M46 0A46 46 0 0 1 0 46" {L} stroke-opacity=".6"/><circle r="20" fill="#ff8ad8"/><circle r="5" fill="#06040f"/></g>',
    "solenne": f'<path d="M-62 -46H62Q68 -46 68 -38V28Q68 36 60 36H-8L-36 62V36H-60Q-68 36 -68 28V-38Q-68 -46 -62 -46Z" {L}/>'
               + "".join(estrela(x, -5, 13, c, i) for i, (x, c) in enumerate([(-32, "#7df9ff"), (0, "#ff8ad8"), (32, "#fff3a6")])),
    "quorum": f'<circle cx="0" cy="-26" r="38" {L}/><circle cx="-28" cy="22" r="38" {L}/><circle cx="28" cy="22" r="38" {L}/>',
    "ghostframe": f'<path d="M-66 -34H66V34H26L12 14H-12L-26 34H-66Z" {L}/><path d="M-40 -8H-16M16 -8H40" stroke="#7df9ff" stroke-width="8" stroke-linecap="round"/><path d="M-50 -52H50M-34 -68H34" stroke="#b895ff" stroke-width="7" stroke-linecap="round" stroke-opacity=".6"/>',
}
PROJETOS = [
    ("insurge", "Insurge", "Software sob medida contra o genérico.", "insurge.space"),
    ("orbyta", "Orbyta", "ERP em que cada área é um planeta.", "orbyta.insurge.space"),
    ("torque", "Torque", "Ordem de serviço para oficina.", "insurge.space/torque"),
    ("rizu", "Rizu", "Meu site: discos, animes e rádio.", "rizu.insurge.space"),
    ("solenne", "Solenne", "Minha IA pessoal, no Discord.", "luizhc06/Solenne"),
    ("quorum", "Quorum", "Conselho de IAs que revisa software.", "luizhc06/Quorum"),
    ("ghostframe", "ghostframe", "Frames gerados para VR, em alpha.", "luizhc06/ghostframeVR"),
]


def projeto(chave, nome, linha, onde, w=410, sufixo=""):
    """Cartão baixo. A folga de 4 px nos lados é o espaço entre as colunas no README."""
    h, x2, y2 = 98, w - 4, 97
    defs = (folha_defs(w) + grad("risco", [(0, "#7df9ff"), (45, "#b895ff"), (75, "#ff8ad8"), (100, "#fff3a6")], 1, 1)
            + grad("prata", PRATA)
            + '<radialGradient id="luz"><stop stop-color="#7224fb" stop-opacity=".6"/><stop offset="1" stop-color="#7224fb" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="q"><rect x="4" y="1" width="{w - 8}" height="{h - 2}" rx="20"/></clipPath>')
    corpo = (f'<g clip-path="url(#q)">{corre(w, h, 10)}</g>'
             f'<rect x="5.5" y="2.5" width="{w - 11}" height="{h - 5}" rx="18.5" fill="#0d0920"/>'
             f'<g clip-path="url(#q)"><circle cx="56" cy="49" r="85" fill="url(#luz)"/></g>'
             f'<g transform="translate(56 49) scale(.44)">{EMBLEMAS[chave]}</g>'
             f'<path d="{letras(nome, DISPLAY, 106, 38, 20)}" fill="url(#prata)"/>'
             f'<path d="{letras(linha, TEXTO, 106, 60, 15)}" fill="#cfc8ee"/>'
             f'<path d="{letras(onde, PIXEL, 106, 81, 14, esp=.3)}" fill="#7df9ff"/>')
    svg(f"projeto-{chave}{sufixo}", w, h, f"{nome}: {linha}", defs, corpo)


def projeto_celular(chave, nome, linha, onde, w=205):
    """Versão do celular: só desenho e nome, para caber em duas colunas."""
    h = 58
    defs = (folha_defs(w) + grad("risco", [(0, "#7df9ff"), (45, "#b895ff"), (75, "#ff8ad8"), (100, "#fff3a6")], 1, 1)
            + grad("prata", PRATA) + f'<clipPath id="q"><rect x="3" y="1" width="{w - 6}" height="{h - 2}" rx="16"/></clipPath>')
    corpo = (f'<g clip-path="url(#q)">{corre(w, h, 10)}</g>'
             f'<rect x="4.5" y="2.5" width="{w - 9}" height="{h - 5}" rx="14.5" fill="#0d0920"/>'
             f'<g transform="translate(36 29) scale(.27)">{EMBLEMAS[chave]}</g>'
             f'<path d="{letras(nome, DISPLAY, 62, 34.5, 16)}" fill="url(#prata)"/>')
    svg(f"projeto-{chave}-celular", w, h, f"{nome}: {linha}", defs, corpo)


# (nome, arquivo em scripts/icones, cor da marca). Issabel e MicroSIP não têm logo aberto: ícone genérico.
# Fontes: simple-icons (CC0), selfh.st/icons (CC BY 4.0: zabbix, glpi, aruba) e tabler (MIT: issabel, microsip) e noctalia-shell (noctalia).
STACK = [
    ("Desenvolvimento e gestão", [("Visual Studio", "visualstudio", "#b184f5"), ("GitHub", "github", "#fff"),
                                  ("Notion", "notion", "#fff"), ("Workspace", "google", "#4c8df6")]),
    ("Monitoramento e redes", [("Zabbix", "zabbix", ""), ("Grafana", "grafana", "#f46800"),
                               ("UniFi", "ubiquiti", "#3d8bff"), ("Aruba", "aruba", "")]),
    ("Infra e virtualização", [("OMV", "openmediavault", "#5dacdf"), ("VMware", "vmware", "#9fb4c9"),
                               ("VirtualBox", "virtualbox", "#3f9be0"), ("Proxmox", "proxmox", "#e57000")]),
    ("Telefonia e helpdesk", [("Issabel", "issabel", "#9dffcb"), ("Asterisk", "asterisk", "#f68f1e"),
                              ("MicroSIP", "microsip", "#7df9ff"), ("GLPI", "glpi", "")]),
    ("Segurança e VPN", [("OpenVPN", "openvpn", "#ea7e20"), ("Bitdefender", "bitdefender", "#ed1c24"),
                         ("pfSense", "pfsense", "#8a9bff"), ("Fortinet", "fortinet", "#ee3124")]),
    ("Uso todo dia", [("CachyOS", "cachyos", "#00d1b2"), ("Niri", "niri", "#e88fd0"), ("Noctalia", "noctalia", ""),
                      ("Windows 11", "windows11", "#3fa9f5")]),
    ("Já passei por", [("Debian", "debian", "#e0386e"), ("Arch", "archlinux", "#1793d1"), ("Ubuntu", "ubuntu", "#e95420"),
                       ("Pop!_OS", "popos", "#48b9c7"), ("Kali", "kalilinux", "#5c9dff"), ("Manjaro", "manjaro", "#35bfa4")]),
]


def icone(arquivo, cor, x, y, lado):
    bruto = (RAIZ / "icones" / f"{arquivo}.svg").read_text(encoding="utf-8")
    caixa = re.search(r'viewBox="([^"]+)"', bruto)[1]
    miolo = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", bruto, re.S)[1])
    return f'<svg x="{x:.1f}" y="{y:.1f}" width="{lado}" height="{lado}" viewBox="{caixa}" fill="{cor or "none"}" color="{cor or "#fff"}">{miolo}</svg>'


def stack():
    """Duas colunas de painéis; o último grupo ocupa a linha inteira."""
    w, alt, vao, pw = 812, 106, 8, 402
    itens = []
    for i, (grupo, nomes) in enumerate(STACK):
        ultimo = i == len(STACK) - 1
        px, py, larg = (i % 2) * (pw + vao), (i // 2) * (alt + vao), w if ultimo else pw
        cor = FOLHA[i % 5]
        itens.append(f'<g transform="translate({px} {py})"><rect x="1" y="1" width="{larg - 2}" height="{alt - 2}" rx="18" fill="#0d0920" stroke="{cor}" stroke-opacity=".45" stroke-width="1.5"/>'
                     f'<path d="{letras(grupo, DISPLAY, 20, 26, 13)}" fill="{cor}"/>')
        passo = (larg - 24) / len(nomes)
        for j, (n, arq, c) in enumerate(nomes):
            cx = 12 + passo * (j + .5)
            lado = 54 if arq in ("vmware", "aruba", "glpi") else 32  # logos só de letras, baixos e largos
            itens.append(icone(arq, c, cx - lado / 2, 59 - lado / 2, lado)
                         + f'<path d="{letras(n, TEXTO, cx, 95, 13.5, "m")}" fill="#f2eeff"/>')
        itens.append("</g>")
    h = math.ceil(len(STACK) / 2) * (alt + vao) - vao
    svg("stack", w, h, "Ferramentas que eu uso", "", "".join(itens))


def rodape():
    w, h = 812, 76
    d = letras("Insurgir é recusar o genérico.", DISPLAY, w / 2, 46, 22, "m")
    svg("rodape", w, h, "Insurgir é recusar o genérico.", folha_defs(840) + f'<clipPath id="t"><path d="{d}"/></clipPath>',
        f'<rect width="{w}" height="{h}" rx="20" fill="{FUNDO}"/><g clip-path="url(#t)">{corre(840, h, 10)}</g>'
        + "".join(estrela(x, y, r, c, i) for i, (x, y, r, c) in enumerate([(60, 26, 8, "#7df9ff"), (752, 50, 9, "#ff8ad8")])))


if __name__ == "__main__":
    hero()
    faixa()
    titulo("titulo-projetos", "O que eu construo")
    titulo("titulo-stack", "Com o que eu trabalho")
    titulo("titulo-commits", "Commits no horizonte")
    for p in PROJETOS:
        if p is not PROJETOS[0]:  # o primeiro usa a versão larga
            projeto(*p)
        projeto_celular(*p, w=410 if p is PROJETOS[0] else 205)
    projeto(*PROJETOS[0], w=820, sufixo="-largo")  # sete projetos: o primeiro fecha a grade
    stack()
    rodape()
