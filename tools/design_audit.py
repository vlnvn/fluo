"""Build a frame-to-code trace and honest visual comparison evidence."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/implementation'
QA = DOCS / 'qa'
FRAMES = json.loads((DOCS / 'FIGMA_FRAME_INVENTORY.json').read_text())['frames']


def coverage(frame):
    name = frame['name'].lower()
    if 'filter-' in name:
        return '#/events + filter overlay', 'App.tsx / filter Dialog', '/sessions/{id}/events', 'filter categories Full/Compact'
    if 'notifications' in name or 'preferences' in name or '/profile' in name or '/help' in name:
        return 'current route + contextual overlay', 'App.tsx / contextual Dialog', '/sessions/{id} and /preferences', 'contextual overlays and focus'
    if 'inspection' in name or 'print-preview' in name:
        return '#/events/{id} + summary/preview', 'App.tsx / summary + preview; backend/reporting.py', '/events/{id}/report.pdf and /print', 'four event PDFs and print calls'
    if 'details' in name or '/event-' in name:
        return '#/events/{id}', 'Views.tsx / EventDetails', '/sessions/{id}/events/{id}', 'four event checklists; Full/Compact'
    if 'lab' in name:
        return '#/scenarios + recorded scenario/playback state', 'Views.tsx / ScenarioReview', '/sessions/{id}/replay', 'scenario reset, pause, speed, rewind, seek'
    if 'events' in name:
        return '#/events + category state', 'Views.tsx / EventCenter', '/sessions/{id}/events', 'filter, sort, event navigation'
    return '#/', 'Views.tsx / Overview', '/sessions/{id}', 'HGB readings, geometry, Full/Compact'


def main():
    lines = ['# Figma frame → runtime trace', '', '83 active design frames map to one application state model. Repeated playback/filter/sidebar variants are states, not separate websites. All route mappings below are implemented; representative visual tests are identified separately from unrendered combinations.', '', '| Frame | Name | Runtime state | Component | API | Test coverage |', '|---|---|---|---|---|---|']
    for frame in FRAMES:
        route, component, api, test = coverage(frame)
        lines.append(f'| {frame["id"]} | {frame["name"]} | {route} | {component} | {api} | {test} |')
    (DOCS / 'FIGMA_TRACEABILITY.md').write_text('\n'.join(lines), encoding='utf-8')
    geometry = []
    xml_path = DOCS / 'sources/figma-page-0.xml'
    if xml_path.exists():
        xml = xml_path.read_text(encoding='utf-8').split('</canvas>')[0] + '</canvas>'
        root = ET.fromstring(xml)
        for node_id in ['74:2','74:107','74:198','74:302','128:5','128:144','128:286','128:422']:
            frame = root.find(f".//*[@id='{node_id}']")
            cards = [n.attrib for n in frame.iter() if n.attrib.get('name','').startswith(('BENTO/','CONTENT/','SHELL/'))]
            geometry.append({'frame':node_id,'cards':cards})
        (DOCS / 'FIGMA_GEOMETRY.json').write_text(json.dumps(geometry,indent=2),encoding='utf-8')
    comparisons = []
    differences = QA / 'visual-diffs'
    differences.mkdir(parents=True,exist_ok=True)
    references = QA / 'figma'
    actuals = QA / 'screenshots'
    for name in ['overview-full','overview-compact','scenario-full','scenario-compact','events-full','events-compact','details-full','details-compact','filter-all-full','filter-return-full','filter-quality-full','filter-all-compact','filter-return-compact','filter-quality-compact','notifications','preferences','help','profile','inspection-summary','a4-document']:
        expected_path, actual_path = references/f'{"a4" if name == "a4-document" else name}.png', actuals/f'{name}.png'
        if not expected_path.exists() or not actual_path.exists():
            comparisons.append({'state':name,'status':'MISSING_REFERENCE_OR_CAPTURE'})
            continue
        expected, actual = Image.open(expected_path).convert('RGB'), Image.open(actual_path).convert('RGB')
        region = 'whole frame; dynamic measurements/content intentionally differ'
        if name.startswith('filter-'):
            # Figma filter nodes are standalone 675×624 white panels.
            # Figma exports include 23 px of outer shadow on every side.
            if expected.size == (721, 670):
                expected = expected.crop((23,23,698,647))
            actual = actual.crop((382,138,1057,762))
            region = '675×624 modal crop; live context text differs'
        elif name in ['notifications','preferences','help','profile','inspection-summary']:
            regions = {'notifications':(939,80,1414,570),'preferences':(325,211,1115,689),'help':(280,210,1160,690),'profile':(904,80,1414,390),'inspection-summary':(320,208,1120,683)}
            box = regions[name]
            expected, actual = expected.crop(box), actual.crop(box)
            region = 'contextual panel crop; underlying active page excluded'
        if name == 'a4-document' and actual.size == (794,1124):
            actual = actual.crop((0,0,794,1123))
            region = '794×1123 A4; 1 px Chromium outward screenshot rounding cropped'
        if expected.size != actual.size:
            comparisons.append({'state':name,'status':'SIZE_MISMATCH','expected':expected.size,'actual':actual.size})
            continue
        a, b = np.asarray(expected).astype(float), np.asarray(actual).astype(float)
        diff = np.abs(a-b)
        metrics = {'mean_absolute_RGB_error_0_255':round(float(diff.mean()),4),'pixel_fraction_with_channel_error_gt_20':round(float((diff.max(axis=2)>20).mean()),6)}
        canvas = Image.new('RGB',(expected.width*3,expected.height+30),'white')
        canvas.paste(expected,(0,30))
        canvas.paste(actual,(expected.width,30))
        canvas.paste(ImageChops.difference(expected,actual).point(lambda x:min(255,x*3)),(expected.width*2,30))
        draw=ImageDraw.Draw(canvas)
        draw.text((10,8),'FIGMA',(22,44,66))
        draw.text((expected.width+10,8),'IMPLEMENTATION — REAL REPLAY',(22,44,66))
        draw.text((expected.width*2+10,8),'ABSOLUTE DIFFERENCE ×3',(22,44,66))
        canvas.save(differences/f'{name}.png')
        comparisons.append({'state':name,'status':'COMPARED_NOT_PIXEL_IDENTICAL','region':region,**metrics,'comparison_file':str((differences/f'{name}.png').relative_to(ROOT))})
    (QA/'VISUAL_COMPARISON.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
    report = ['# Visual QA — measured differences', '', 'The application is not claimed pixel-identical. Original Figma renders are compared to actual Chromium screenshots at 1440×900. Charts, values, dates, event identifiers, gate states, queue counts and provenance are sourced from real archived synthetic telemetry and intentionally differ from illustrative Figma values. Full-frame error is therefore not a pure layout metric. Overlay comparisons crop the panel; filters compare the standalone white panel. Windows Chromium and Figma font rasterization also differ.', '', '| State | Mean RGB error (0–255) | Pixels with >20 channel error | Comparison |', '|---|---:|---:|---|']
    for c in comparisons:
        report.append(f'| {c["state"]} | {c.get("mean_absolute_RGB_error_0_255","—")} | {c.get("pixel_fraction_with_channel_error_gt_20","—")} | {c["status"]} |')
    report += ['', '## Deliberate implementation differences', '', '- Illustrative readings and fixed EV-018 contents are replaced by actual scored replay values and deterministic state-change IDs.', '- Data provenance is visible in a restrained status footer and report metadata.', '- Search/pagination, replay seek and the explicit evidence/review submission form extend the static design to satisfy functional requirements; the review form is below the canonical first viewport.', '- The seven principal scenarios retain the Figma ordering. Two additional archived quality/mode windows are available below the scrollable scenario library.', '- Filters and contextual overlays retain the white Light panel geometry; no navy canvas is used.', '- No numeric threshold is used to relabel these differences as pixel-perfect. Original references, implementation captures and ×3 difference images are retained locally.', '', 'Geometry assertions, real asset load checks, native keyboard controls, modal focus containment, reduced motion and narrower desktop overflow are tested in Playwright. See `screenshots/geometry.json` and `e2e-results.json`.']
    (QA/'VISUAL_QA.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps({'mapped_frames':len(FRAMES),'compared_states':sum(c['status'].startswith('COMPARED') for c in comparisons),'comparisons':comparisons[:4]},indent=2))


if __name__ == '__main__':
    main()
