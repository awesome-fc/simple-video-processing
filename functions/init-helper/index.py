# -*- coding: utf-8 -*-
import logging
import os
import time
from aliyun.log import *
import json

def handler(event, context):
    endpoint = "{}.log.aliyuncs.com".format(context.region)
    creds = context.credentials
    client = LogClient(endpoint, creds.accessKeyId,
                       creds.accessKeySecret, creds.securityToken)
    
    evt = json.loads(event)
    project = evt['project']
    access_logs = "access-logs"
    function_logs = "function-logs"
    
    # update function-logs index
    print("create function-logs index ...")
    token_list = [',', ' ', "'", '"', ';', '=', '(', ')', '[', ']', '{',  '}',
                  '?', '@', '&', '<', '>', '/', ':', '\n', '\t', '\r']
    line_config = IndexLineConfig(token_list, True, chinese=True)
    key_config_list = {"message": IndexKeyConfig(token_list, True, chinese=True)}
    index_detail = IndexConfig(10, line_config, key_config_list)
    res = client.update_index(project, function_logs, index_detail)
    res.log_print()
    
    time.sleep(5) # wait all log resource ready
    print("start create dashboard for project {} ...".format(event))
    
    # create dashboard
    with open("dashboard.json") as f:
        dashboard_detail = f.read()
        res = client.create_dashboard(
            project, dashboard_detail)
        res.log_print()




    
