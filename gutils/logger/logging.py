"""
logger
"""
import logging

def get_logger(name=""):
    """
    获取日志记录器。
    Parameters
    ----------
    name (str): 日志记录器的名称，默认为""。
    Returns
    -------
        logging.Logger: 日志记录器。
    """
    logger = logging.getLogger(name=name)
    logger.setLevel(level=logging.DEBUG)
    # handler
    f_hdlr = logging.FileHandler(filename=f"{name}.log", mode="w" )
    f_hdlr.setLevel(level=logging.DEBUG)
    c_hdlr = logging.StreamHandler()
    c_hdlr.setLevel(level=logging.INFO)
    # formatter
    fmt = logging.Formatter(fmt="%(asctime)-s  "
                                "%(levelname)-s  "
                                "%(name)-s  "
                                "%(filename)-s  "
                                "%(funcName)-s  "
                                "Line: %(lineno)-s  "
                                "Msg: %(message)s  ",
                            datefmt="%Y-%m-%d %H:%M:%S")
    f_hdlr.setFormatter(fmt)
    c_hdlr.setFormatter(fmt)
    logger.addHandler(hdlr=f_hdlr)
    logger.addHandler(hdlr=c_hdlr)
    return logger