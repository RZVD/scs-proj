#!/bin/python3

import random
from matplotlib import subprocess

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
import json
import time


def clean_data():
    with open('data.csv', 'w') as datafile:
        datafile.write("TestName,Language,Size,Duration\n")

def build_apps():
    subprocess.run([
        'g++',
        './c++/memory/linked_list.cpp',
        '-o', './c++/memory/linked_list',
        '-O3'
    ], capture_output=True)

    subprocess.run([
        'zig', 'build-exe', '-lc'
        './zig/memory/linked_list.zig',
        '-o', './zig/memory/linked_list',
        '-O', 'ReleaseFast'
    ], capture_output=True)

    subprocess.run([
        'cargo', 
        'build',
        '--release'
    ], capture_output=True, cwd='rust/memory/dynamic')

def memory_tests(config):
    min = config['min']
    max = config['max']
    length = config['array_size']
    testcase_dest = config['testcase_dest']
    random_array = [random.randint(min, max) for _ in range (length)]
    
    with open(testcase_dest, "w") as testcase_file:
        testcase_file.write(
            str(random_array)
                .replace('[', '')
                .replace(']', '')
                .replace(', ', ' ')
        )


    subprocess.run([
        './c++/memory/linked_list',
        testcase_dest,
        'data.csv',
        str(length)
    ], capture_output=True)

    subprocess.run([
        './zig/memory/linked_list',
        testcase_dest,
        'data.csv',
        str(length)
    ], capture_output=True)

    subprocess.run([
        './rust/memory/dynamic/target/release/dynamic',
        testcase_dest,
        'data.csv',
        str(length)
    ], capture_output=True)
        

def threading_tests(config):
    pass

def parse_data(config):
    df = pd.read_csv("data.csv")

    grouped = df.groupby('TestName')

    if config['save']:
        os.makedirs(f'charts/{timestamp}/')

    for test_name, group in grouped:
        plt.figure(figsize=config['figsize'])
        plt.bar(group['Language'], group['Duration'])
        plt.title(f'Duration for {test_name}')
        plt.xlabel('Language')
        plt.ylabel('Duration')
        
        if config['save']:
            plt.savefig(f'charts/{timestamp}/{test_name}_chart.png')
        
        if config['show']:
            plt.show()

def main(config):
    global timestamp
    timestamp = int(time.time())
    if config['compile'] == True:
        build_apps()
    
    if config['clean']:
        clean_data()
    memory_tests(config['memory'])
    threading_tests(config['threading'])
    parse_data(config['charts'])

if __name__ == '__main__':
    config = {}
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    main(config)
