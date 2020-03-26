# -*- coding: utf-8 -*-
import logging
import oss2
import os
import time
import json
import subprocess
import shutil

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)

OUTPUT_DST = os.environ["OUTPUT_DST"]

# a decorator for print custom json log of handler
def print_excute_json_log(func):
    def wrapper(*args, **kwargs):
        event, context = args[0], args[1]
        start_time_stamp = time.time()
        ret = func(*args, **kwargs)
        evt = json.loads(event)
        evt = evt["events"]
        oss_bucket_name = evt[0]["oss"]["bucket"]["name"]
        object_key = evt[0]["oss"]["object"]["key"]
        _, extension = get_fileNameExt(object_key)
        size = evt[0]["oss"]["object"]["size"]
        M_size = round(size / 1024.0 / 1024.0, 2)
        end_time_stamp = time.time()
        elapsed_time = end_time_stamp - start_time_stamp
        json_log={
            "request_id": context.request_id,
            "video_name": object_key,
            "video_format": extension[1:],
            "size": M_size,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time_stamp+8*3600)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time_stamp+8*3600)),
            "elapsed_time": elapsed_time,
            "processed_video_location": OUTPUT_DST,
        }
        print(json.dumps(json_log))
        return ret
    return wrapper

def get_fileNameExt(filename):
    (fileDir, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension

@print_excute_json_log
def handler(event, context):
    evt = json.loads(event)
    evt = evt["events"]
    oss_bucket_name = evt[0]["oss"]["bucket"]["name"]
    object_key = evt[0]["oss"]["object"]["key"]
    shortname, extension = get_fileNameExt(object_key)
    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId, creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(auth, 'oss-%s-internal.aliyuncs.com' % context.region, oss_bucket_name)
    input_path = oss_client.sign_url('GET', object_key, 6 * 3600)
    transcoded_filepath = '/tmp/' + shortname + extension
    ts_dir = '/tmp/ts'
    if os.path.exists(ts_dir):
         shutil.rmtree(ts_dir)
    os.mkdir(ts_dir)
    split_transcoded_filepath = os.path.join(ts_dir, shortname + '_%03d.ts')
    cmd1 = ['/code/ffmpeg', '-y', '-threads', '2', '-i', input_path, '-c:v', 'libx264', '-r', '30',
            '-c:a', 'libfdk_aac', '-ab', '800k', '-ar', '44100', transcoded_filepath]
    cmd2 = ['/code/ffmpeg', '-y', '-i', transcoded_filepath, '-c', 'copy', '-map', '0', '-f', 'segment',
            '-segment_list', os.path.join(ts_dir, 'playlist.m3u8'), '-segment_time', '10', split_transcoded_filepath]
    try:
        subprocess.check_call(cmd1)
        subprocess.check_call(cmd2)
    except subprocess.CalledProcessError as exc:
        err_ret = {
            'request_id': context.request_id,
            'returncode': exc.returncode, 
            'cmd': exc.cmd,
            'output': exc.output,
        }
        print(json.dumps(err_ret))

    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    
    for filename in os.listdir(ts_dir):
        filepath = os.path.join(ts_dir,filename)
        filekey = os.path.join(OUTPUT_DST, shortname, filename)
        oss_client.put_object_from_file(filekey, filepath)
        os.remove(filepath)
        print("Uploaded {} to {}".format(filepath, filekey))
    
    return "ok"
