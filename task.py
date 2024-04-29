import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Importamos ttk para usar el widget Progressbar, esto no jalo
import threading
import queue
import time

class AddProcessDialog(tk.Toplevel):
    def __init__(self, parent, process_manager):
        super().__init__(parent)
        self.title("Add Process")
        self.process_manager = process_manager
        
        self.priority_label = tk.Label(self, text="Priority (1 for high, 2 for medium, 3 for low):")
        self.priority_label.pack()

        self.priority_entry = tk.Entry(self)
        self.priority_entry.pack()

        self.add_button = tk.Button(self, text="Add", command=self.add_process)
        self.add_button.pack()

    def add_process(self):
        priority = self.priority_entry.get()
        try:
            priority = int(priority)
            if priority < 1 or priority > 3:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid priority. Please enter a number between 1 and 3.")
            return
        
        self.process_manager.add_process(priority)
        self.destroy()

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        
        self.processes = queue.Queue()
        self.semaphore = threading.Semaphore(1)
        self.process_count = 1  # Contador para el orden de llegada de los procesos
        self.stop_simulation_flag = False  # Bandera para detener la simulación

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.process_frame = tk.Frame(self.main_frame, width=800, borderwidth=1, relief=tk.RIDGE)
        self.process_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.process_list_label = tk.Label(self.process_frame, text="Processes")
        self.process_list_label.pack()

        self.process_list = tk.Listbox(self.process_frame, width=50, height=20)
        self.process_list.pack(fill=tk.BOTH, expand=True)

        self.progress_bars = {}  # Diccionario para mantener las barras de progreso por proceso

        self.add_button = tk.Button(self.main_frame, text="Add Process", command=self.open_add_process_dialog)
        self.add_button.pack()

        self.remove_button = tk.Button(self.main_frame, text="Remove Process", command=self.remove_process)
        self.remove_button.pack()

        self.mode_frame = tk.Frame(self.main_frame)
        self.mode_frame.pack()

        self.mode_label = tk.Label(self.mode_frame, text="Mode:")
        self.mode_label.pack(side=tk.LEFT)

        self.mode_var = tk.StringVar()
        self.mode_var.set("FIFO")
        self.mode_menu = tk.OptionMenu(self.mode_frame, self.mode_var, "FIFO", "LIFO")
        self.mode_menu.pack(side=tk.LEFT)

        self.start_simulation_button = tk.Button(self.main_frame, text="Start Simulation", command=self.start_simulation)
        self.start_simulation_button.pack()

        self.stop_simulation_button = tk.Button(self.main_frame, text="Stop Simulation", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_simulation_button.pack()

        self.simulation_timer = None
        self.simulation_interval = 1  # Interval in seconds for simulation

    def open_add_process_dialog(self):
        dialog = AddProcessDialog(self.root, self)
        dialog.grab_set()

    def add_process(self, priority):
        process = {"priority": priority, "progress": 0, "arrival_order": self.process_count}
        self.process_count += 1  # Incrementar el contador de orden de llegada
        self.semaphore.acquire()
        if self.mode_var.get() == "FIFO":
            self.processes.put(process)
        elif self.mode_var.get() == "LIFO":
            temp_queue = queue.Queue()
            while not self.processes.empty():
                temp_queue.put(self.processes.get())
            self.processes.put(process)
            while not temp_queue.empty():
                self.processes.put(temp_queue.get())
        self.semaphore.release()
        self.update_list()
        self.update_progress_bars()  # Actualizar las barras de progreso

    def remove_process(self):
        if not self.processes.empty():
            self.semaphore.acquire()
            self.processes.get()
            self.semaphore.release()
            self.update_list()
            self.update_progress_bars()  # Actualizar las barras de progreso

    def update_list(self):
        self.process_list.delete(0, tk.END)
        items = list(self.processes.queue)
        items.sort(key=lambda x: (x["priority"], x["arrival_order"]), reverse=self.mode_var.get() == "FIFO")
        for process in items:
            self.process_list.insert(tk.END, f"Priority: {process['priority']}, Order: {process['arrival_order']}, Progress: {process['progress']}%")

    def update_progress_bars(self):
        for process_id, process in self.progress_bars.items():
            process["bar"].configure(value=process["progress"])

    def simulate_processes(self):
        while not self.processes.empty() and not self.stop_simulation_flag:
            process = self.processes.get()
            if process["progress"] < 100:
                process["progress"] += 10
                self.processes.put(process)
                self.update_list()
                self.update_progress_bars()  # Actualizar las barras de progreso
                time.sleep(self.simulation_interval)

    def start_simulation(self):
        self.start_simulation_button.config(state=tk.DISABLED)
        self.stop_simulation_button.config(state=tk.NORMAL)
        self.stop_simulation_flag = False  # Resetear la bandera
        self.simulation_timer = threading.Thread(target=self.simulate_processes)
        self.simulation_timer.start()

    def stop_simulation(self):
        if self.simulation_timer:
            self.stop_simulation_flag = True  # Establecer la bandera para detener la simulación
            self.simulation_timer.join()
        self.start_simulation_button.config(state=tk.NORMAL)
        self.stop_simulation_button.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
