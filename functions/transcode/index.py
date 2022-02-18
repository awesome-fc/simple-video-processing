# -*- coding: utf-8 -*-
import logging
import oss2
import os
import json
import subprocess
import shutil

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)
LOGGER = logging.getLogger()


def get_fileNameExt(filename):
    (_, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension


def handler(event, context):
    LOGGER.info(event)
    evt = json.loads(event)
    oss_bucket_name = evt["bucket"]
    object_key = evt["object"]
    output_dir = evt["output_dir"]
    dst_format = evt['dst_format']
    shortname, _ = get_fileNameExt(object_key)
    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId,
                        creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(auth, 'oss-%s-internal.aliyuncs.com' %
                             context.region, oss_bucket_name)

    # simplifiedmeta = oss_client.get_object_meta(object_key)
    # size = float(simplifiedmeta.headers['Content-Length'])
    # M_size = round(size / 1024.0 / 1024.0, 2)

    input_path = oss_client.sign_url('GET', object_key, 6 * 3600)
    # m3u8 特殊处理
    rid = context.request_id
    if dst_format == "m3u8":
        return handle_m3u8(rid, oss_client, input_path, shortname, output_dir)
    else:
        return handle_common(rid, oss_client, input_path, shortname, output_dir, dst_format)


def handle_m3u8(request_id, oss_client, input_path, shortname, output_dir):
    ts_dir = '/tmp/ts'
    if os.path.exists(ts_dir):
        shutil.rmtree(ts_dir)
    os.mkdir(ts_dir)
    transcoded_filepath = os.path.join('/tmp', shortname + '.ts')
    split_transcoded_filepath = os.path.join(
        ts_dir, shortname + '_%03d.ts')
    cmd1 = ['ffmpeg', '-y', '-i', input_path, '-c:v',
            'libx264', transcoded_filepath]
    cmd2 = ['ffmpeg', '-y', '-i', transcoded_filepath, '-f', 'segment',
            '-segment_list', os.path.join(ts_dir, 'playlist.m3u8'), '-segment_time', '10', split_transcoded_filepath]
    try:
        subprocess.run(
            cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        subprocess.run(
            cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        for filename in os.listdir(ts_dir):
            filepath = os.path.join(ts_dir, filename)
            filekey = os.path.join(output_dir, shortname + "-m3u8", filename)
            oss_client.put_object_from_file(filekey, filepath)
            os.remove(filepath)
            print("Uploaded {} to {}".format(filepath, filekey))

    except subprocess.CalledProcessError as exc:
        # if transcode fail，trigger invoke dest-fail function
        raise Exception(request_id +
                        " transcode failure, detail: " + str(exc))

    finally:
        if os.path.exists(ts_dir):
            shutil.rmtree(ts_dir)

        # remove ts 文件
        if os.path.exists(transcoded_filepath):
            os.remove(transcoded_filepath)

    return {}


def handle_common(request_id, oss_client, input_path, shortname, output_dir, dst_format):
    transcoded_filepath = os.path.join('/tmp', shortname + '.' + dst_format)
    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)
    cmd = ["ffmpeg", "-y", "-i", input_path, transcoded_filepath]
    try:
        subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        oss_client.put_object_from_file(
            os.path.join(output_dir, shortname + '.' + dst_format), transcoded_filepath)
    except subprocess.CalledProcessError as exc:
        # if transcode fail，trigger invoke dest-fail function
        raise Exception(request_id +
                        " transcode failure, detail: " + str(exc))
    finally:
        if os.path.exists(transcoded_filepath):
            os.remove(transcoded_filepath)

    return {}
