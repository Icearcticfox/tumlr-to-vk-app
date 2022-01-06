import logging as log

log_format = (
    '[%(asctime)s] %(levelname)-8s %(message)s')
    # '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

log.basicConfig(
    level=log.DEBUG,
    format=log_format,
    #filename=('debug.log'),
)

logger = log.getLogger(__name__)

# logger.debug('debug')
# logger.info('info')
# logger.warning('warning')
# logger.error('error')
# logger.critical('critical')