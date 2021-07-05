#!/usr/bin/env python3

import glob
import rrdtool
import pandas as pd
import sqlite3
import time
from datetime import datetime
import os
import threading
import multiprocessing
import random

munin_data_dir = '/var/lib/munin'
sqlite_data_dir = 'sqlite-data'

def get_df_from_rrd(rrd_file):
    df = pd.DataFrame(data = [], columns=['time', 'value'])
    i = 0
    #for step in [ 300, 1800, 7200, 86400 ]:
    for step in [ 300 ]:
        #rrd_fetch = rrdtool.fetch(rrd_file, "AVERAGE", "-r", str(int(step/300)), "-s", str(int(time.time()) - step*400))
        rrd_fetch = rrdtool.fetch(rrd_file, "AVERAGE")
        start = rrd_fetch[0][0]
        end   = rrd_fetch[0][1]
        real_step = rrd_fetch[0][2]
        #print(f'{start = }')
        #print(f'{end = }')
        #print(f'{step = }         {real_step = }')
        #pprint.pprint(rrdtool.dump(rrd_file))

        m_time = start
        for value in rrd_fetch[2]:
            m_time += real_step
            df.loc[i] = [ datetime.utcfromtimestamp(m_time), value[0]]
            #print(df.loc[i])
            i += 1
    return df


def df2sqlite(df, sqlite_file):
    os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
    table_name = 'data'
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute(f'DROP TABLE if exists {table_name}')
    df.to_sql(table_name, conn)
    conn.close()

def convert_rrds(rrd_file_list):

    rrd_file_list_len = len(rrd_file_list)
    i = 0
    s = 0
    for rrd in rrd_file_list:
        i += 1
        sqlite_file = sqlite_data_dir + rrd[:-3].replace(munin_data_dir, '') + 'sqlite'
        if not os.path.isfile(sqlite_file) or os.path.getmtime(sqlite_file) < os.path.getmtime(rrd):
            print(f'{i}/{rrd_file_list_len}  {rrd}    ', end='')
            df2sqlite(get_df_from_rrd(rrd), sqlite_file)
            print('OK')
        else:
            print('.', end='')
            s += 1

    print(f'Skipped: {s}')



def convert_all_rrds_mp():
    rrd_file_list = glob.glob(f'{munin_data_dir}/**/*.rrd', recursive=True)
    random.shuffle(rrd_file_list)

    i = 0
    s = 0
    max_thread_n = multiprocessing.cpu_count()

    last_item = 0
    for thread_n in range(max_thread_n):
        print(f'{thread_n = }')
        rrd_file_list_len = len(rrd_file_list)
        first_item = last_item
        last_item = ( thread_n + 1 ) * int(rrd_file_list_len / max_thread_n)
        if last_item != 0:
            mp = multiprocessing.Process(target = convert_rrds,
                                        args = (rrd_file_list[first_item:last_item],)
            )
            mp.start()

if __name__ == "__main__":
    convert_all_rrds_mp()