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

def build_apps(config):
    if config['compile'] == True:
        capture_output = not config['show_outputs']
        for dir in ['memory', 'threading']:
            subprocess.run([
                'g++',
                f'./c++/{dir}/main.cpp',
                '-o', f'./c++/{dir}/main',
                '-O3'
            ], capture_output=capture_output)

            subprocess.run([
                'zig', 'build-exe', '-lc', 
                './main.zig',
                '-O', 'ReleaseFast'
            ], capture_output=capture_output, cwd=f'./zig/{dir}/')

            subprocess.run([
                'cargo', 
                'build',
                '--release'
            ], capture_output=capture_output, cwd=f'rust/{dir}/')

def memory_tests(config):
    min = config['min']
    max = config['max']
    length = config['array_size']
    testcase_dest = config['testcase_dest']
    random_array = [random.randint(min, max) for _ in range (length)]
    capture_output = not config['show_outputs']

    
    with open(testcase_dest, "w") as testcase_file:
        testcase_file.write(
            str(random_array)
                .replace('[', '')
                .replace(']', '')
                .replace(', ', ' ')
        )

    subprocess.run([
        './c++/memory/main',
        testcase_dest,
        'data.csv',
        str(length)
    ], capture_output=capture_output)

    for allocator in ['c_allocator', 'general_purpose_allocator', 'page_allocator']:
        subprocess.run([
            './zig/memory/main',
            testcase_dest,
            'data.csv',
            str(length),
            allocator
        ], capture_output=capture_output)

    subprocess.run([
        './rust/memory/target/release/main',
        testcase_dest,
        'data.csv',
        str(length)
    ], capture_output=capture_output)

def threading_tests(config):
    runs = str(config["thread_launches"])
    capture_output = not config['show_outputs']
    subprocess.run([
        './c++/threading/main',
        runs,
        'data.csv',
    ], capture_output=capture_output)

    subprocess.run([
        './zig/threading/main',
        runs,
        'data.csv',
    ], capture_output=capture_output)

    subprocess.run([
        './rust/threading/target/release/main',
        runs,
        'data.csv',
    ], capture_output=capture_output)

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
        plt.ylabel('Duration (ns)')
        
        if config['save']:
            plt.savefig(f'charts/{timestamp}/{test_name}_chart.png')
        
        if config['show']:
            plt.show()

def main(config):
    global timestamp
    timestamp = int(time.time())
    build_apps(config['compilation'])
    
    if config['benchmark']['clean']:
        clean_data()
    memory_tests(config['memory'])
    threading_tests(config['threading'])
    parse_data(config['charts'])

if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    main(config)
