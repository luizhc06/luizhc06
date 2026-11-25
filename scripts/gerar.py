"""Desenha os SVGs de assets/ no visual da Insurge (cromo e folha holográfica).

Uso: pip install fonttools brotli && python scripts/gerar.py
O texto vira contorno porque o GitHub não carrega fonte externa dentro de SVG.
"""
import math
import random
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
    w, h = 1200, 720
    rnd = random.Random(7)
    pontos = "".join(f'<circle cx="{rnd.randint(20, 1180)}" cy="{rnd.randint(20, 690)}" r="{rnd.choice([.8, 1.1, 1.6])}" '
                     f'fill="#f2eeff" opacity="{rnd.uniform(.15, .6):.2f}"/>' for _ in range(110))
    brilhos = "".join(estrela(x, y, r, c, i * .9) for i, (x, y, r, c) in enumerate([
        (110, 130, 13, "#7df9ff"), (250, 270, 8, "#ff8ad8"), (905, 330, 9, "#fff3a6"), (1120, 350, 14, "#9dffcb"),
        (800, 70, 10, "#b895ff"), (60, 330, 8, "#9dffcb"), (380, 60, 7, "#fff3a6"), (1090, 640, 9, "#ff8ad8")]))
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
    tam *= 1090 / largura("RIZU", NEGRO, 100, -2)
    nome = letras("RIZU", NEGRO, 600, 590, tam, "m", -2)
    # o contorno real manda na caixa do degradê, então o horizonte do cromo cai no meio da letra
    tag = letras("Logística de dia, vibe coding com IA", TEXTO, 58, 654, 33)
    tag2 = letras("nas horas vagas.", TEXTO, 58, 696, 33)
    marca = letras("insurge.space", PIXEL, 1142, 696, 30, "f", 1)
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
             '<ellipse cx="600" cy="300" rx="620" ry="380" fill="url(#roxo)"/><ellipse cx="1080" cy="80" rx="480" ry="330" fill="url(#rosa)"/>'
             f'{pontos}<g transform="translate(600 255) rotate(-18)" fill="none" stroke="#9dffcb" stroke-opacity=".26" stroke-width="1.2">{globo}</g>{brilhos}'
             f'<g transform="translate(600 205) rotate(-16)"><g class="boia">'
             f'<path d="{anel}" fill="#b06bff" fill-rule="evenodd" filter="url(#aura)" opacity=".9"/>'
             f'{pinta_anel}<circle r="122" fill="url(#buraco)" stroke="#d075ef" stroke-opacity=".6" stroke-width="1.5"/>'
             f'<g clip-path="url(#frente)">{pinta_anel}</g></g></g>'
             f'<g transform="translate(1075 170)"><circle r="88" fill="{FUNDO}" fill-opacity=".55"/><g class="gira" style="animation-duration:22s"><path d="{em_circulo("CONTRA O GENÉRICO * SOB MEDIDA * INSURGE * ", PIXEL, 64, 23)}" fill="#f2eeff"/></g>'
             + '<circle r="24" fill="#030208" stroke="#b895ff" stroke-width="3"/><ellipse rx="46" ry="10" transform="rotate(-18)" fill="none" stroke="#ff8ad8" stroke-width="4"/></g>'
             f'<path d="{nome}" fill="#7224fb" filter="url(#aura)" opacity=".9"/><path d="{nome}" fill="url(#cromo)"/>'
             f'<g clip-path="url(#cnome)" style="mix-blend-mode:color" opacity=".85">{corre(600, h, 9, larg=1200)}</g>'
             f'<path d="{tag}{tag2}" fill="#f2eeff"/><path d="{marca}" fill="#b895ff"/></g>')
    svg("hero", w, h, "Rizu: logística de dia, vibe coding com IA nas horas vagas", defs, corpo)


def faixa():
    w, h = 1200, 120
    itens = ["SISTEMAS WEB", "INTEGRAÇÕES", "APPS", "AGENTES DE IA", "INFRA", "REDES"]
    x, d, est = 0, "", ""
    for t in itens:
        d += letras(t, DISPLAY, x, 13, 34)
        x += largura(t, DISPLAY, 34) + 45
        est += estrela(x, 0, 14, TINTA, classe="")
        x += 45
    bloco = f'<path d="{d}" fill="{TINTA}"/>{est}'
    defs = folha_defs(1200) + f'<clipPath id="q"><rect width="{w}" height="{h}"/></clipPath>'
    copias = "".join(f'<g transform="translate({x * i:.1f} 0)">{bloco}</g>' for i in range(math.ceil(1300 / x) + 1))
    corpo = (f'<g clip-path="url(#q)"><g transform="rotate(-1.6 600 60)"><g transform="translate(-30 24)">'
             f'<rect width="1260" height="72" fill="url(#folha)"/></g>'
             f'<g transform="translate(0 60)"><g style="--w:-{x:.1f}px;animation-duration:26s" class="corre">{copias}</g></g></g></g>')
    svg("faixa", w, h, ", ".join(itens), defs, corpo)


def titulo(nome, txt):
    w, h, tam = 840, 92, 44
    d = letras(txt, DISPLAY, w / 2, 62, tam, "m", -1)
    m = largura(txt, DISPLAY, tam, -1) / 2 + 45
    defs = folha_defs(840) + f'<clipPath id="t"><path d="{d}"/></clipPath>'
    corpo = (f'<rect width="{w}" height="{h}" rx="20" fill="{FUNDO}"/><g clip-path="url(#t)">{corre(840, h, 10)}</g>'
             + estrela(w / 2 - m, 46, 17, "#ff8ad8") + estrela(w / 2 + m, 46, 17, "#7df9ff", 2))
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
    "boboya": f'<path d="M0 -66L18 -22L66 -18L30 14L42 62L0 36L-42 62L-30 14L-66 -18L-18 -22Z" {L}/><circle cx="-13" cy="2" r="6" fill="#7df9ff"/><circle cx="13" cy="2" r="6" fill="#7df9ff"/><path d="M-9 17Q0 25 9 17" {L.replace("7", "5", 1)}/>',
    "solenne": f'<path d="M-62 -46H62Q68 -46 68 -38V28Q68 36 60 36H-8L-36 62V36H-60Q-68 36 -68 28V-38Q-68 -46 -62 -46Z" {L}/>'
               + "".join(estrela(x, -5, 13, c, i) for i, (x, c) in enumerate([(-32, "#7df9ff"), (0, "#ff8ad8"), (32, "#fff3a6")])),
    "quorum": f'<circle cx="0" cy="-26" r="38" {L}/><circle cx="-28" cy="22" r="38" {L}/><circle cx="28" cy="22" r="38" {L}/>',
    "ghostframe": f'<path d="M-66 -34H66V34H26L12 14H-12L-26 34H-66Z" {L}/><path d="M-40 -8H-16M16 -8H40" stroke="#7df9ff" stroke-width="8" stroke-linecap="round"/><path d="M-50 -52H50M-34 -68H34" stroke="#b895ff" stroke-width="7" stroke-linecap="round" stroke-opacity=".6"/>',
}
PROJETOS = [
    ("insurge", "Insurge", ["Software sob medida", "contra o genérico."], "insurge.space"),
    ("orbyta", "Orbyta", ["ERP em que cada área da", "operação é um planeta."], "orbyta.insurge.space"),
    ("torque", "Torque", ["Ordem de serviço para", "oficina e serralheria."], "insurge.space/torque"),
    ("rizu", "Rizu", ["Meu site: buraco negro,", "discos, animes e rádio."], "rizu.insurge.space"),
    ("boboya", "BOBOYA", ["Loja de merch de anime", "em estética Y2K."], "boboya.insurge.space"),
    ("solenne", "Solenne", ["Minha IA pessoal,", "morando no Discord."], "luizhc06/Solenne"),
    ("quorum", "Quorum", ["Conselho de IAs que", "revisa software."], "luizhc06/Quorum"),
    ("ghostframe", "ghostframe", ["Geração de frames para", "VR em streaming, em alpha."], "luizhc06/ghostframeVR"),
]


def projeto(chave, nome, linhas, onde):
    w, h = 600, 300
    defs = (folha_defs(600) + grad("risco", [(0, "#7df9ff"), (45, "#b895ff"), (75, "#ff8ad8"), (100, "#fff3a6")], 1, 1, 'gradientUnits="objectBoundingBox"')
            + grad("prata", PRATA)
            + '<radialGradient id="luz"><stop stop-color="#7224fb" stop-opacity=".55"/><stop offset="1" stop-color="#7224fb" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="borda"><path clip-rule="evenodd" d="M26 0H574A26 26 0 0 1 600 26V274A26 26 0 0 1 574 300H26A26 26 0 0 1 0 274V26A26 26 0 0 1 26 0ZM27 4A23 23 0 0 0 4 27V273A23 23 0 0 0 27 296H573A23 23 0 0 0 596 273V27A23 23 0 0 0 573 4Z"/></clipPath>'
            '<clipPath id="q"><rect width="600" height="300" rx="26"/></clipPath>')
    corpo = (f'<g clip-path="url(#q)"><rect width="{w}" height="{h}" fill="#0d0920"/><circle cx="490" cy="105" r="240" fill="url(#luz)"/></g>'
             f'<g clip-path="url(#borda)">{corre(600, h, 8)}</g>'
             f'<g transform="translate(490 105)">{EMBLEMAS[chave]}</g>'
             f'<path d="{letras(nome, DISPLAY, 36, 92, 46, esp=-1)}" fill="url(#prata)"/>'
             + "".join(f'<path d="{letras(t, TEXTO, 36, 160 + i * 39, 30)}" fill="#cfc8ee"/>' for i, t in enumerate(linhas))
             + f'<path d="{letras(onde, PIXEL, 36, 262, 28, esp=.5)}" fill="#7df9ff"/>')
    svg(f"projeto-{chave}", w, h, f"{nome}: {' '.join(linhas)}", defs, corpo)


STACK = [
    ("Desenvolvimento e gestão", ["Visual Studio", "GitHub", "Notion", "Google Workspace"]),
    ("Monitoramento e redes", ["Zabbix", "Grafana", "Ubiquiti UniFi", "Aruba Networks"]),
    ("Infraestrutura e virtualização", ["OpenMediaVault", "VMware", "VirtualBox", "Proxmox"]),
    ("Telefonia e helpdesk", ["Issabel", "Asterisk", "MicroSIP", "GLPI"]),
    ("Segurança e VPN", ["OpenVPN", "Bitdefender", "pfSense", "Fortinet"]),
    ("Uso todo dia", ["Garuda Linux", "Windows 11"]),
    ("Já passei por", ["Debian", "Arch Linux", "Ubuntu", "Mint", "Kali Linux", "Manjaro"]),
]


def stack():
    w, y, itens = 840, 56, []
    for i, (grupo, nomes) in enumerate(STACK):
        cor = FOLHA[i % 5]
        itens.append(f'<path d="{letras(grupo, DISPLAY, 36, y, 23)}" fill="{cor}"/>')
        x, y = 36, y + 22
        for n in nomes:
            lw = largura(n, TEXTO, 25) + 40
            if x + lw > w - 36:
                x, y = 36, y + 60
            itens.append(f'<rect x="{x:.0f}" y="{y}" width="{lw:.0f}" height="48" rx="24" fill="#150c33" stroke="{cor}" stroke-opacity=".55" stroke-width="1.5"/>'
                         f'<path d="{letras(n, TEXTO, x + 20, y + 33, 25)}" fill="#f2eeff"/>')
            x += lw + 12
        y += 104
    h = y - 22
    svg("stack", w, h, "Ferramentas que eu uso",
        '<radialGradient id="luz"><stop stop-color="#7224fb" stop-opacity=".4"/><stop offset="1" stop-color="#7224fb" stop-opacity="0"/></radialGradient>',
        f'<rect width="{w}" height="{h}" rx="26" fill="{FUNDO}"/><ellipse cx="760" cy="{h / 2:.0f}" rx="420" ry="{h * .5:.0f}" fill="url(#luz)" clip-path="inset(0 round 26px)"/>' + "".join(itens))


def rodape():
    w, h = 840, 150
    d = letras("Insurgir é recusar o genérico.", DISPLAY, w / 2, 92, 38, "m", -1)
    svg("rodape", w, h, "Insurgir é recusar o genérico.", folha_defs(840) + f'<clipPath id="t"><path d="{d}"/></clipPath>',
        f'<rect width="{w}" height="{h}" rx="26" fill="{FUNDO}"/><g clip-path="url(#t)">{corre(840, h, 10)}</g>'
        + "".join(estrela(x, y, r, c, i) for i, (x, y, r, c) in enumerate([(60, 34, 9, "#7df9ff"), (780, 118, 10, "#ff8ad8"), (420, 126, 7, "#fff3a6")])))


if __name__ == "__main__":
    hero()
    faixa()
    titulo("titulo-projetos", "O que eu construo")
    titulo("titulo-stack", "Com o que eu trabalho")
    titulo("titulo-commits", "Commits no horizonte")
    for p in PROJETOS:
        projeto(*p)
    stack()
    rodape()
