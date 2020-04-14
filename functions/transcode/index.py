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

def get_fileNameExt(filename):
    (fileDir, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension

def get_beijing_time_str(utc_time_stamp):
    local_time = time.localtime(utc_time_stamp + 8*3600)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (utc_time_stamp - int(utc_time_stamp)) * 1000
    beijing_time_str = "%s.%03d" % (data_head, data_secs)
    return beijing_time_str

def handler(event, context):
    utc_now = time.time()
    evt = json.loads(event)
    evt = evt["events"]
    oss_bucket_name = evt[0]["oss"]["bucket"]["name"]
    object_key = evt[0]["oss"]["object"]["key"]
    size = evt[0]["oss"]["object"]["size"]
    shortname, extension = get_fileNameExt(object_key)
    M_size = round(size / 1024.0 / 1024.0, 2)
    json_log = {
        "request_id": context.request_id,
        "video_name": object_key,
        "video_format": extension[1:],
        "size": M_size,
        "start_time": get_beijing_time_str(utc_now),
        "processed_video_location": OUTPUT_DST,
    }
    print(json.dumps(json_log))
   
    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId, creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(auth, 'oss-%s-internal.aliyuncs.com' % context.region, oss_bucket_name)
    input_path = oss_client.sign_url('GET', object_key, 6 * 3600)
    transcoded_filepath = '/tmp/' + shortname + DST_TARGET
    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    cmd = ["/code/ffmpeg", "-y", "-i", input_path, "-vf", "scale=640:480", "-b:v", "800k", "-bufsize", "800k", transcoded_filepath]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exc:
        err_ret = {
            'request_id': context.request_id,
            'returncode': exc.returncode,
            'cmd': exc.cmd,
            'output': exc.output.decode(),
            'stderr': exc.stderr.decode(),
            'event': evt,
        }
        print(json.dumps(err_ret))
        # if transcode fail， send event to mns queue or insert in do db
        # ...
        raise Exception(context.request_id + " transcode failure")
        return

    oss_client.put_object_from_file(
        os.path.join(OUTPUT_DST, shortname + DST_TARGET), transcoded_filepath)
    
    # if transcode succ， send event to mns queue or insert in do db
    # ...

    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    
    return "ok"
