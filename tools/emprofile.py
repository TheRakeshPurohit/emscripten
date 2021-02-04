#!/usr/bin/env python3
# Copyright 2016 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import json
import os
import shutil
import sys
import tempfile
import time

profiler_logs_path = os.path.join(tempfile.gettempdir(), 'emscripten_toolchain_profiler_logs')

# If set to 1, always generates the output file under the same filename and doesn't delete the temp data.
DEBUG_EMPROFILE_PY = 0


# Deletes all previously captured log files to make room for a new clean run.
def delete_profiler_logs():
  if os.path.exists(profiler_logs_path):
    shutil.rmtree(profiler_logs_path)


def list_files_in_directory(d):
  files = []
  if os.path.exists(d):
    for i in os.listdir(d):
      f = os.path.join(d, i)
      if os.path.isfile(f):
        files.append(f)
  return files


def create_profiling_graph(outfile):
  log_files = [f for f in list_files_in_directory(profiler_logs_path) if 'toolchain_profiler.pid_' in f]

  all_results = []
  if len(log_files):
    print(f'Processing {len(log_files)} profile log files in {profiler_logs_path}...')
  for log_file in log_files:
    print(f'Processing: {log_file}')
    with open(log_file) as f:
      json_data = f.read()
    lines = json_data.split('\n')
    lines = [x for x in lines if x != '[' and x != ']' and x != ',' and len(x.strip())]
    lines = [(x + ',') if not x.endswith(',') else x for x in lines]
    lines[-1] = lines[-1][:-1]
    json_data = '[' + '\n'.join(lines) + ']'
    try:
      all_results += json.loads(json_data)
    except json.JSONDecodeError as e:
      print(str(e), file=sys.stderr)
      print('Failed to parse JSON file "' + f + '"!', file=sys.stderr)
      return 1
  if len(all_results) == 0:
    print(f'No profiler logs were found in path: ${profiler_logs_path}.\nTry setting the environment variable EM_PROFILE_TOOLCHAIN=1 and run some emcc commands, then re-run "emprofile.py --graph".', file=sys.stderr)
    return 1

  all_results.sort(key=lambda x: x['time'])

  json_file = outfile + '.json'
  open(json_file, 'w').write(json.dumps(all_results, indent=2))
  print(f'Wrote {json_file}')

  html_file = outfile + '.html'
  template_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'toolchain_profiler.results_template.html')
  with open(template_file) as f:
    html_contents = f.read().replace('{{{results_log_file}}}', f'"{json_file}"')
  with open(html_file, 'w') as f:
    f.write(html_contents)
  print('Wrote "' + html_file + '"')

  if not DEBUG_EMPROFILE_PY:
    delete_profiler_logs()

  return 0


def main(args):
  if len(args) < 2:
    print('''\
Usage:
       emprofile.py --reset
         Deletes all previously recorded profiling log files.

       emprofile.py --graph
         Draws a graph from all recorded profiling log files.

Optional parameters:

        --outfile=x.html
          Specifies the name of the results file to generate.
  ''')
    return 1

  if '--reset' in args:
    delete_profiler_logs()
  elif '--graph' in args:
    outfile = 'toolchain_profiler.results_' + time.strftime('%Y%m%d_%H%M')
    for arg in args:
      if arg.startswith('--outfile='):
        outfile = arg.split('=', 1)[1].strip().replace('.html', '')
    return create_profiling_graph(outfile)
  else:
    print('Unknown command "' + args[1] + '"!')
    return 1

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
