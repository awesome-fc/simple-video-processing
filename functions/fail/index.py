# -*- coding: utf-8 -*-
import logging


def handler(event, context):
    logger = logging.getLogger()
    logger.info('destnation fail: {}'.format(event))
    # do your things
    # ...
    return {}
