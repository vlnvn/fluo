"""Encode the actual browser recording; retain source and explicit limitations."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/implementation/demo'


def main():
    recording = json.loads((OUT / 'RECORDING.json').read_text())
    source = Path(recording['videoPath'])
    if not source.is_absolute():
        source = OUT / source
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    output = OUT / 'FLUO_DEMO_END_TO_END.mp4'
    filters = ('pad=iw:ih+80:0:0:color=0xf5f9ff,'
               "subtitles=FLUO_DEMO_END_TO_END.srt:fontsdir=../../../web/public/assets/fonts:"
               "force_style='FontName=Archivo,FontSize=7,PrimaryColour=&H00422C16,Outline=0,Shadow=0,Alignment=2,MarginV=3'")
    encoded = subprocess.run([encoder, '-y', '-i', str(source), '-vf', filters,
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                              '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(output)],
                             cwd=OUT, capture_output=True, text=True)
    (ROOT / '.local/demo-encode.log').write_text(encoded.stderr, encoding='utf-8')
    encoded.check_returncode()
    decoded = subprocess.run([encoder, '-v', 'error', '-i', str(output), '-f', 'null', '-'],
                             capture_output=True, text=True)
    (ROOT / '.local/demo-decode.log').write_text(decoded.stderr, encoding='utf-8')
    decoded.check_returncode()
    reader = imageio_ffmpeg.read_frames(str(output))
    metadata = next(reader)
    reader.close()
    frames = OUT / 'frames'
    frames.mkdir(exist_ok=True)
    for second in (5, 18, 58, 83, 100, 124, 143, 156, 163, 182):
        subprocess.run([encoder, '-y', '-v', 'error', '-ss', str(second), '-i', str(output),
                        '-frames:v', '1', str(frames / f'{second:03d}.png')], check=True)
    recording['videoPath'] = str(source.relative_to(OUT)).replace('\\', '/')
    recording['recorderSha256'] = hashlib.sha256((ROOT / 'tools/record_demo.mjs').read_bytes()).hexdigest()
    recording['recorderWorkingTreeNote'] = 'Checkbox awaits async server-confirmed state; recorder modified after recorded app commit. App code unchanged.'
    (OUT / 'RECORDING.json').write_text(json.dumps(recording, indent=2), encoding='utf-8')
    result = {'source': recording['videoPath'], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'file': output.name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'bytes': output.stat().st_size, 'metadata': metadata, 'full_decode_exit': decoded.returncode,
              'decode_stderr': decoded.stderr, 'audio': 'muted; no audio track',
              'edit': 'One continuous real browser capture; H264 encode and captions in added bottom strip. No UI frames fabricated.',
              'visual_review': 'PENDING', 'public_deployment': False}
    (OUT / 'VIDEO_PROVENANCE.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
