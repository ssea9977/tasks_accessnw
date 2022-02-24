import os
import getpass
from subprocess import CREATE_NO_WINDOW
import win32com.client as win32
import time
import sys
import chromedriver_autoinstaller
from PyQt5.QtWidgets import *
from PyQt5 import uic
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
from datetime import datetime, timedelta

# 패키지 없으면 설치(selenium, datetime)
# try:
#     from selenium import webdriver
#     from selenium.webdriver.common.keys import Keys
#     from selenium.webdriver.common.alert import Alert
#     from selenium.webdriver.chrome.service import Service
# except:
#     print("selenium Not Installed")
#     install_code = 'pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org selenium'
#     os.system(install_code)
#     time.sleep(30)
#     from selenium import webdriver
#     from selenium.webdriver.common.keys import Keys
#     from selenium.webdriver.common.alert import Alert
#     from selenium.webdriver.chrome.service import Service
# try:
#     from datetime import datetime, timedelta
# except:
#     print("datetime Not Installed")
#     install_code = 'pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org datetime'
#     os.system(install_code)
#     time.sleep(30)
#     from datetime import datetime, timedelta

# UI for .exe
form_main = uic.loadUiType('siteinfo.ui')[0]


class WindowClass(QMainWindow, form_main):
    #초기화 메서드 
    def __init__(self): 
        super().__init__() 
        self.setupUi(self) 
        #pushButton (시작버튼)을 클릭하면 아래 fuctionStart 메서드와 연결 됨. 
        self.pushButton.clicked.connect(self.fileformat)

    # KPOP 크롤링 후 파일 변환 함수
    def fileformat(self):
        # webdriver headless 상태에서 다운로드 함수
        def enable_download_headless(browser,download_dir):
            browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
            browser.execute("send_command", params)
        self.progressBar.setRange(0, 5)
        self.progressBar.setValue(0)
        # 본인 ID/PW
        kpop_id = ''
        kpop_pw = ''
        username = getpass.getuser()
        path = 'C:/Users/' + username + '/Downloads/'
        driver_path = chromedriver_autoinstaller.install()

        # 어제 날짜 구하기(offloading 파일 다운을 위한)
        today = datetime.today().strftime('%Y-%m-%d')
        yesterday = datetime.today() - timedelta(1)
        input_date = yesterday.strftime('%Y%m%d')

        # chromedriver load(headless mode)
        service = Service(driver_path)
        service.creationflags = CREATE_NO_WINDOW
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument('--no-sandbox')
        options.add_argument('--verbose')
        options.add_experimental_option("prefs", {
            "download.default_directory": 'C:\\Users\\' + username + '\\Downloads',
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--headless')

        # driver = webdriver.Chrome(path + 'chromedriver_win32/chromedriver', chrome_options=options)
        # enable_download_headless(driver, path)
        driver = webdriver.Chrome(driver_path, chrome_options=options, service=service)
        enable_download_headless(driver, driver_path)
        driver.implicitly_wait(3)
        self.progressBar.setValue(1)
        # KPOP 접속
        driver.get('http://172.21.27.207/index.html')

        # KPOP 로그인
        driver.find_element_by_name('ps_id').send_keys(kpop_id)
        driver.find_element_by_name('ps_password').send_keys(kpop_pw)
        driver.find_element_by_xpath('//*[@id="login"]/div[1]/button/b').click()

        # 팝업창 닫기
        da = Alert(driver)
        da.accept()
        self.progressBar.setValue(2)
        # LTE_SITE download
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[1]/a').click()
        driver.switch_to.window(driver.window_handles[1])
        driver.find_element_by_xpath('//*[@id="btn1"]').click()
        driver.switch_to.window(driver.window_handles[0])

        # LTE_PARA_SITE download
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[2]/a').click()

        # 5G_SITE download
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[5]/a').click()
        driver.switch_to.window(driver.window_handles[2])
        driver.find_element_by_xpath('//*[@id="btn1"]').click()
        driver.switch_to.window(driver.window_handles[0])

        # ELG_SITE download
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[9]/a').click()

        # ELG_PARA_SITEdownload
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[10]/a').click()

        # 5G_OFFLOADING download
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/a').click()
        driver.find_element_by_xpath('//*[@id="root"]/nav/div/ul[2]/li/ul/li[15]/a').click()
        driver.switch_to.window(driver.window_handles[3])
        driver.find_element_by_xpath('//*[@id="datepicker"]').send_keys(input_date)
        driver.find_element_by_xpath('//*[@id="datepicker2"]').send_keys(input_date)
        driver.find_element_by_xpath('//*[@id="container"]/span/form/input[4]').click()
        driver.switch_to.window(driver.window_handles[0])
        self.progressBar.setValue(3)

        # 해당 파일 다운로드 까지 기다린 후 실행 (LTE_STIE_INFO)
        self.textBrowser.append('파일 다운 대기 중')
        print('파일 다운 대기')
        file = 'C:/Users/' + username + '/Downloads/LTE_NEW_SITE_INFO_' + today + '.xls'
        while True:
            if os.path.isfile(file):
                print("다운로드 완료")
                self.textBrowser.append('다운로드 완료')
                self.progressBar.setValue(4)
                # chromedriver 및 창 종료
                driver.quit()
                #print('창 종료')

                # 다운로드 폴더의 상위 파일 리스트 가져오기 (날짜 순 정렬)
                def sorted_ls(path):
                    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
                    return list(sorted(os.listdir(path), key=mtime))

                sorted_list = sorted_ls(path)
                file_list = sorted_list[-6:]

                # 가져온 파일 리스트 xls, csv 파일을 xlsb 형태로 변환 (문서 폴더 저장)
                for i in range(len(file_list)):
                    excel = win32.gencache.EnsureDispatch('Excel.Application')
                    
                    file_name = file_list[i]

                    print(file_name + ' 변환 중...')
                    self.textBrowser.append(file_name + ' 변환 중...')

                    if file_name[-1] == 'v':
                        wb = excel.Workbooks.Open(path + file_name)
                        file_name_forCsv = file_name[:-3] + 'xlsb'
                        wb.SaveAs(file_name_forCsv, FileFormat=50)
                    else:
                        wb = excel.Workbooks.Open(path + file_name)
                        wb.SaveAs(file_name + 'b', FileFormat=50)
                # excel 종료
                self.progressBar.setValue(5)
                print('파일 변환 완료 : 문서 폴더를 확인하세요.')
                self.textBrowser.append('파일 변환 완료 : 문서 폴더를 확인하세요.')
                wb.Close()
                excel.Application.Quit()
                break
            else:
                time.sleep(30)
        #sys.exit(0)
        #os.exit()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv) 
        myWindow = WindowClass() 
        myWindow.show() 
        app.exec_()

    # 오류확인
    except Exception as e:
        print("예외 상황 발생 : ", e)
        sys.exit()
    