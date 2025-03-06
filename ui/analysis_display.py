import tkinter as tk
from tkinter import ttk

class AnalysisDisplay:
    
    def __init__(self, parent):
        self.parent = parent
        
        self.move_frame = tk.LabelFrame(parent, text="Best Move", font=("Arial", 12, "bold"), padx=5, pady=5)
        self.move_frame.pack(fill=tk.X, pady=5)
        
        self.move_label = tk.Label(self.move_frame, text="Calculating...", font=("Arial", 16, "bold"), fg="#009900")
        self.move_label.pack(pady=5)
        
        self.eval_label = tk.Label(self.move_frame, text="", font=("Arial", 10))
        self.eval_label.pack(pady=2)
        
        self.tab_control = ttk.Notebook(parent)
        
        self.basic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.basic_tab, text="Basic Analysis")
        
        self.detailed_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.detailed_tab, text="Detailed Analysis")
        
        self.tab_control.pack(expand=1, fill=tk.BOTH, pady=10)
        
        self.explanation_text = tk.Text(self.basic_tab, height=16, width=50, font=("Arial", 10), wrap=tk.WORD)
        self.explanation_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        explanation_scrollbar = tk.Scrollbar(self.basic_tab, command=self.explanation_text.yview)
        explanation_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.explanation_text.config(yscrollcommand=explanation_scrollbar.set)
        
        self.detailed_text = tk.Text(self.detailed_tab, height=16, width=50, font=("Arial", 10), wrap=tk.WORD)
        self.detailed_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        detailed_scrollbar = tk.Scrollbar(self.detailed_tab, command=self.detailed_text.yview)
        detailed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detailed_text.config(yscrollcommand=detailed_scrollbar.set)
    
    def set_move(self, move_text, color="#009900"):
        self.move_label.config(text=move_text, fg=color)
    
    def set_evaluation(self, eval_text):
        self.eval_label.config(text=eval_text)
    
    def set_basic_analysis(self, text):
        self.explanation_text.delete(1.0, tk.END)
        if text: 
            self.explanation_text.insert(tk.END, text)
    
    def set_detailed_analysis(self, text):
        self.detailed_text.delete(1.0, tk.END)
        if text: 
            self.detailed_text.insert(tk.END, text)
    
    def clear_analysis(self):
        self.move_label.config(text="No move found")
        self.eval_label.config(text="")
        self.explanation_text.delete(1.0, tk.END)
        self.detailed_text.delete(1.0, tk.END)