"""Create static TTFs from the exact bundled Archivo font; retain OFL."""
from pathlib import Path
from shutil import copy2
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'web/node_modules/@fontsource-variable/archivo'
font_path=source/'files/archivo-latin-wght-normal.woff2'
out=ROOT/'web/public/assets/fonts'
out.mkdir(parents=True,exist_ok=True)
for weight in (400,500,600):
    font=TTFont(font_path)
    font=instantiateVariableFont(font,{'wght':weight},inplace=True)
    font.flavor=None
    font.save(out/f'archivo-{weight}.ttf')
for name in ('OFL.txt','LICENSE'):
    if (source/name).exists():
        copy2(source/name,out/name)
print('Prepared original Archivo report font weights 400/500/600')
