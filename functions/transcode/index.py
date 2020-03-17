# -*- coding: utf-8 -*-
import logging
import oss2
import os
import time
import json
import subprocess

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)

OUTPUT_DST = os.environ["OUTPUT_DST"]
DST_TARGET = os.environ["DST_TARGET"]

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
    transcoded_filepath = '/tmp/' + shortname + DST_TARGET
    cmd = ["/code/ffmpeg", "-y", "-i", input_path, "-vf", "scale=640:480", "-b:v", "800k", "-bufsize", "800k", transcoded_filepath]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        err_ret = {
            'request_id': context.request_id,
            'returncode': exc.returncode, 
            'cmd': exc.cmd,
            'output': exc.output,
        }
        print(json.dumps(err_ret))

    oss_client.put_object_from_file(OUTPUT_DST + shortname + DST_TARGET , transcoded_filepath)
    
    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    
    return "ok"
