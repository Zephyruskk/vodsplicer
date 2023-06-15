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
        self.button_analyzer.grid(row=0, column=0, pady=(15, 0), sticky="nsew")
        
        self.button_splicer = tk.Button(self, text="Select Input for Splicer", command=self.select_input_splicer)
        self.button_splicer.grid(row=1, column=0, pady=(15, 0), sticky="nsew")
        
        self.upload_var = tk.BooleanVar()
        self.checkbox_upload = tk.Checkbutton(self, text="Upload to YouTube", variable=self.upload_var)
        self.checkbox_upload.grid(row=1, column=1, pady=(15, 0))
        
        label_output = tk.Label(self, text="Standard Output:")
        label_output.grid(row=2, column=0, pady=(20, 0), columnspan=2)
        
        self.output_text = tk.Text(self, height=7, width=50, bg="black", fg="white", font=("Courier", 10))
        self.output_text.grid(row=3, column=0, columnspan=2)

        self.grid_rowconfigure(3, weight=1)  # Allow the output_text widget to expand vertically

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
        self.update_output_text(f"Analyzing {file_path}\nPlease be patient as this may take a while...\n")
        command = ["python", "analyzer.py", file_path]
        process = Popen(command, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        threading.Thread(target=self.read_output, args=(process,), daemon=True).start()

    def run_splicer(self, file_name):
        command = ["python", "splicer.py", file_name]
        if self.upload_var.get():
            command.append("--upload")
        process = Popen(command, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        threading.Thread(target=self.read_output, args=(process,), daemon=True).start()


if __name__ == "__main__":
    app = Application()
    sys.stdout = app.output_text
    app.mainloop()
