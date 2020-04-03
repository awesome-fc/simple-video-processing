# -*- coding: utf-8 -*-
import logging
import oss2
import os
import time
import json
import subprocess
import shutil
from mns.account import Account
from mns.queue import *

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)

accid = "<your ak id>"
acckey = "<your ak secret>"
# internal endpoint, if region is not same, remove internal
endpoint = "http://<your uid>.mns.<your region>-internal.aliyuncs.com/"
my_mns_account = Account(endpoint, accid, acckey)
queue_name = "<your queue>"
my_queue = my_mns_account.get_queue(queue_name)

def send_mns_msg(msg_body):
    msg = Message(msg_body)
    try:
        re_msg = my_queue.send_message(msg)
        print("Send Message Succeed! MessageBody:%s MessageID:%s" %
              (msg_body, re_msg.message_id))
    except MNSExceptionBase as e:
        print("Send Message Fail! Exception:%s\n" % e)

def get_fileNameExt(filename):
    (fileDir, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension

def handler(event, context):
    start_time_stamp = time.time()
    evt = json.loads(event)
    oss_bucket_name = evt["bucket"]
    object_key = evt["object"]
    OUTPUT_DST = evt["output_dir"]
    shortname, extension = get_fileNameExt(object_key)
    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId, creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(auth, 'oss-%s-internal.aliyuncs.com' %
                             context.region, oss_bucket_name)
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
            'event': evt,
        }
        print(json.dumps(err_ret))
        # if transcode fail， send event to mns queue or insert in do db
        # ...
        send_mns_msg(json.dumps({
            'request_id': context.request_id,
            'result': "fail",
            'event': evt,
        }))
        raise Exception(context.request_id + " transcode failure")
        return

    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    
    for filename in os.listdir(ts_dir):
        filepath = os.path.join(ts_dir,filename)
        filekey = os.path.join(OUTPUT_DST, shortname, filename)
        oss_client.put_object_from_file(filekey, filepath)
        os.remove(filepath)
        print("Uploaded {} to {}".format(filepath, filekey))
        
    # if transcode succ， send event to mns queue or insert in do db
    # ...
    send_mns_msg(json.dumps({
        'request_id': context.request_id,
        'result': "succ",
        'event': evt,
    }))
        
    simplifiedmeta = oss_client.get_object_meta(object_key)
    size = float(simplifiedmeta.headers['Content-Length'])
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
    
    return "ok"
