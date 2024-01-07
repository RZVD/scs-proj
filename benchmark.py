#!/bin/python3
import tkinter as tk
from tkinter import filedialog 
import random
from matplotlib import subprocess, shutil
import os
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
import yaml
import argparse

class AppGUI:
    __default_config = {
        'memory': {
            'array_size': 100000,
            'min': 0,
            'max': 123546243,
            'testcase_dest': './mem_testcase',
            'show_outputs': True
        },
        'threading': {
            'thread_launches': 100000,
            'pipe_reads': 100000,
            'migration_runs': 100000,
            'show_outputs': False
        },
        'benchmark': {
            'clean': True,
        },
        'compilation': {
            'compile': False,
            'show_outputs': False
        },
        'charts': {
            'save': True,
            'show': True,
            'figsize': [15, 6]
        }
    }

    def __init__(self, root: tk.Tk, config: dict | None):
        self.root = root
        self.root.title("Benchmarking Configuration")
        self.__config = config if config is not None else self.__default_config
        self.__create_widgets()

    def __create_widgets(self):
        self.entry_widgets = {}

        tk.Button(self.root, text="Select Config File", command=self.__load_config).pack(pady=10)
        tk.Button(self.root, text="Run Tests", command=self.run_tests).pack(pady=10)

        for key, value in self.__config.items():
            tk.Label(self.root, text=f"{key.capitalize()} Configuration").pack(pady=5, anchor="w")
            for option, default_value in value.items():
                frame = tk.Frame(self.root)
                frame.pack(pady=2, padx=10, anchor="w")
                tk.Label(frame, text=f"{option.capitalize()}:", width=15, anchor="w").pack(side="left")

                if isinstance(default_value, bool):
                    entry_var = tk.BooleanVar(value=default_value)
                    entry_widget = tk.Checkbutton(frame, variable=entry_var)
                elif option == 'figsize':
                    entry_var = tk.StringVar(value=', '.join(map(str, default_value)))
                    entry_widget = tk.Entry(frame, textvariable=entry_var)
                else:
                    entry_var = tk.StringVar(value=str(default_value))
                    entry_widget = tk.Entry(frame, textvariable=entry_var)

                entry_widget.pack(side="left")

                self.entry_widgets[(key, option)] = entry_var

    def __load_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*"), ("JSON Files", "*.json"), ("YAML Files", "*.yaml")])
        if file_path:
            with open(file_path, 'r') as config_file:
                self.__config.update |= yaml.safe_load(config_file)

            print(f"Config loaded from {file_path}")
            self.__update_gui_from_config()

    def __update_gui_from_config(self):
        for (key, option), entry_var in self.entry_widgets.items():
            config_value = self.__config.get(key, {}).get(option)
            if isinstance(config_value, bool):
                entry_var.set(config_value)
            else:
                entry_var.set(str(config_value))

    def __update_config_from_gui(self):
        for (key, option), entry_var in self.entry_widgets.items():
            widget_value = entry_var.get()
            try:
                if option == 'figsize':
                    widget_value = [int(x.strip()) for x in widget_value.split(',')]
                else:
                    widget_value = int(widget_value)
            except ValueError:
                pass

            self.__config[key][option] = widget_value

    def run_tests(self):
        self.__update_config_from_gui()
        benchmark(self.__config)


def clean_data():
    with open('data.csv', 'w') as datafile:
        datafile.write("TestName,Language,Size,Duration\n")

def build_apps(config):
    if config['compile']:
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
                './main.zig', '/lib/x86_64-linux-gnu/libpthread.so.0', # Zig compiler bug
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

    allocators = ['c_allocator', 'general_purpose_allocator', 'page_allocator', 'arena_allocator']
    for allocator in allocators:
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
    creation_runs  = str(config["thread_launches"])
    pipe_reads     = str(config['pipe_reads'])
    migration_runs = str(config['migration_runs'])

    capture_output = not config['show_outputs']
    subprocess.run([
        './c++/threading/main',
        creation_runs,
        pipe_reads,
        migration_runs,
        'data.csv',
    ], capture_output=capture_output)

    subprocess.run([
        './zig/threading/main',
        creation_runs,
        pipe_reads,
        migration_runs,
        'data.csv',
    ], capture_output=capture_output)

    subprocess.run([
        './rust/threading/target/release/main',
        creation_runs,
        pipe_reads,
        migration_runs,
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
            shutil.copyfile('data.csv', f'charts/{timestamp}/data.csv')
        
        if config['show']:
            plt.show()

def benchmark(config):
    global timestamp
    timestamp = int(time.time())
    build_apps(config['compilation'])
    
    if config['benchmark']['clean']:
        clean_data()

    memory_tests(config['memory'])
    threading_tests(config['threading'])

    parse_data(config['charts'])

def main(args):
    if args.json:
        print(args.json)
        config = json.loads(args.json)
    else:
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)

        override_options = {
            'memory': ['array_size', 'min', 'max', 'testcase_dest', 'show_outputs'],
            'threading': ['thread_launches', 'pipe_reads', 'migration_runs', 'show_outputs'],
            'benchmark': ['clean', 'show_outputs'],
            'compilation': ['compile' ,'show_outputs'],
            'charts': ['save', 'show', 'figsize']
        }

        for section, options in override_options.items():
            for option in options:
                cli_option = f'{section}_{option.replace("-", "_")}'
                if getattr(args, cli_option) is not None:
                    config[section][option] = getattr(args, cli_option)

    if args.gui:
        gui = AppGUI(
            tk.Tk(), 
            config
        )
        gui.root.mainloop()
    else:
        benchmark(config)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Benchmarking Tool")

    parser.add_argument('--json', type=str, help='JSON string representing the config')
    parser.add_argument('--gui', action='store_true', help='Launch with GUI')

    parser.add_argument('--memory-array-size', type=int, help='Array size for memory tests')
    parser.add_argument('--memory-min', type=int, help='Lower bound for elements generated for memory test')
    parser.add_argument('--memory-max', type=int, help='Upper bound for elements generated for memory test')
    parser.add_argument('--memory-testcase-dest', type=str, help='Destination for memory testcases')
    parser.add_argument('--memory-show-outputs', type=bool, help='Show outputs for memory tests')

    parser.add_argument('--threading-thread-launches', type=int, help='Number of thread launches for threading tests')
    parser.add_argument('--threading-pipe-reads', type=int, help='Number of pipe reads for threading tests')
    parser.add_argument('--threading-migration-runs', type=int, help='Number of pipe reads for threading tests')
    parser.add_argument('--threading-show-outputs', type=bool, help='Show outputs for threading tests')

    parser.add_argument('--benchmark-clean', type=bool, help='Cleans data.csv')
    parser.add_argument('--benchmark-show-outputs', type=bool, help='Don\'t remember what this was for. Not used in code yeat' )

    parser.add_argument('--compile', action='store_true', dest='compilation_compile', help='Recompiles the apps before benchmarking')
    parser.add_argument('--compilation-show-outputs', action='store_true', help='Show outputs for compilation')

    parser.add_argument('--charts-save', type=bool, help='Save charts as images under charts/{timestamp}')
    parser.add_argument('--charts-show', type=bool, help='Shows charts')
    parser.add_argument('--charts-figsize', type=int, nargs='+', help='')
    args = parser.parse_args()
    main(args)
