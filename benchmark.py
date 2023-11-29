#!/bin/python3

import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from matplotlib import subprocess
import os
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
import yaml


class App:
    def __init__(self, root, config):
        self.root = root
        self.root.title("Test Configuration")

        self.config = config

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.root, text="Select Config File", command=self.load_config).pack(pady=10)
        tk.Button(self.root, text="Run Tests", command=self.run_tests).pack(pady=10)

        for section, options in self.config.items():
            tk.Label(self.root, text=f"{section.capitalize()} Configuration").pack(pady=5, anchor="w")
            for option, default_value in options.items():
                frame = tk.Frame(self.root)
                frame.pack(pady=2, padx=10, anchor="w")
                tk.Label(frame, text=f"{option.capitalize()}:", width=15, anchor="w").pack(side="left")
                if isinstance(default_value, bool):
                    var = tk.BooleanVar()
                    var.set(default_value)
                    tk.Checkbutton(frame, variable=var).pack(side="left")
                    self.config[section][option] = var
                elif isinstance(default_value, list):
                    var = tk.StringVar()
                    var.set(str(default_value))
                    tk.Entry(frame, textvariable=var).pack(side="left")
                    self.config[section][option] = var
                else:
                    var = tk.IntVar() if isinstance(default_value, int) else tk.StringVar()
                    var.set(default_value)
                    tk.Entry(frame, textvariable=var).pack(side="left")
                    self.config[section][option] = var

    def load_config(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'r') as config_file:
                self.config = json.load(config_file)
            print(f"Config loaded from {file_path}")

    def run_tests(self):
        # Execute the tests with the loaded or default config
        main(self.config)



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
    root = tk.Tk()
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    app = App(root, config)
    root.mainloop()
