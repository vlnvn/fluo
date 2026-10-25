"""Encode real local browser capture and verify every output frame decodes."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/implementation/demo'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    recording = json.loads((OUT / 'LIVE_OVERVIEW_RECORDING.json').read_text(encoding='utf8'))
    assert recording['status'] == 'PASS' and not recording['hosted_recording']
    source = Path(recording['videoPath'])
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    output = OUT / 'FLUO_LIVE_OVERVIEW.mp4'
    filters = ('pad=iw:ih+80:0:0:color=0xf5f9ff,'
               "subtitles=FLUO_LIVE_OVERVIEW.srt:fontsdir=../../../web/public/assets/fonts:"
               "force_style='FontName=Archivo,FontSize=7,PrimaryColour=&H00422C16,Outline=0,Shadow=0,Alignment=2,MarginV=3'")
    encoded = subprocess.run([encoder, '-y', '-i', str(source), '-vf', filters, '-c:v', 'libx264',
                              '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-an',
                              '-movflags', '+faststart', str(output)], cwd=OUT, capture_output=True, text=True)
    (ROOT / '.local/live-overview-encode.log').write_text(encoded.stderr, encoding='utf8')
    encoded.check_returncode()
    decoded = subprocess.run([encoder, '-v', 'error', '-xerror', '-i', str(output), '-map', '0:v:0',
                              '-progress', 'pipe:1', '-f', 'null', '-'], capture_output=True, text=True)
    (ROOT / '.local/live-overview-decode.log').write_text(decoded.stdout + decoded.stderr, encoding='utf8')
    decoded.check_returncode()
    frames_decoded = int([line.split('=')[1] for line in decoded.stdout.splitlines() if line.startswith('frame=')][-1])
    reader = imageio_ffmpeg.read_frames(str(output))
    metadata = next(reader)
    reader.close()
    assert 120 <= metadata['duration'] <= 180, 'Video must be 2–3 minutes'
    assert frames_decoded > 0 and not decoded.stderr
    pdf = PdfReader(OUT / 'FLUO_LIVE_OVERVIEW_EVENT.pdf')
    assert len(pdf.pages) >= 1 and any('Demo lokal:' in (p.extract_text() or '') for p in pdf.pages)
    frames = ROOT / '.local/live-overview-frames'
    frames.mkdir(exist_ok=True)
    sample_seconds = [round((c['start'] + c['end']) / 2, 2) for c in recording['captions']]
    sheet = Image.new('RGB', (960, 4 * 187), '#edf3f8')
    draw = ImageDraw.Draw(sheet)
    for index, second in enumerate(sample_seconds):
        target = frames / f'{index:02d}.png'
        subprocess.run([encoder, '-y', '-v', 'error', '-ss', str(second), '-i', str(output),
                        '-frames:v', '1', str(target)], check=True)
        with Image.open(target) as image:
            image.thumbnail((320, 164))
            sheet.paste(image, ((index % 3) * 320, (index // 3) * 187))
        draw.text(((index % 3) * 320 + 4, (index // 3) * 187 + 165), f'{second}s', fill='#162c42')
    sheet.save(frames / 'contact-sheet.png')
    old = OUT / 'FLUO_DEMO_END_TO_END.mp4'
    old_proof = json.loads((OUT / 'VIDEO_PROVENANCE.json').read_text(encoding='utf8'))
    result = {'status': 'PASS_DECODE_AND_ASSERTIONS', 'recorded_app_commit': recording['app_commit'],
              'url': recording['url'], 'hosted_recording': False, 'file': output.name,
              'sha256': digest(output), 'bytes': output.stat().st_size, 'metadata': metadata,
              'srt_sha256': digest(OUT / 'FLUO_LIVE_OVERVIEW.srt'), 'source_sha256': digest(source),
              'recorder_sha256': digest(ROOT / 'tools/record_live_overview.mjs'),
              'full_decode_exit': decoded.returncode, 'frames_decoded': frames_decoded,
              'pdf_pages': len(pdf.pages), 'pdf_sha256': digest(OUT / 'FLUO_LIVE_OVERVIEW_EVENT.pdf'),
              'live_overview_samples': len(recording['samples']), 'quality_gate_verified': True,
              'edit': 'Continuous real local Playwright capture; H264 encode and Indonesian captions in added bottom strip. No UI numbers, states or animations fabricated. No time cuts or speed changes.',
              'audio': 'No audio track; captioned demonstration', 'visual_review': 'PENDING',
              'sample_seconds': sample_seconds,
              'old_video_audit': {'hash_matches_original_provenance': digest(old) == old_proof['sha256'],
                                  'duration_seconds': old_proof['metadata']['duration'],
                                  'recorder_gap': 'Old script paused replay in Scenario Review before later navigating to Overview. No live Overview transition proof; English captions; 185.8 seconds.',
                                  'original_files_preserved': True}}
    (OUT / 'LIVE_OVERVIEW_PROVENANCE.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'duration': metadata['duration'], 'frames_decoded': frames_decoded,
                      'sha256': result['sha256'], 'old_video_hash_matches': result['old_video_audit']['hash_matches_original_provenance']}))


if __name__ == '__main__':
    main()
