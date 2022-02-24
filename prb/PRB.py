import os
import getpass
import pandas as pd
import sys
import pymysql
from PyQt5.QtWidgets import *
from PyQt5 import uic

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('prb.ui')
form_main = uic.loadUiType(form)[0]
username = getpass.getuser()
down_path = 'C:/Users/' + username + '/Downloads/'

class WindowClass(QMainWindow, form_main):
    #초기화 메서드 
    def __init__(self): 
        super().__init__() 
        self.setupUi(self) 
        self.lineEdit.setText("ex.20220101")

        #pushButton (시작버튼)을 클릭하면 아래 fuctionStart 메서드와 연결 됨. 
        self.pushButton.clicked.connect(self.button_event)
        self.pushButton.clicked.connect(self.cal_prb)
        
    def button_event(self): 
        self.start_date = self.lineEdit.text()
        self.end_date = self.lineEdit_2.text()
        self.lineEdit.setText(self.start_date)
        self.lineEdit_2.setText(self.end_date)

    # DB 연결 및 쿼리
    def connect_db(self, host, db):
        conn = None
        cur = None

        sql = ""

        conn = pymysql.connect(host=host, user='root', password='Rkdqnrlte1q', db=db, charset='utf8')
        cur = conn.cursor()

        # SITE INFO
        sql = "SELECT * FROM site_info_ru30"
        result = pd.read_sql_query(sql,conn)
        info = pd.DataFrame(result)

        conn = None
        cur = None

        sql = ""

        # KPI_Daily
        conn = pymysql.connect(host='172.21.27.208', user='root', password='Rkdqnrlte1q', db='Samsung_LTE', charset='utf8')
        cur = conn.cursor()
        start_date = self.start_date
        end_date = self.end_date
        new_kpi = pd.DataFrame()

        for date in pd.date_range(start_date, end_date):
            input_date = date.strftime('%Y%m%d')
            print(input_date)
            self.textBrowser.append("데이터 가져오는 중 ... kpi_" + input_date)
            print("데이터 가져오는 중 ... kpi_" + input_date)

            sql = """SELECT c.sday,c.h,c.lsm, c.enb, c.cell, c.prbreal, c.rrc_total
            FROM (
            SELECT a.sday,left(a.stime,2) AS h,a.lsm,a.enb,a.cell, IFNULL(SUM(a.prb_dl_total)/ SUM(a.prb_dl_cnt),0) AS prbreal, SUM(a.rrc_attempt) AS rrc_total
            FROM Samsung_LTE.kpi_""" + input_date + """ AS a
            WHERE a.stime >= '0900' AND a.stime < '2400'
            GROUP BY a.lsm,a.enb,a.cell,h
            ) AS c"""
            result = pd.read_sql_query(sql,conn)
            kpi = pd.DataFrame(result)
            
            new_kpi = pd.concat([new_kpi, kpi])

        return info, new_kpi

    def cal_prb(self):
        info, kpi = self.connect_db('172.21.27.208', 'Samsung_LTE')
        join_df = pd.merge(info, kpi, left_on = ['eNB_Name', 'Cell'], right_on=['enb', 'cell'], how='inner')
        join_df['enb_PCI'] = join_df['enb'] + "_" + join_df['PCI']

        ru_df = info
        ru_df['enb_PCI'] = ru_df['eNB_Name'] + '_' + ru_df['PCI']
        ru_df = ru_df[ru_df['BW']=='900M']
        ru_df = ru_df.groupby('enb_PCI').count().reset_index()
        ru_df['ru'] = ru_df['lsms']
        ru_count_df = ru_df[['enb_PCI', 'ru']]

        prepro_df = join_df.pivot_table(['prbreal'], index=['sday', 'h', 'enb_PCI','BW'])
        prepro_df = prepro_df.reset_index()

        prepro_df_900m = prepro_df[prepro_df['BW']=='900M']
        prepro_df_900m = prepro_df_900m[prepro_df_900m['prbreal'] > 70]
        grouped = prepro_df_900m.groupby(['enb_PCI', 'BW']).count().reset_index()
        grouped2 = prepro_df.groupby(['enb_PCI', 'BW']).max().reset_index()
        rrc_sum = pd.pivot_table(join_df, index=['h', 'enb_PCI', 'BW'],values='rrc_total').reset_index()
        grouped3 = rrc_sum.groupby(['enb_PCI', 'BW']).sum().reset_index()
        grouped['count'] = grouped['prbreal']
        grouped2['max_prb'] =  grouped2['prbreal']
        prb_df = grouped2[['enb_PCI', 'BW', 'max_prb']]
        count_df  = grouped[['enb_PCI', 'BW', 'count']]
        rrc_df = grouped3[['enb_PCI', 'BW', 'rrc_total']]

        prepro = pd.pivot_table(prb_df, index=['enb_PCI'], columns='BW', values='max_prb').reset_index()
        rrc_prepro = pd.pivot_table(rrc_df, index=['enb_PCI'], columns='BW', values='rrc_total').reset_index()
        prepro.dropna(subset=['900M'], inplace=True)
        prepro.fillna(0, inplace=True)
        rrc_prepro.fillna(0, inplace=True)

        tmp = prepro[['enb_PCI', '900M', '1.8G', '1.8H', '1.8E', '2.1G', '2.1E']]
        count_df = count_df[count_df['BW']=='900M']

        prepro_count = pd.merge(tmp, count_df[['enb_PCI', 'count']], left_on='enb_PCI', right_on='enb_PCI', how='inner')
        result_count = pd.merge(prepro_count, rrc_prepro, left_on='enb_PCI', right_on='enb_PCI', how='inner')
        result_sum = result_count['900M_y'] + result_count['1.8G_y'] + result_count['1.8E_y'] + result_count['1.8H_y'] +  result_count['2.1G_y'] + result_count['2.1E_y']

        col_num = 0
        for column_name in result_count:
            if 'x' in column_name:
                new_col_name = column_name[:-2] + '_max_prb'
                result_count[new_col_name] = round(result_count[column_name], 1)
                result_count.drop(column_name, axis=1, inplace=True)

            if 'y' in column_name:
                new_col_name = column_name[:-2] + '_rrc_rate'
                print(result_count[column_name].value_counts())

                result_count[new_col_name] = round((result_count[column_name] / (result_sum)) * 100)
                result_count.fillna(0, inplace=True)
                result_count[new_col_name] = result_count[new_col_name].astype(int)
                result_count[new_col_name] = result_count[new_col_name].astype(str) + '%'
                result_count.drop(column_name, axis=1, inplace=True)
            col_num += 1

        tmp_list = result_count[['900M_max_prb', '1.8G_max_prb', '1.8H_max_prb', '1.8E_max_prb', '2.1E_max_prb', '2.1G_max_prb']]
        count_list = []
        for i, v  in tmp_list.iterrows():
            count = 0
            for a in v:
                if a != 0:
                    count += 1
            count_list.append(count)
        result_count['fa'] = count_list

        prepro_df2 = join_df.pivot_table(['prbreal'], index=['enb','PCI','BW', 'lsm', 'RS_POWER', 'type_MCMC'])
        prepro_df2 = prepro_df2.reset_index()
        prepro_df2['enb_PCI'] = prepro_df2['enb'] + "_" + prepro_df2['PCI']
        prepro_df_900m = prepro_df2[prepro_df2['BW']=='900M']

        results = pd.merge(result_count, prepro_df_900m[['enb_PCI', 'lsm', 'RS_POWER', 'type_MCMC']], left_on='enb_PCI', right_on='enb_PCI', how='inner')
        real_result =  pd.merge(results, ru_count_df, left_on='enb_PCI', right_on='enb_PCI', how='inner')
        real_result
        real_result = real_result[['lsm', 'enb_PCI', '900M_max_prb', '1.8G_max_prb', '1.8H_max_prb', '1.8E_max_prb', '2.1E_max_prb', '2.1G_max_prb', 'fa',
            '900M_rrc_rate', '1.8G_rrc_rate', '1.8H_rrc_rate', '1.8E_rrc_rate', '2.1E_rrc_rate', '2.1G_rrc_rate', 'type_MCMC', 'ru', 'RS_POWER', 'count']]

        path = down_path + 'prb_' + self.start_date + '_' + self.end_date + '.csv'
        real_result.to_csv(path, header=True, index=False)
        self.textBrowser.append(path + "를 확인하세요.")
        print(path + "를 확인하세요.")

        return real_result

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv) 
        myWindow = WindowClass() 
        myWindow.show() 
        app.exec_()
        sys.exit()

    # 오류확인
    except Exception as e:
        print("예외 상황 발생 : ", e)
        myWindow.textBrowser.append(e)
        #sys.exit()