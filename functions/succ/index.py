# -*- coding: utf-8 -*-
import logging


def handler(event, context):
    logger = logging.getLogger()
    logger.info('destnation success: {}'.format(event))
    # do your things
    # ...
    return {}
