import sounddevice as sd
import tkinter as tk
from tkinter import scrolledtext, ttk
import re

def get_default_device():
    devices = sd.query_devices()
    match = re.match(r'^<\s*(\d+)\s*(.*)', devices)
    index = int(match.group(1))  # Extraer el número del índice y convertirlo a entero
    device_name = match.group(2)  # Extraer el nombre del dispositivo

    print(f"Dispositivo de salida por defecto es {device_name} con indice {index}")
    return device_name, index

    
def get_audio_device_list():
    devices = sd.query_devices()
    print(f'devicessssS: {devices}')
    # Crear listas separadas para dispositivos con 'hostapi': 0 y 'hostapi': 1
    mme_devices = [(index, dev['name']) for index, dev in enumerate(devices) if dev['hostapi'] == 0]
    ds_devices = [dev['name'] for dev in devices if dev['hostapi'] == 1]
    
    # Inicializar listas para los resultados
    device_list = []

    # Comparar nombres y buscar coincidencias
    for index, mme_device in mme_devices:
        for ds_device in ds_devices:
            if mme_device in ds_device:
                print(f"Dispositivo hostapi 1: {ds_device} - Índice hostapi 0: {index}")
                device_list.append(f'{ds_device} [{index}]')  # Agregar nombre del dispositivo hostapi 1
 # Agregar índice del dispositivo hostapi 0

    return device_list

def start_tkinter():
    global yellow_circle_image0
    global yellow_circle_image1
    global yellow_circle_image2
    state = "OFF"
    width = 0
    height = 0

    circle_images = {
        "yellow": [None, None, None],
        "red": [None, None, None],
        "green": [None, None, None]
    }
    
    circle_labels = {
        "yellow": [None, None, None],
        "red": [None, None, None],
        "green": [None, None, None]
    }

    window = tk.Tk()
    window.title("Bot de Twitch")
    window.geometry("700x500")

    main_frame = tk.Frame(window, background="cyan")
    main_frame.pack(fill='both', expand=True)

    # Crear un nuevo Frame para manejar los círculos con grid()
    circle_frame = tk.Frame(main_frame)
    circle_frame.pack(side='bottom', pady=10)  # Usamos pack para el frame completo

    output_device_label = tk.Label(main_frame, text="Dispositivo de salida:", background="blue")
    output_device_label.place(x=10, y=10)

    output_device_tk = tk.StringVar(window)
    device_list = get_audio_device_list()

    #output_device_tk.set(device_name)
    #selected_device = load_selected_device(window)

    #if selected_device:
    #    output_device_tk.set(selected_device)
    print(device_list[0])
    print(device_list[1])
    print(device_list[2])
    output_device_menu = ttk.Combobox(main_frame, textvariable=output_device_tk, values=device_list, background="red")
    output_device_menu.place(x=150, y=10, width=400)
    output_device_menu.bind("<<ComboboxSelected>>", lambda event: set_audio_device(output_device_tk, output_device_tk.get()))
    window.mainloop()


def set_audio_device(output_device_tk, device_name):
    output_device_tk.set(device_name)
    index = re.search(r'\[(\d+)\]', device_name).group(1) if re.search(r'\[(\d+)\]', device_name) else None
    print(f"Dispositivo de salida cambiado a {device_name} con indice {index}")
    return device_name, index



start_tkinter()