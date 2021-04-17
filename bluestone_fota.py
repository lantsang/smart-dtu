'''

File: bluestone_fota.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import uos
import fota
import app_fota
import ujson
import utime
import log
import _thread

from usr import bluestone_common
from misc import Power

log.basicConfig(level = log.INFO)
_fota_log = log.getLogger("FOTA")

class BluestoneFOTA(object):
    inst = None

    def __init__(self):
        BluestoneFOTA.inst = self

        self.file_dir_name = r'/usr/fireware'

    '''
    1. 先根据差分固件包的Url地址下载差分固件包文件
    2. 然后将差分固件包文件升级
    详情参考：https://python.quectel.com/doc/doc/Advanced_development/zh/QuecPythonInterface/FOTA_binary_upgrade.html
    '''
    def _download_fota(self, fireware_url):
        file_name = self._download_one_file(fireware_url)
        file_exist = bluestone_common.BluestoneCommon.check_file_exist(file_name)
        if not file_exist:
            _fota_log.error("Cannot download fireware file from '{}'".format(download_url))
            return
        
        fota_obj = fota()
        file_size = uos.stat(file_name)[6]
        with open(file_name, "rb") as f:
            while True:
                count = f.read(1024)
                if not count:
                    break
                fota_obj.write(count, file_size)
            
        _fota_log.info("Flush fireware and verify...")
        res = fota_obj.verify()
        if res != 0:
            _fota_log.error("Fireware verify failed ")
        
        _fota_log.info("Fireware was downloaded, restarting system to take effect")
        utime.sleep_ms(2000)
        Power.powerRestart()

    def _get_download_list(self, download_url_list):
        if not download_url_list or len(download_url_list) <= 0:
            _fota_log.error("Download url list is null or empty")
            return None
        result = []
        for download_url in download_url_list:
            download_url = download_url.replace('https', 'http')
            is_url = bluestone_common.BluestoneCommon.is_url(download_url)
            _fota_log.info("Download url is {}".format(download_url))
            if not is_url:
                _fota_log.error("'{}' is not a valid url".format(download_url))
                return
            file_name = '/usr/' + download_url.split('/')[-1]
            result.append({"url": download_url, "file_name": file_name})
        return result

    def _download_fota_app(self, download_url_list):
        fota = app_fota.new()
        download_list = self._get_download_list(download_url_list)
        if not download_list or len(download_list) <= 0:
            return
        
        result = fota.bulk_download(download_list)
        if result and len(result) > 0:
            _fota_log.error("Cannot download files, the error is {}".format(result))
            return
        
        fota.set_update_flag()
        utime.sleep_ms(1000)

        _fota_log.info("User application files were downloaded, restarting system to take effect")
        Power.powerRestart()

    def _download_one_file(self, download_url):
        download_url = download_url.replace('https', 'http')

        fota = app_fota.new()
        is_url = bluestone_common.BluestoneCommon.is_url(download_url)
        if not is_url:
            _fota_log.error("'{}' is not a valid url".format(download_url))
            return
        file_name = '/usr/' + download_url.split('/')[-1]
        _fota_log.info("Download url is {}, file name is {}".format(download_url, file_name))

        fota.download(download_url, file_name)
        return file_name

    def _download_fota_file(self, download_url):
        file_name = self._download_one_file(download_url)
        file_exist = bluestone_common.BluestoneCommon.check_file_exist(file_name)
        if file_exist:
            fota.set_update_flag()
            utime.sleep_ms(1000)

            _fota_log.info("User application file was downloaded, restarting system to take effect")
            Power.powerRestart()
        else:
            _fota_log.error("Cannot download file from '{}'".format(download_url))

    def start_fota_file(self, download_url):
        _fota_log.info("Start a new thread to download fota file")
        _thread.start_new_thread(self._download_fota_file, ([download_url]))
    
    def start_fota_app(self, download_url_list):
        _fota_log.info("Start a new thread to download fota files")
        _thread.start_new_thread(self._download_fota_app, ([download_url_list]))

    def start_fota_firmware(self, fireware_url):
        _fota_log.info("Start a new thread to download fota fireware")
        _thread.start_new_thread(self._download_fota, ([fireware_url]))
        