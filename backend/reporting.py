"""Event-specific A4 reports using the current Figma report geometry."""
import io
from datetime import datetime, timezone
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from .inference_adapter import ROOT

ASSETS = ROOT / 'web/public/assets'


def measured(value, unit):
    return 'Unavailable' if value is None else f'{value:.1f} {unit}'


def report_data(detail):
    event, frame = detail['event'], detail['frame']
    is_return = event['category'] == 'return'
    return {
        'status': 'INVESTIGATE - UNCONFIRMED' if is_return else 'DATA / MODE CHECK',
        'observation': 'Condensate return deviation observed during production. Meter verification is required before determining a physical cause.' if is_return else 'A data or operating-mode transition was recorded. Verify measurement availability and valid history before interpreting the return signal.',
        'readings': [('Steam feed', measured(frame['readings']['steam_kg_h'], 'kg/h')), ('Condensate return', measured(frame['readings']['return_kg_h'], 'kg/h')), ('Steam pressure', measured(frame['readings']['pressure_barg'], 'bar(g)'))],
        'qualification': [('Time', event['timestamp']), ('Signature score', 'Withheld / insufficient evidence' if frame['inference']['score'] is None else f"{frame['inference']['score']:.6f} (uncalibrated; not cause probability)"), ('Operating mode', frame['operating_mode'].capitalize()), ('Meter validity', frame['quality_action']), ('Physical cause', 'Unconfirmed / independent verification required')],
    }


def pdf_report(detail):
    data = report_data(detail)
    event, review = detail['event'], detail['review']
    out = io.BytesIO()
    canvas = Canvas(out, pagesize=A4)
    canvas.setTitle(f"Fluo inspection {event['id']}")
    canvas.setAuthor('Fluo local research workspace')
    canvas.setSubject(f"Simulated research telemetry; model SHA256={detail['lineage']['model_sha256']}; dataset SHA256={detail['lineage']['dataset_sha256']}")
    for weight in (400, 600):
        name = f'Archivo-{weight}'
        path = ASSETS / f'fonts/archivo-{weight}.ttf'
        if name not in pdfmetrics.getRegisteredFontNames() and path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))
    fonts = {400: 'Archivo-400' if 'Archivo-400' in pdfmetrics.getRegisteredFontNames() else 'Helvetica', 600: 'Archivo-600' if 'Archivo-600' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'}
    scale = A4[0] / 794
    canvas.scale(scale, scale)
    height = A4[1] / scale

    def rect(x, y, width, tall, fill, radius=0, stroke=None):
        canvas.setFillColor(colors.HexColor(fill))
        canvas.setStrokeColor(colors.HexColor(stroke or fill))
        canvas.setLineWidth(.7)
        if radius:
            canvas.roundRect(x, height-y-tall, width, tall, radius, fill=1, stroke=bool(stroke))
        else:
            canvas.rect(x, height-y-tall, width, tall, fill=1, stroke=bool(stroke))

    def text(value, x, y, width=698, size=13, weight=400, color='#162c42', max_height=100):
        style = ParagraphStyle('A4', fontName=fonts[weight], fontSize=size, leading=size*1.45, textColor=colors.HexColor(color))
        paragraph = Paragraph(escape(str(value)), style)
        _, actual_height = paragraph.wrap(width, max_height)
        paragraph.drawOn(canvas, x, height-y-actual_height)
        return actual_height

    def line(y):
        canvas.setStrokeColor(colors.HexColor('#dbe7f3'))
        canvas.setLineWidth(.7)
        canvas.line(48, height-y, 746, height-y)

    rect(0, 0, 794, 126, '#f1f7fd')
    brand = ASSETS / 'report-brand.png'
    if brand.exists():
        canvas.drawImage(str(brand), 46, height-91, 128, 60, mask='auto')
    text('INSPECTION SUMMARY', 228, 43, 510, 20, 600)
    text(f"Event {event['id']} / Condensate return", 228, 78, 510, 13, color='#50657b')
    line(148)
    text('PT Arunika Tekstil', 48, 166, 443, 24, 600)
    text('Pabrik Bandung / Unit Sizing A', 48, 206, 442, 15, color='#50657b')
    rect(512, 164, 235, 38, '#fff2e6', 8)
    text(data['status'], 524, 175, 215, 11, 600, '#a65a11')
    text('OBSERVATION', 48, 266, 360, 14, 600, '#1d52c4')
    text(data['observation'], 48, 298, 685, 14)
    for index, (label, value) in enumerate(data['readings']):
        x = 48+236*index
        rect(x, 381, 221, 105, '#f4f9ff', 10, '#dce8f5')
        text(label, x+14, 397, 200, 12, color='#50657b')
        text(value, x+14, 429, 201, 23, 600)
    text('EVIDENCE & QUALIFICATION', 48, 526, 698, 14, 600, '#1d52c4')
    for index, (label, value) in enumerate(data['qualification']):
        y = 558+39*index
        text(label, 48, y, 225, 12, color='#50657b')
        text(value, 282, y, 464, 11.5)
        line(y+28)
    text('RECOMMENDED VERIFICATION', 48, 779, 698, 14, 600, '#1d52c4')
    for index, step in enumerate(review['steps']):
        y = 817+38*index
        canvas.setStrokeColor(colors.HexColor('#9cb7d4'))
        canvas.setLineWidth(.8)
        canvas.rect(50, height-y-14, 14, 14, fill=0, stroke=1)
        if step['checked']:
            text('x', 52, y-3, 12, 13, 600, '#1d52c4')
        text(step['label'], 79, y-2, 650, 12)
    text(f"Operator review: {review['status']} / {review['operator_label']} / revision {review['revision']}", 48, 972, 698, 9, color='#50657b')
    rect(48, 1004, 698, 72, '#eef5fd', 10)
    text('SAFETY & CONTROL', 61, 1014, 670, 12, 600, '#1d52c4')
    text('Decision support only. No automatic equipment actuation or recovery is authorized. Simulated research telemetry; fictional facility; no industrial validation.', 61, 1038, 665, 10)
    line(1090)
    text(f"Model SHA-256: {detail['lineage']['model_sha256']}", 48, 1095, 698, 6, color='#50657b')
    text(f"Dataset SHA-256: {detail['lineage']['dataset_sha256']}", 48, 1105, 698, 6, color='#50657b')
    canvas.showPage()
    # Long notes and the audit trail get a real appendix instead of overlapping
    # the fixed A4 summary. Scientific metadata stays in the PDF itself.
    if review['note'] or review['audit']:
        canvas.scale(scale, scale)
        y = 50
        y += text(f"Inspection review record / {event['id']}", 48, y, 698, 22, 600)+20
        y += text(f"Operator: {review['operator_label']} / authenticated: false", 48, y, 698, 12)+10
        y += text(f"Submitted: {review['submitted_at'] or 'Not submitted'}", 48, y, 698, 12)+15
        if review['note']:
            y += text('Evidence / note', 48, y, 698, 14, 600)+10
            y += text(review['note'], 48, y, 698, 12, max_height=700)+20
        y += text('Audit trail', 48, y, 698, 14, 600)+10
        for item in review['audit']:
            if y > 990:
                canvas.showPage()
                canvas.scale(scale, scale)
                y = 50
            y += text(f"{item['at']} / {item['action']} / revision {item['revision']}", 48, y, 698, 10)+8
        text(f"Generated: {datetime.now(timezone.utc).isoformat()}", 48, min(y+15,1070), 698, 9, color='#50657b')
    canvas.save()
    return out.getvalue()


def html_report(detail, session_id, embedded=False):
    data = report_data(detail)
    event, review = detail['event'], detail['review']

    def e(value):
        return escape(str(value), quote=True)

    readings = ''.join(f'<section class="kpi" style="left:{48+236*i}px"><span>{e(label)}</span><strong>{e(value)}</strong></section>' for i, (label, value) in enumerate(data['readings']))
    qualification = ''.join(f'<div class="evidence-row"><span>{e(label)}</span><strong>{e(value)}</strong></div>' for label, value in data['qualification'])
    steps = ''.join(f'<li><span class="box">{"✓" if step["checked"] else ""}</span>{e(step["label"])}</li>' for step in review['steps'])
    appendix = ''
    if review['note'] or review['audit']:
        audit = ''.join(f'<li>{e(item["at"])} / {e(item["action"])} / revision {item["revision"]}</li>' for item in review['audit'])
        appendix = f'<article class="appendix"><h2>Inspection review record / {e(event["id"])}</h2><p>{e(review["operator_label"])} / {e(review["status"])}</p><p>{e(review["note"])}</p><p>Submitted: {e(review["submitted_at"] or "Not submitted")}</p><ul>{audit}</ul></article>'
    toolbar_style = '.tools{display:none!important}' if embedded else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Fluo inspection {e(event['id'])}</title><style>
{toolbar_style}
@font-face{{font-family:Archivo;src:url('/assets/fonts/archivo-400.ttf') format('truetype');font-weight:400}}@font-face{{font-family:Archivo;src:url('/assets/fonts/archivo-600.ttf') format('truetype');font-weight:600}}*{{box-sizing:border-box}}body{{margin:0;background:#eaf1f8;color:#162c42;font:13px/1.45 Archivo,Arial,sans-serif}}h1,h2,p{{margin:0}}.tools{{padding:12px;display:flex;justify-content:center;gap:12px}}button{{background:#1d52c4;color:white;border:0;border-radius:8px;padding:10px 18px;cursor:pointer;font:inherit}}article{{background:white;width:794px;height:1123px;position:relative;margin:0 auto 20px;box-shadow:0 5px 25px #263e6220}}.header-band{{height:126px;background:#f1f7fd}}.brand{{position:absolute;left:46px;top:31px}}h1{{position:absolute;left:228px;top:43px;font-size:20px;font-weight:600;text-transform:uppercase}}.event-id{{position:absolute;left:228px;top:78px;font-size:13px;color:#50657b}}.divider{{position:absolute;left:48px;right:48px;top:148px;border-top:1px solid #dbe7f3}}.facility{{position:absolute;left:48px;top:166px;font-size:24px;font-weight:600}}.facility-detail{{position:absolute;left:48px;top:206px;font-size:15px;color:#50657b}}.status{{position:absolute;left:512px;top:164px;width:235px;height:38px;background:#fff2e6;border-radius:8px;color:#a65a11;padding:11px 12px;font-size:11px;font-weight:600}}h2{{font-size:14px;font-weight:600;color:#1d52c4}}.observation-heading{{position:absolute;left:48px;top:266px}}.observation{{position:absolute;left:48px;top:298px;width:685px;font-size:14px}}.kpi{{position:absolute;top:381px;width:221px;height:105px;background:#f4f9ff;border:1px solid #dce8f5;border-radius:10px;padding:16px 14px}}.kpi span{{font-size:12px;color:#50657b}}.kpi strong{{display:block;margin-top:18px;font-size:23px;font-weight:600}}.evidence-heading{{position:absolute;left:48px;top:526px}}.evidence{{position:absolute;left:48px;right:48px;top:555px}}.evidence-row{{height:39px;border-bottom:1px solid #dbe7f3;display:grid;grid-template-columns:234px 1fr;align-items:start;padding-top:3px;font-size:12px}}.evidence-row span{{color:#50657b}}.evidence-row strong{{font-weight:400;font-size:11.5px}}.verification-heading{{position:absolute;left:48px;top:779px}}.steps{{position:absolute;left:50px;right:48px;top:814px;list-style:none;padding:0;margin:0}}.steps li{{height:38px;display:flex;align-items:flex-start;gap:15px;font-size:12px}}.box{{border:1px solid #9cb7d4;width:15px;height:15px;display:inline-grid;place-items:center;color:#1d52c4;font-size:12px}}.review-status{{position:absolute;left:48px;top:972px;font-size:9px;color:#50657b}}.safety{{position:absolute;top:1004px;left:48px;right:48px;height:72px;background:#eef5fd;border-radius:10px;padding:10px 13px}}.safety h2{{font-size:12px}}.safety p{{font-size:10px;margin-top:10px}}footer{{position:absolute;left:48px;right:48px;top:1090px;border-top:1px solid #dbe7f3;padding-top:5px;font-size:6px;color:#50657b;overflow-wrap:anywhere}}.appendix{{padding:48px;height:auto;min-height:1123px;overflow-wrap:anywhere}}.appendix h2{{font-size:22px;margin-bottom:25px}}.appendix p{{margin:15px 0;white-space:pre-wrap}}@page{{size:A4;margin:0}}@media print{{body{{background:white}}.tools{{display:none}}article{{margin:0;box-shadow:none;width:210mm;height:297mm;break-after:page;break-inside:avoid}}article:last-child{{break-after:auto}}.appendix{{height:auto;min-height:297mm}}}}</style></head><body><div class="tools"><button id="print">Print A4</button><button id="back">Back to summary</button><button id="close">Close</button></div><main><article aria-label="A4 inspection summary"><div class="header-band"></div><img class="brand" src="/assets/ReportOriginalBrandVector.svg" alt="Fluo"><h1>Inspection summary</h1><p class="event-id">Event {e(event['id'])} / Condensate return</p><div class="divider"></div><p class="facility">PT Arunika Tekstil</p><p class="facility-detail">Pabrik Bandung / Unit Sizing A</p><div class="status">{e(data['status'])}</div><h2 class="observation-heading">OBSERVATION</h2><p class="observation">{e(data['observation'])}</p>{readings}<h2 class="evidence-heading">EVIDENCE &amp; QUALIFICATION</h2><div class="evidence">{qualification}</div><h2 class="verification-heading">RECOMMENDED VERIFICATION</h2><ul class="steps">{steps}</ul><p class="review-status">Operator review: {e(review['status'])} / {e(review['operator_label'])} / revision {review['revision']}</p><section class="safety"><h2>SAFETY &amp; CONTROL</h2><p>Decision support only. No automatic equipment actuation or recovery is authorized. Simulated research telemetry; fictional facility; no industrial validation.</p></section><footer>Model SHA-256: {e(detail['lineage']['model_sha256'])}<br>Dataset SHA-256: {e(detail['lineage']['dataset_sha256'])}</footer></article>{appendix}</main><script>document.getElementById('print').onclick=()=>window.print();document.getElementById('close').onclick=()=>{{if(window.opener)window.close();else history.back()}};document.getElementById('back').onclick=()=>{{if(window.opener){{window.opener.focus();window.close()}}else history.back()}};</script></body></html>'''
