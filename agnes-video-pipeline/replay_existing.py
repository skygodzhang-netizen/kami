#!/usr/bin/env python3
"""Run the production five-scene merge/verification stages on retained Agnes clips."""
import argparse
import json
import os
import shutil
from datetime import datetime, timezone

from pipeline import PIPELINE_ROOT, inspect
from pipeline_concat import concat, verify, write_report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-batch', required=True)
    args = parser.parse_args()
    source = os.path.realpath(args.source_batch)
    runtime = os.path.realpath(os.path.join(PIPELINE_ROOT, 'runtime'))
    if not source.startswith(runtime + os.sep):
        parser.error('source batch must be inside the existing pipeline runtime')
    scenes = json.load(open(os.path.join(PIPELINE_ROOT, 'scenes.json')))['scenes']
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    batch = os.path.join(runtime, 'replay-existing-' + stamp)
    for subdir in ('videos', 'logs', 'final', 'reports'):
        os.makedirs(os.path.join(batch, subdir), exist_ok=True)
    results = []
    for scene in scenes:
        sid = scene['scene_id']
        prior = os.path.join(source, 'videos', sid + '.mp4')
        if not os.path.isfile(prior) or os.path.getsize(prior) == 0:
            results.append({'scene_id': sid, 'status': 'missing_source', 'error': 'retained clip absent'})
            continue
        current = os.path.join(batch, 'videos', sid + '.mp4')
        shutil.copy2(prior, current)
        result = {'scene_id': sid, 'task_id': 'historical-artifact', 'status': 'completed',
                  'local_file': current, 'file_size': os.path.getsize(current)}
        inspect(result, scene, batch)
        results.append(result)
    merged = concat(results, scenes, batch, target_w=720, target_h=1280, fps=24)
    target = os.path.join(batch, 'final', 'black_clothing_5scene_final.mp4')
    validation = verify(target, 5)
    report = write_report(batch, results, scenes, merged, validation, 'historical-artifacts',
                          manifest_extra={'source_batch': source, 'mode': 'replay-existing-no-provider-submit'})
    summary = {'batch': batch, 'source': source, 'scene_count': len(results),
               'scene_decode_pass': all(r.get('decode', {}).get('exit') == 0 for r in results),
               'merge_method': merged.get('method'), 'merge_count': merged.get('count'),
               'verify_pass': validation.get('pass'), 'final': target,
               'fresh_provider_generation': False}
    with open(os.path.join(batch, 'reports', 'replay-summary.json'), 'w') as file:
        json.dump(summary, file, indent=2)
    print(json.dumps(summary))
    if not summary['scene_decode_pass'] or not summary['verify_pass'] or summary['merge_count'] != 5:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
