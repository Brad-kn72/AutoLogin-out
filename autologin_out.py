import sys
import json
import logging
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTextEdit, QHBoxLayout
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# 로그인 정보 저장 파일
CREDENTIAL_FILE = 'credentials.json'

# 로깅 설정
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(message)s')

def load_credentials():
    if os.path.exists(CREDENTIAL_FILE):
        with open(CREDENTIAL_FILE, 'r') as f:
            return json.load(f)
    return {'id': '', 'pw': ''}

def save_credentials(data):
    with open(CREDENTIAL_FILE, 'w') as f:
        json.dump(data, f)

class AutoWorker(QWidget):
    def __init__(self):
        super().__init__()
        self.driver = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Monthly Kitchen 자동 출퇴근')
        layout = QVBoxLayout()

        creds = load_credentials()
        self.id_input = QLineEdit(creds['id'])
        self.pw_input = QLineEdit(creds['pw'])
        self.pw_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel('ID'))
        layout.addWidget(self.id_input)
        layout.addWidget(QLabel('PW'))
        layout.addWidget(self.pw_input)

        save_btn = QPushButton('로그인 정보 저장')
        save_btn.clicked.connect(self.save_credentials)
        layout.addWidget(save_btn)

        login_status = QPushButton('저장된 로그인 정보 보기')
        login_status.clicked.connect(self.show_credentials)
        layout.addWidget(login_status)

        self.work_btn = QPushButton('출근 자동 클릭')
        self.work_btn.clicked.connect(lambda: self.run_automation('출근하기'))
        layout.addWidget(self.work_btn)

        self.leave_btn = QPushButton('퇴근 자동 클릭')
        self.leave_btn.clicked.connect(lambda: self.run_automation('퇴근하기'))
        layout.addWidget(self.leave_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel('로그 출력'))
        layout.addWidget(self.log_output)

        retry_btn = QPushButton('문제 발생 시 초기화 후 재시도')
        retry_btn.clicked.connect(self.reset_and_retry)
        layout.addWidget(retry_btn)

        self.setLayout(layout)

    def log(self, msg):
        logging.info(msg)
        self.log_output.append(msg)

    def show_error(self, msg):
        self.log(f"오류 발생: {msg}")
        QMessageBox.critical(self, '오류', msg)

    def save_credentials(self):
        data = {'id': self.id_input.text(), 'pw': self.pw_input.text()}
        save_credentials(data)
        QMessageBox.information(self, '저장됨', '로그인 정보가 저장되었습니다.')

    def show_credentials(self):
        creds = load_credentials()
        QMessageBox.information(self, '저장된 정보', f"ID: {creds['id']}\nPW: {creds['pw']}")

    def init_driver(self):
        try:
            options = Options()
            options.add_argument('--headless')
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
        except WebDriverException as e:
            self.show_error(f"ChromeDriver 오류: {str(e)}")

    def run_automation(self, action):
        self.init_driver()
        if not self.driver:
            return

        try:
            creds = load_credentials()
            self.driver.get('https://monthlykitchen.dooray.com/work-schedule/user/register-month')

            if '로그인' in self.driver.page_source:
                self.driver.find_element(By.NAME, 'username').send_keys(creds['id'])
                self.driver.find_element(By.NAME, 'password').send_keys(creds['pw'])
                self.driver.find_element(By.TAG_NAME, 'button').click()

            if action == '출근하기':
                el = self.driver.find_element(By.XPATH, "//span[text()='출근하기']/parent::button")
                if el.is_enabled():
                    el.click()
                    self.log('출근 버튼 클릭 완료')
                else:
                    self.log('출근 버튼이 비활성화 상태입니다')

            elif action == '퇴근하기':
                el = self.driver.find_element(By.XPATH, "//span[text()='퇴근하기']/parent::button")
                if el.is_enabled():
                    el.click()
                    self.log('퇴근 버튼 클릭 완료')
                else:
                    self.log('퇴근 버튼이 비활성화 상태입니다')

        except NoSuchElementException as e:
            self.show_error(f"요소를 찾을 수 없음: {str(e)}")
        except Exception as e:
            self.show_error(f"자동화 오류: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

    def reset_and_retry(self):
        self.log('초기화 후 재시도 시작')
        if self.driver:
            self.driver.quit()
        self.run_automation('출근하기')  # 기본은 출근으로 시도

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AutoWorker()
    window.resize(500, 600)
    window.show()
    sys.exit(app.exec_())
