import atexit
import json
from tkinter import Tk, BOTH, Canvas


def qr_frame():
    def on_resize(evt):
        global info
        tk.configure(width=evt.width, height=evt.height)
        canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill='gray', outline='gray')
        info = (canvas.winfo_rootx() - 5, canvas.winfo_rooty() - 5,
                canvas.winfo_width() + 10, canvas.winfo_height() + 10)
        tk.title(f'{info}')
        tk.wm_attributes('-topmost', 1)

    tk.geometry('320x320')
    tk.wm_attributes('-transparentcolor', 'gray')
    canvas = Canvas(tk)
    canvas.pack(fill=BOTH, expand=True, padx=10, pady=10)
    tk.bind('<Configure>', on_resize)
    tk.mainloop()


def save():
    with open('region.txt', 'w', encoding='u8') as f:
        json.dump(info, f)


if __name__ == '__main__':
    atexit.register(save)
    info = [0, 0, 0, 0]
    tk = Tk()
    qr_frame()
