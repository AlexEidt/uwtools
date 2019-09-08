
import os
import re
import pandas as pd
from zlib import compress, decompress

path_ = os.path.normpath(f'C:\\Users\\alex\\Documents\\UWTools\\Time_Schedules')
campuses = ['Seattle', 'Bothell', 'Tacoma']

def concat_campuses():
    for campus in campuses:
        campus_df = pd.DataFrame()
        for f in os.listdir(os.path.normpath(f'{path_}/{campus}')):
            f_name = f'{path_}/{campus}/{f}'
            df = pd.read_csv(os.path.normpath(str(f_name)))
            name, _ = os.path.splitext(f)
            c, _, q, y = name.split('_')
            df['Campus'] = c
            df['Quarter'] = q
            df['Year'] = y
            campus_df = pd.concat([campus_df, df], axis=0)
        campus_df.to_csv(os.path.normpath(f'{path_}/Combined_Schedules/{campus}_TimeSchedules.csv'), sep='\t')

    
def compress_df():
    combined_path = os.path.normpath(f'{path_}/Combined_Schedules')
    for f in os.listdir(combined_path):
        for campus in campuses:
            df = os.path.normpath(f'{combined_path}/{campus}_TimeSchedules.csv')
            with open(df, mode='r') as f:
                c = compress(f.read().encode())
                with open(os.path.normpath(f'{combined_path}/{campus}_Compressed'), mode='wb') as compressed:
                    compressed.write(c)
    for campus in campuses:
        os.remove(os.path.normpath(f'{combined_path}/{campus}_TimeSchedules.csv'))

def decode_df():
    for campus in campuses:
        c_path = os.path.normpath(f'{path_}/Combined_Schedules')
        with open(os.path.normpath(f'{c_path}/{campus}_Compressed'), mode='rb')as f:
            with open(os.path.normpath(f'{c_path}/{campus}_TimeSchedules.csv'), mode='w') as new:
                new.write(decompress(f.read()).decode())


#concat_campuses()
#compress_df()
#decode_df()

def compress_file(file_name, compressed):
    with open(os.path.normpath(f'{os.getcwd()}/{file_name}'), mode='r') as f:
        with open(os.path.normpath(f'{os.getcwd()}/{compressed}'), mode='wb') as comp:
            comp.write(compress(f.read().encode()))
    os.remove(os.path.normpath(f'{os.getcwd()}/{file_name}'))

total = {}


#compress_file('Coordinates.json', 'Coordinates')

