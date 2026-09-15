"""Refresh frozen Unreal test inputs from validated Blender pose evidence.

Standard Python only. Does not run Blender, import C++ output, or synthesize
target matrices. Geometry-only source updates must retain the same controller
and numerically equivalent reference targets before provenance is refreshed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
POSES = ROOT / 'artifacts/sode01/pose-review.json'
SOURCE_VALIDATION = ROOT / 'artifacts/sode01/source-validation.json'
FIXTURE = ART / 'Scripts/suspension-reference-poses.json'
COMPARISON = ROOT / 'artifacts/sode01/suspension-fixture-refresh.json'
TARGET_KEYS = ('opening_cm', 'lift_clearance_cm', 'direction', 'target_blender_cm',
    'upper_reference_blender_cm', 'shoulder_blender_cm', 'elbow_blender_cm', 'torso_delta_blender_cm')
POSE_NAMES = ('neutral', 'arms-forward', 'arms-raised', 'bow-diagnostic', 'A_Idle:15', 'A_Idle:110',
    'A_Walk:8', 'A_Walk:23', 'A_Walk:37', 'A_Run:8', 'A_Run:23', 'A_Run:40',
    'A_Attack:6', 'A_Attack:12', 'A_Attack:20', 'A_Attack:28')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric_difference(old, new):
    if isinstance(old, list) and isinstance(new, list):
        require(len(old) == len(new), 'Numeric reference shape changed')
        return max((numeric_difference(a, b) for a, b in zip(old, new)), default=0.)
    require(type(old) in (int, float) and type(new) in (int, float), 'Non-numeric reference value')
    require(math.isfinite(old) and math.isfinite(new), 'Nonfinite reference value')
    return abs(old-new)


def make_fixture():
    report = json.loads(POSES.read_text())
    validation = json.loads(SOURCE_VALIDATION.read_text())
    previous = json.loads(FIXTURE.read_text())
    source_sha, motion_sha = sha(ART / 'Sode01.blend'), sha(ART / 'Scripts/sode_motion.py')
    require(report.get('validated') is True and report.get('controlled_rigid_suspension') is True
        and report.get('source_file_unchanged') is True, 'Need a successful full controlled Blender pose report')
    require(report['source_sha256'] == source_sha, 'Pose report does not match the current authoritative source')
    require(report['motion_script_sha256'] == motion_sha == previous['motion_script_sha256'],
        'Controller changed or pose evidence is stale; refresh cannot replace controller regression expectations')
    require(validation.get('validated') is True and validation['source']['sha256'] == source_sha,
        'Need successful source validation for this exact Blender source')
    require(validation['preserved_manny']['identical_bone_hierarchy'] and
        validation['preserved_manny']['matches_native_fixture_hash'], 'Native Manny reference identity is unverified')
    checks = report['checks']
    require([check['pose'] for check in checks] == list(POSE_NAMES), 'Expected the complete sixteen-pose Blender measurement')
    neutral = checks[0]['suspension_targets']
    old_samples = {(sample['pose'], sample['side']): sample for sample in previous['samples']}
    require(len(old_samples) == 32, 'Existing immutable reference must contain 32 unique side/pose pairs')
    samples, differences = [], []
    for check in checks:
        require(set(check['suspension_targets']) == {'l', 'r'}, 'Each Blender pose must contain both anatomical sides')
        for side in ('l', 'r'):
            target = check['suspension_targets'][side]
            sample = {key: target[key] for key in TARGET_KEYS}
            sample.update({'pose': check['pose'], 'frame': check['frame'], 'side': side,
                'elbow_reference_blender_cm': neutral[side]['elbow_blender_cm']})
            old = old_samples[(sample['pose'], side)]
            difference = max(numeric_difference(old[key], sample[key])
                for key in (*TARGET_KEYS, 'elbow_reference_blender_cm', 'frame'))
            differences.append({'pose': sample['pose'], 'side': side, 'maximum_numeric_change': difference})
            require(difference <= .0001, 'Geometry-only update changed the frozen target: ' + sample['pose'] + ' ' + side)
            samples.append(sample)
    fixture = {'description': previous['description'], 'source_blend_sha256': source_sha,
        'motion_script_sha256': motion_sha, 'pose_review_sha256': sha(POSES),
        'source_validation_sha256': sha(SOURCE_VALIDATION),
        'provenance': 'Numerical arrays copied only from the validated Blender pose report; never generated from C++ results',
        'samples': samples}
    comparison = {'validated': True, 'previous_fixture_sha256': sha(FIXTURE),
        'previous_source_blend_sha256': previous['source_blend_sha256'],
        'source_blend_sha256': source_sha, 'motion_script_sha256': motion_sha,
        'pose_review': str(POSES.relative_to(ROOT)), 'pose_review_sha256': sha(POSES),
        'generator_sha256': sha(Path(__file__)), 'source_validation_sha256': sha(SOURCE_VALIDATION),
        'sample_count': len(samples), 'maximum_numeric_change': max(item['maximum_numeric_change'] for item in differences),
        'comparison_tolerance': .0001, 'comparisons': differences}
    return fixture, comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Validate freshness and equivalence without writing either file')
    args = parser.parse_args()
    fixture, comparison = make_fixture()
    if not args.check_only:
        FIXTURE.write_text(json.dumps(fixture, indent=2, allow_nan=False) + '\n')
        comparison['refreshed_fixture_sha256'] = sha(FIXTURE)
        COMPARISON.write_text(json.dumps(comparison, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'sample_count': comparison['sample_count'],
        'maximum_numeric_change': comparison['maximum_numeric_change'],
        'written': not args.check_only, 'fixture': str(FIXTURE.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
