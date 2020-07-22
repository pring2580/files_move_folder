# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import datetime
import traceback
import threading
import re
import subprocess
import shutil
import json
import ast
import time
import urllib
import rclone

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery
from framework.job import Job
from framework.util import Util
from system.model import ModelSetting as SystemModelSetting
from framework.logger import get_logger

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelItem

import cgitb
cgitb.enable(format='text')

#synoindex 호출용
from urlparse import urlparse

class LogicNormal(object):
    @staticmethod
    @celery.task
    def scheduler_function():
        try:
            #logger.debug("파일정리 시작!")
            source_path = ModelSetting.get('source_path')
            download_path = ModelSetting.get('download_path')
            noname_path = ModelSetting.get('noname_path')
            #logger.debug("source_path >> %s", source_path);
            #logger.debug("download_path >> %s", download_path);
            #logger.debug("noname_path >> %s", noname_path);
	    if source_path != '' and download_path != '' and noname_path != '':
               LogicNormal.file_move(source_path, download_path, noname_path)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def file_move(source_path, download_path, noname_path):
       logger.debug("=========== SCRIPT START ===========")
       #전달받은 path 경로에 / 없는 경우 예외처리
       if source_path.rfind("/")+1 != len(source_path):
          source_path = source_path+'/'

       if download_path.rfind("/")+1 != len(download_path):
          download_path = download_path+'/'

       if noname_path.rfind("/")+1 != len(noname_path):
          noname_path = noname_path+'/'

       ROOT_PATH = source_path
       FILE_PATH = download_path
       NO_NAME_PATH = noname_path
       
       #필수 폴더 존재하는 경우만 진행
       if os.path.isdir(ROOT_PATH) and os.path.isdir(FILE_PATH) and os.path.isdir(NO_NAME_PATH):
           #검색 제외 리스트
           exclude = ['@eaDir']
           #이동할 파일 조회(파일, 폴더내 파일)
           fileList = os.listdir(FILE_PATH)
           
           for file in fileList:
              mvBool = True
              for ex in exclude:
                  #시스템폴더 패스
                  if ex == file:
                      mvBool = False
              #예외파일명 아니면 이동처리
              if mvBool:
                 #파일이동처리
                 log("이동할 파일명 : %s", file)
                 #프로그램명으로 폴더 생성
                 directory = file.split('.')[0]
                 directory = ROOT_PATH+directory
                 try:
                     if not os.path.isdir(directory): 
                        os.makedirs(directory)
                 except OSError:
                     log("Error: Creating directory." + directory)
                 
                 #log("이동처리할 경로 : %s", FILE_PATH+file)
                 #이동할 file명 조회(폴더인 경우 대비)
                 if os.path.isfile(FILE_PATH+file):
                    log("파일 : %s", FILE_PATH+file)
                    fileName = file.split('.')[0]
                    #log("fileDate : %s", fileDate)
                    if os.path.isdir(ROOT_PATH+fileName):
                       log("### 파일이동처리 시작 ###")
                       log("이동할 파일명 : %s", file)
                       log("이동할 경로 : %s", directory)
                       shutil.move(FILE_PATH+file, directory+'/'+file)
                       log("### 파일이동처리 완료 ###")
                    else:
                       #no_name로 이동
                       shutil.move(FILE_PATH+file, NO_NAME_PATH+file)
                 #폴더처리 시작
                 elif os.path.isdir(FILE_PATH+file):
                 #else:
                    #폴더내 파일이동 후 삭제할 폴더
                    delete_path = FILE_PATH+file
                    log("delete_path : %s", delete_path)
       	           #while start
                    while True:
                       filepath = get_lastfile(file)
                       if filepath == '':
                          break;
                       file_info = os.path.split(filepath)
                       file_name = file_info[1]
                       #이름에 해당하는 폴더 있으면 이동
                       fileName = file_name.split('.')[0]
                       #log("fileDate : %s", fileDate)
                       if os.path.isdir(ROOT_PATH+fileName):
                           log("### 파일이동처리 시작 ###")
                           log("이동할 파일명 : %s", file)
                           log("이동할 경로 : %s", directory)
                           shutil.move(FILE_PATH+file, directory+'/'+file)
                           log("### 파일이동처리 완료 ###")
                       else:
                           #no_name로 이동
                           shutil.move(FILE_PATH+file, NO_NAME_PATH+file)
              	     #while end
              	     #폴더 삭제
                    if not delete_path == '':
                       remove_dir(delete_path)
                 #폴더 처리 완료
       else:
          logger.debug("폴더 존재하지 않으므로 진행하지 않습니다.")
          logger.debug("라이브러리경로 : %s", ROOT_PATH)
          logger.debug("다운로드 경로 : %s", FILE_PATH)
          logger.debug("날짜없는파일 처리 경로 : %s", NO_NAME_PATH)
       
       
       logger.debug("=========== SCRIPT END ===========")

    @staticmethod
    def remove_dir(path):
       shutil.rmtree(path)

    @staticmethod
    def get_lastfile(file):
       #파일이 나올때까지 반복
       full_filename = ""
       dirname = file
       for (path, dir, files) in os.walk(dirname):
          for filename in files:
             #synology 썸네일폴더 제외
             if path.find("@eaDir") < 0 :
                full_filename = path+'/'+filename
       return full_filename

    @staticmethod
    def get_whichday(date):
       r=['월','화','수','목','금','토','일']
       year = int(date[0:2])
       month = int(date[2:4])
       date = int(date[4:6])
       aday=datetime.date(year,month,date)
       bday=aday.weekday()
       return r[bday]