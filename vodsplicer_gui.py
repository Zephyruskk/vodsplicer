import sys
import threading
import tkinter as tk
from tkinter import filedialog
from subprocess import Popen, PIPE, STDOUT


class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("VOD Splicer GUI")
        
        self.button_analyzer = tk.Button(self, text="Select Input for Analyzer", command=self.select_input_analyzer)
        self.button_analyzer.pack(pady=(15,0))
        self.button_splicer = tk.Button(self, text="Select Input for Splicer", command=self.select_input_splicer)
        self.button_splicer.pack(pady=(15,0))
        label_output = tk.Label(self, text="Standard Output:")
        label_output.pack(pady=(20,0))
        self.output_text = tk.Text(self, height=7, width=50, bg="black", fg="white", font=("Courier", 10))        
        self.output_text.pack()

    def select_input_analyzer(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.run_analyzer(file_path)

    def select_input_splicer(self):
        file_path = filedialog.askopenfilename(initialdir="./sheets")
        if file_path:
            self.run_splicer(file_path)

    def update_output_text(self, output):
        self.output_text.configure(state=tk.NORMAL)  # Enable editing the text widget
        self.output_text.insert(tk.END, output)
        self.output_text.configure(state=tk.DISABLED)  # Disable editing the text widget
        self.output_text.see(tk.END)  # Scroll to the end of the text widget


    def read_output(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.update_output_text(output)

    def run_analyzer(self, file_path):
        command = ["python", "analyzer.py", file_path]
        process = Popen(command, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        threading.Thread(target=self.read_output, args=(process,), daemon=True).start()

    def run_splicer(self, file_name):
        command = ["python", "splicer.py", file_name]
        process = Popen(command, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        threading.Thread(target=self.read_output, args=(process,), daemon=True).start()


if __name__ == "__main__":
    app = Application()
    sys.stdout = app.output_text
    app.mainloop()
