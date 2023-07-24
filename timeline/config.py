from pathlib import Path

timeline_paths = [
    Path('/Users/nicolas/Downloads'),
]
timeline_metadata_path = Path('/tmp/timeline')

output_path = Path(__file__).parent.parent / 'output'

timeline_includerules = {'*'}
timeline_ignorerules = set()
