import os
import signal
import sys


def launch():
    GuiApp = safe_import_GuiApp(allow_install=True)
    if GuiApp is None:
        return 1
    signal.signal(signal.SIGINT, signal.SIG_DFL)    # Allow Ctrl-C to close the program
    return GuiApp().exec()


def safe_import_GuiApp(allow_install=True):
    try:
        from src.EV3DriverStation.app import GuiApp  # noqa: F401
    except ImportError as e:
        print('Missing dependancies for EV3-DriverStation.')
        print(e)
    else:
        return GuiApp

    from tkinter import messagebox
    if allow_install \
        and messagebox.askyesno('EV3-DriverStation dependancies are not installed', 
                                "EV3-DriverStation relies on several python packages.\n" +
                                "Do you want to install them now?"
                            )\
        and install():
        return safe_import_GuiApp(allow_install=False)
    else:
        messagebox.showerror('EV3-DriverStation dependancies are not installed', 
                                "EV3-DriverStation cannot run without its dependancies.\n" +
                                "Please install them manually.")
        return None


def install():
    print('Installing dependancies...')
    import subprocess
    import tkinter as tk
    from queue import Empty, Queue
    from threading import Thread
    
    std_out_queue = Queue()
    def enqueue_output(out):
        for line in iter(out.readline, b''):
            std_out_queue.put(line)
        out.close()

    CWD = os.path.dirname(os.path.realpath(__file__))

    # Setup tkinter window
    win = tk.Tk()
    win.geometry("600x400")
    win.title("Installing EV3-DriverStation dependancies...")

    text = tk.Text(win, bg="black", fg="white", font=("Consolas", 9))
    v = tk.Scrollbar(win, orient='vertical', command=text.yview)
    text.configure(yscrollcommand=v.set)

    cancel_button = tk.Button(win, text="Cancel")
    cancel_button.pack(side=tk.BOTTOM, fill=tk.X)
    v.pack(side=tk.RIGHT, fill='y')
    text.pack()

    # Start pip install
    pip = subprocess.Popen([sys.executable, "-m", "pip", "install", "-e", "."], cwd=CWD, 
                           stdout=subprocess.PIPE)
    # Start thread to read pip output
    t = Thread(target=enqueue_output, args=(pip.stdout,))
    t.daemon = True
    t.start()
    

    # Setup cancel button
    def cancel():
        pip.kill()
        win.destroy()
    cancel_button.config(command=cancel)

    # Setup update function
    def update():
        while True:
            try:
                line = std_out_queue.get_nowait()
            except Empty:
                break
            else:
                text.insert(tk.END, line.decode())
                text.see(tk.END)

        if pip.poll() is not None:
            if pip.returncode == 0:
                text.insert(tk.END, "Done.")
                text.see(tk.END)
                text.after(1000, win.destroy)
            else:
                text.insert(tk.END, "Error: " + str(pip.returncode))
                text.see(tk.END)

                # Change cancel button to close button
                cancel_button.config(text="Close", command=win.destroy)
        else:
            text.after(100, update)
    
    text.after(100, update)

    win.attributes('-topmost',True)
    win.mainloop()

    return pip.returncode  == 0


if __name__ == '__main__':
    sys.exit(launch())
