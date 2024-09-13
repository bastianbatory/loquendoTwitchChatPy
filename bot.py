import os
import json
import yaml
import re
import time
import random
import threading
from twitchio.ext import commands
from twitchio import Channel
from twitchio import errors
from loquendo import Loquendo
from pydub import AudioSegment
import sys
import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
import sounddevice as sd

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

token = config['TWITCH_OAUTH_TOKEN']
channel = config['TWITCH_CHANNEL']
ignored_users = config['IGNORED_USERS']
voice_command = config['COMMAND']
help_message = config['HELP_MESSAGE']
ignored_messages = config['IGNORED_MESSAGES_STARTS_WITH']

output_device_tk=None
token_loquendo = None
update_queue = asyncio.Queue()

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.blinking = False
        self.available_voices = ["Carlos", "Jorge", "Diego", "Javier", "Paulina-Ml", "Angelica", "Isabela", "Francisca", "Soledad"]

    async def event_message(self, message):
        if (message.author and message.author.name not in ignored_users):
            print(message.content)
            if message.content.startswith(voice_command):
                message_args = re.sub(r'^!voz\s*', '', message.content)
                if not message_args:
                    await message.channel.send(help_message)
                    print(self.available_voices)
                    print(message_args)
                if message_args in self.available_voices:
                    voice_mapping[message.author.name] = message_args
                    print(message_args)
                    await message.channel.send(f"/me Voz cambiada a {message_args} para {message.author.name}")
                    save_voice_mapping()
                else:
                    voices = ', '.join(self.available_voices)
                    await message.channel.send(f"/me La voz {message_args} no existe, voces disponibles: {voices}")

            if not message.content.startswith("!"):
                message_args = re.sub(r'^!voz\s*', '', message.content)
                tts_texto = f"{message.author.name} dize: {message_args}"

                if message.author.name in voice_mapping:
                    voice = voice_mapping[message.author.name]
                else:
                    voice = random.choice(self.available_voices)
                    voice_mapping[message.author.name] = voice
                    save_voice_mapping()
                print(f"Voz configurada: {voice}")
                audio_file_path = None
                while audio_file_path is None:
                    audio_file_path = loquendo.get_audio_file(text=tts_texto, voice=voice, token=token_loquendo)
                    await asyncio.sleep(1)
                show_circle("green", 0)
                volume = volume_scale.get()
                name, index = load_selected_device()
                file = loquendo.play_file(audio_file_path, volume, index)
                if not file:
                    show_circle("red", 0)
                loquendo.delete_file(audio_file_path)

    
    async def event_ready(self):        
        print(f'Login Bot en Twitch | {self.nick}')
        channel_obj = self.get_channel(channel)
        if channel_obj:
            print(f"Canal obtenido: {channel_obj.name}")
            show_circle("green", 1)
        else:
            print("error al conectar el bot")
            show_circle("red", 1)
            await asyncio.sleep(10)
            os._exit(1)


    async def event_channel_joined(self, channel: Channel) -> None:
        show_circle("green", 2)
        if channel and hasattr(channel, 'name'):
            window.update()
        else:
            print("❌ Error: El objeto canal no tiene un atributo 'name'")
            show_circle("red", 2)

    async def event_channel_join_failure(self, channel):
        try:
            print("error al conectar al canal")
            show_circle("red", 2)
            await asyncio.sleep(10)
            os._exit(1)
        except Exception as e:
            print(e)

    
def update_circle(color, row):    
    circle_images[color][row] = tk.PhotoImage(file=f'./assets/{color}_circle.png').subsample(10, 10)
    circle_labels[color][row] = tk.Label(circle_frame, image=circle_images[color][row])
    circle_labels[color][row].grid(row=row, column=0, padx=5, pady=2)

    if color == "yellow":
        def toggle_circle():
            circle_images.setdefault("no_circle", [None] * len(circle_labels[color]))
            if circle_labels[color][row].cget("image") == str(circle_images[color][row]):
                circle_images["no_circle"][row] = tk.PhotoImage(file='./assets/no_circle.png').subsample(10, 10)
                circle_labels[color][row].config(image=circle_images["no_circle"][row])
            else:
                circle_images[color][row] = tk.PhotoImage(file=f'./assets/{color}_circle.png').subsample(10, 10)
                circle_labels[color][row].config(image=circle_images[color][row])
            window.after(500, toggle_circle)
        toggle_circle()
    else:
        circle_labels[color][row].config(image=circle_images[color][row])


async def circles():
    while not stop_event.is_set():
        color, row = await update_queue.get()  
        update_circle(color, row)
        await asyncio.sleep(0) 

def show_circle(color, row):
    asyncio.ensure_future(update_queue.put((color, row)))

def get_default_device():
    default_input, index_def = sd.default.device
    devices = sd.query_devices()
    if not devices:
       print("no devices")
       sys.exit() 
    mme_devices = [(index, dev['name']) for index, dev in enumerate(devices) if dev['hostapi'] == 0]
    ds_devices = [dev['name'] for dev in devices if dev['hostapi'] == 1]

    for index, mme_device in mme_devices:
        if index is index_def:
            for ds_device in ds_devices:
                if mme_device in ds_device:
                    out_channels = int(devices[index]['max_output_channels'])
                    if out_channels > 0:
                        return ds_device, index


def set_audio_device(output_device_tk, device_name_index):
    output_device_tk.set(device_name_index)
    index = re.search(r'\[(\d+)\]', device_name_index).group(1) if re.search(r'\[(\d+)\]', device_name_index) else None
    index = int(index)
    device_name = re.sub(r'\s*\[\d+\]', '', device_name_index)
    
    save_selected_device(device_name, index)
    print(f"Dispositivo de salida cambiado a {device_name} con indice {index}")

    return device_name, index

def get_audio_device_list():
    devices = sd.query_devices()
    if not devices:
       print("no devices")
       sys.exit()
    mme_devices = [(index, dev['name']) for index, dev in enumerate(devices) if dev['hostapi'] == 0]
    ds_devices = [dev['name'] for dev in devices if dev['hostapi'] == 1]
    device_list = []

    for index, mme_device in mme_devices:
        for ds_device in ds_devices:
            if mme_device in ds_device:

                out_channels = int(devices[index]['max_output_channels'])
                if out_channels > 0:
                    device_list.append(f'{ds_device} [{index}]')  

    return device_list


def save_selected_device(device_name, index):
    with open('selected_device.json', 'w') as f:
        json.dump({"selected_device": device_name, "index": index}, f)


async def run_twitch_bot(token, channel):
    global bot_instance
    bot_instance = Bot()
    try:
       # show_circle("yellow", 1)
        await bot_instance.start()
        print("instance ok")
    except errors.AuthenticationError:
 #       bot_instance.start_circle("red", 1)
 #       bot_instance.stop_circle("yellow", 1)
 #       bot_instance.stop_circle("green", 1)
 #       logger.log(f"❌ Token de Twitch incorrecto")
        show_circle("red", 1)
        print("instance no")
        await asyncio.sleep(10)
        os._exit(1)


def load_selected_device():
    if os.path.exists('selected_device.json'):
        with open('selected_device.json', 'r') as f:
            data = json.load(f)
            device_name = data.get("selected_device")
            device_index = data.get("index")
            return device_name, device_index
    return None

#def img():
#    a = tk.PhotoImage(window, file='./assets/yellow_circle.png' )
#    a.pack()

def start_tkinter():
    global circle_images
    global circle_labels
    global circle_frame

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
    window.geometry("200x580")

    main_frame = tk.Frame(window)
    main_frame.pack(fill='both', expand=True)

    # Crear un nuevo Frame para manejar los círculos con grid()
    circle_frame = tk.Frame(main_frame)
    circle_frame.pack(side='top', pady=10)  # Frame de círculos en la parte superior

    # Etiquetas de conexión en el frame circle_frame
    twitch_bot_label = tk.Label(circle_frame, text="Conexion a servidor de voces")
    twitch_bot_label.grid(row=0, column=1, pady=5, sticky='w')

    twitch_bot_label = tk.Label(circle_frame, text="Conexion a Twitch [Bot]")
    twitch_bot_label.grid(row=1, column=1, pady=5, sticky='w')

    twitch_channel_label = tk.Label(circle_frame, text="Conexion a Twitch [Canal]")
    twitch_channel_label.grid(row=2, column=1, pady=5, sticky='w')

    # Frame para Volumen y Fader
    volume_frame = tk.Frame(main_frame)
    volume_frame.pack(side='top', pady=(10, 0), fill='x', padx=10)

    # Etiqueta de volumen
    volume_label = tk.Label(volume_frame, text="Volumen:")
    volume_label.pack(side='top', pady=(0, 5))

    # Escala de volumen
    global volume_scale
    volume_scale = tk.Scale(volume_frame, from_=100, to=0, orient=tk.VERTICAL, length=320)
    volume_scale.set(75)
    volume_scale.pack(side='top', fill='y', expand=True)

    # Frame para Dispositivo de salida y ComboBox
    device_frame = tk.Frame(main_frame)
    device_frame.pack(side='bottom', pady=10, fill='x', padx=10)

    # Etiqueta de dispositivo de salida
    output_device_label = tk.Label(device_frame, text="Dispositivo de salida:")
    output_device_label.pack(side='top', pady=(0, 5))

    # ComboBox de dispositivos de salida
    default_device, ind = get_default_device()
    selected_device, a = load_selected_device()
    if selected_device:
        device = selected_device
        output_device_tk = tk.StringVar(window, device)
        output_device_tk.set(device)
    elif default_device:
        device = f'{default_device} [{ind}]'
        output_device_tk = tk.StringVar(window, device)
        output_device_tk.set(device)
        save_selected_device(default_device, ind)

    device_list = get_audio_device_list()
    output_device_menu = ttk.Combobox(device_frame, textvariable=output_device_tk, values=device_list)
    output_device_menu.pack(side='top', pady=(0, 20), fill='x')  # Llenar horizontalmente y un poco de padding abajo

    output_device_menu.bind("<<ComboboxSelected>>", lambda event: set_audio_device(output_device_tk, output_device_tk.get()))
    print("6")

    print("5")

    return window

def load_voice_mapping():
    try:
        with open('voice_mapping.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_voice_mapping():
    with open('voice_mapping.json', 'w') as f:
        json.dump(voice_mapping, f, indent=4)

#def run_bot_in_thread():
#    loop = asyncio.new_event_loop()
#    asyncio.set_event_loop(loop)
#    loop.run_until_complete(run_twitch_bot(token, channel))

def on_closing():
    stop_event.set()  # Señaliza el evento de parada
    window.destroy()  # Cierra la ventana
    sys.exit()

async def token_loquendo():
    global token_loquendo
    while not stop_event.is_set():
        token_loquendo = await loquendo.get_token()  
        if token_loquendo:
            show_circle("green", 0)
            await asyncio.sleep(10)
        else:
            show_circle("red", 0)
            await asyncio.sleep(1)


async def main():
    global loquendo
    global stop_event
    global window
    global voice_mapping
    voice_mapping = load_voice_mapping()
    loquendo = Loquendo()

    stop_event = threading.Event()
    
    asyncio.create_task(circles())
    show_circle("yellow", 0)
    show_circle("yellow", 1)
    show_circle("yellow", 2)
    await asyncio.gather(run_twitch_bot(token, channel), token_loquendo())


async def a():
    print("a")

async def b():
    print("b")

if __name__ == "__main__":
    window = start_tkinter() 
    
    second_thread = threading.Thread(target=asyncio.run, args=(main(),), daemon=True)
    second_thread.start()
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()

