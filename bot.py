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
import pyaudio
import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
import sounddevice as sd

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

token = config['TWITCH_OAUTH_TOKEN']
channel = config['TWITCH_CHANNEL']
ignored_names = config['IGNORED_USERS']
voice_command = config['COMMAND']
help_message = config['HELP_MESSAGE']
ignored_messages = config['IGNORED_MESSAGES_STARTS_WITH']

logger = None
#window = None

class Logger:
    def __init__(self, log_widget):
        self.log_widget = log_widget

    def log(self, message):
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)

def initialize_logger(log_widget):
    global logger
    logger = Logger(log_widget)

class Bot(commands.Bot):
    def __init__(self, loquendo, logger, volume_scale, output_device_var, window, red_label, yellow_label, green_label):
        self.loquendo = loquendo
        self.logger = logger
        self.volume_scale = volume_scale
        self.output_device_var = output_device_var
        self.window = window
        self.red_label = red_label
        self.yellow_label = yellow_label
        self.green_label = green_label
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.voice_mapping = self.load_voice_mapping()
        self.available_voices = ["Carlos", "Jorge", "Diego", "Javier", "Paulina-Ml", "Angelica", "Isabela", "Francisca", "Soledad"]

    def log(self, message):
        self.logger.log(message)


    def load_voice_mapping(self):
        try:
            with open('voice_mapping.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_voice_mapping(self):
        with open('voice_mapping.json', 'w') as f:
            json.dump(self.voice_mapping, f, indent=4)

    def on_device_selected(self, device_name):
        save_selected_device(device_name, self)
        self.output_device_var.set(device_name)
        self.log(f"Dispositivo de salida cambiado a {device_name}")
        print(f"Dispositivo de salida cambiado a {device_name}")

    async def event_ready(self):
        #self.log(f'Bot {self.nick} conectado ')
        print(f'Login en Twitch | {self.nick}')
        channel_obj = self.get_channel(channel)
        if channel_obj:
            print(f"Canal obtenido: {channel_obj.name}")
        else:
            print("No se pudo obtener el canal.")

    async def event_channel_joined(self, channel: Channel) -> None:
        if channel and hasattr(channel, 'name'):
            self.log(f'✔ [3/3] Conectado al canal de Twitch "{channel.name}" con el bot "{self.nick}"')

                # Forzar actualización de la ventana para que se muestre la imagen
            self.window.update()
            self.log(f'------------------------------------------------')
            self.log(f'✔✔✔ Todo listo, escuchando mensajes ✔✔✔')
            self.log(f'------------------------------------------------')
        else:
            self.log("❌ Error: El objeto canal no tiene un atributo 'name'")

    async def event_channel_join_failure(self, channel):
        self.log(f"❌ Error al conectar con el canal {channel}, canal no existe o hubo un error, revisa el archivo config.yaml")
        await asyncio.sleep(10)
        os._exit(1)

    async def event_message(self, message):
        def clean_message(msg):
            cleaned_msg = re.sub(r'\s+', ' ', msg).strip()
            return cleaned_msg

        in_message = clean_message(message.content)

        if message.author and message.author.name not in ignored_names:
            if in_message == voice_command:
                await message.channel.send(help_message)
            elif in_message.startswith(voice_command + ' '):
                await self.set_voice(message)
            else:
                if not self.is_command_or_link(in_message):
                    await self.process_message(message)

    async def process_message(self, message):

        texto = f"{message.author.name} dize: {message.content}"
        self.log(f"-----------------------------")
        self.log(f"Texto generado: {texto}")
        print(f"-----------------------------")
        print(f"Texto generado: {texto}")

        if message.author.name in self.voice_mapping:
            voz = self.voice_mapping[message.author.name]
        else:
            voz = random.choice(self.available_voices)
            self.voice_mapping[message.author.name] = voz
            self.save_voice_mapping()
        self.log(f"Voz configurada: {voz}")
        print(f"Voz configurada: {voz}")

        archivo_salida = f"{message.author.name}_{message.id}.wav"
        result = self.loquendo.tts(texto, voz, archivo_salida)

        if result["res"] == "OK":
            self.log(f"Mensaje de {message.author.name} sintetizado con éxito.")
            self.log(f"Voz sintetizada: {voz}")
            print(f"Mensaje de {message.author.name} sintetizado con éxito.")
            print(f"Voz sintetizada: {voz}")
            audio = AudioSegment.from_wav(archivo_salida)

            volumen = self.volume_scale.get()
            self.log(f"Volumen del audio: {volumen}")
            print(f"Volumen del audio: {volumen}")
            audio = audio + (volumen - 50)

            audio.export(archivo_salida, format="wav")
            self.log(f"Archivo de audio generado")
            print(f"Archivo de audio generado")

            p = pyaudio.PyAudio()

            output_device_name = self.output_device_var.get()
            self.log(f"Dispositivo de salida configurado: {output_device_name}")
            print(f"Dispositivo de salida configurado: {output_device_name}")

            output_device_index = get_output_device_index(output_device_name)

            if output_device_index is not None:
                self.log("Dispositivo de salida encontrado")
                print("Dispositivo de salida encontrado")

                stream = p.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=audio.frame_rate,
                                output=True,
                                output_device_index=output_device_index)
                self.log(f"Reproduciendo audio...")
                print(f"Reproduciendo audio...")           

                stream.write(audio.raw_data)
                self.log("Audio reproducido.")
                print("Audio reproducido.")
                
                stream.stop_stream()
                stream.close()
            else:
                self.log(f"❌ Dispositivo de salida no encontrado: {output_device_name}")
                print(f"❌ Dispositivo de salida no encontrado: {output_device_name}")

            os.remove(archivo_salida)
            self.log(f"Archivo de audio eliminado.")
            self.log(f"-----------------------------")
            print(f"Archivo de audio eliminado.")
            print(f"-----------------------------")
        elif '401' in str(result['res']):
            print(f"No autenticado con el servidor de voces: {result['res']}")
        else:
            self.log(f"❌ Error al sintetizar el mensaje de {message.author.name}: {result['res']}")
            self.log(f"-----------------------------")
            print(f"Error al sintetizar el mensaje de {message.author.name}: {result['res']}")
            print(f"-----------------------------")

    async def set_voice(self, message):
        try:
            voz = message.content.split(' ', 1)[1]
            self.log(f"Cambiando voz para {message.author.name}")
            print(f"Cambiando voz para {message.author.name}")

        except IndexError:
            await message.channel.send("Por favor, proporciona una voz válida.")
            self.log(f"Voz inválida")
            print(f"❌ Voz inválida")
            return
        
        if voz in self.available_voices:
            self.voice_mapping[message.author.name] = voz
            self.save_voice_mapping()
            await message.channel.send(f"Voz cambiada a {voz} para {message.author.name}")
            self.log(f"Voz cambiada a {voz} para {message.author.name}")
            self.log(f"-----------------------------")
            print(f"Voz cambiada a {voz} para {message.author.name}")
        else:
            await message.channel.send(f"La voz {voz} no existe o {message.author.name} ya la tiene")
            self.log(f"❌ La voz {voz} no existe o ya la tiene")
            self.log(f"-----------------------------")
            print(f"La voz {voz} no existe o ya la tiene")

    def is_command_or_link(self, content):
        return content.startswith(('!', *ignored_messages))

def list_mme_audio_devices():
    devices = sd.query_devices()
    mme_devices = []
    for i, device in enumerate(devices):
        if device['hostapi'] == 0:
            if device['max_output_channels'] > 0:
                mme_devices.append((i, device['name']))
    return mme_devices

def list_audio_output_devices():
    mme_devices = list_mme_audio_devices()
    output_devices = [name for _, name in mme_devices]
    return output_devices

def get_default_output_device():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['hostapi'] == 0 and device['max_output_channels'] > 0:
            name = device['name']
            if name.startswith('<'):
                return i, name
    return None, None

def get_output_device_index(device_name):
    mme_devices = list_mme_audio_devices()
    for index, name in mme_devices:
        if name == device_name:
            return index
    return None


def save_selected_device(device_name, bot_instance=None):
    with open('selected_device.json', 'w') as f:
        json.dump({"selected_device": device_name}, f)


async def run_bot(loquendo, logger, volume_scale, output_device_var, window, red_label, yellow_label, green_label):
    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var, window, red_label, yellow_label, green_label)
    try:
        await bot_instance.start()
    except errors.AuthenticationError:
        logger.log(f"❌ Token de Twitch incorrecto")

def load_selected_device(window):
    # Comprueba que el logger esté inicializado antes de usarlo
    if logger:
        logger.log(f"⏳ [0/3] Dispositivo de salida: Cargando...")
    else:
        print("Logger no inicializado.")

    if os.path.exists('selected_device.json'):
        with open('selected_device.json', 'r') as f:
            data = json.load(f)
            device_name = data.get("selected_device")
            
            if logger:
                logger.log(f"✔ [1/3] Dispositivo de salida: OK -> {device_name}")
            print(f"Dispositivo de salida cargado: {device_name}")

#                yellow_label.pack(side=tk.LEFT, padx=5)  # Posicionar el círculo a la derecha con un pequeño espacio


            return device_name
    return None

#def img():
#    a = tk.PhotoImage(window, file='./assets/yellow_circle.png' )
#    a.pack()

import tkinter as tk
from tkinter import ttk, scrolledtext

def start_tkinter_and_bot():
    def on_closing():
        if bot_instance:
            bot_instance.loop.run_until_complete(bot_instance.close())
        window.destroy()

    window = tk.Tk()
    window.title("Bot de Twitch")
    window.geometry("700x500")  # Ajusta el tamaño de la ventana

    # Marco principal
    main_frame = tk.Frame(window)
    main_frame.pack(fill='both', expand=True)

    # Menú desplegable de dispositivo de salida en la parte superior
    output_device_label = tk.Label(main_frame, text="Dispositivo de salida:")
    output_device_label.place(x=10, y=10)  # Posicionar con 'place'

    output_device_var = tk.StringVar(window)

    output_devices = list_audio_output_devices()
    selected_device = load_selected_device(window)

    if selected_device:
        output_device_var.set(selected_device)

    output_device_menu = ttk.Combobox(main_frame, textvariable=output_device_var, values=output_devices)
    output_device_menu.place(x=150, y=10, width=200)  # Posicionar con 'place'
    
    output_device_menu.bind("<<ComboboxSelected>>", lambda event: bot_instance.on_device_selected(output_device_var.get()))

    # Widget de texto para log
    log_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
    log_widget.place(x=10, y=50, width=480, height=350)  # Posicionar con 'place'

    # Barra de volumen a la derecha
    volume_label = tk.Label(main_frame, text="Volumen:")
    volume_label.place(x=520, y=50)  # Posicionar con 'place'

    volume_scale = tk.Scale(main_frame, from_=0, to=100, orient=tk.VERTICAL)
    volume_scale.set(50)
    volume_scale.place(x=520, y=80, height=320)  # Posicionar con 'place'

    # Marco para las luces de estado (Movido a la izquierda debajo del log_widget)
    status_frame = tk.Frame(main_frame)
    status_frame.place(x=10, y=410)  # Marco debajo del log_widget

    # Etiquetas y círculos de conexión a servidor de voces (verde)
    green_circle = tk.PhotoImage(file='./assets/green_circle.png').subsample(10, 10)
    green_label = tk.Label(status_frame, image=green_circle)
    green_label.grid(row=0, column=0, padx=5, pady=2)  # Usar 'grid' dentro del marco

    twitch_bot_label = tk.Label(status_frame, text="Conexion a servidor de voces")
    twitch_bot_label.grid(row=0, column=1, sticky='w')  # Etiqueta a la derecha del círculo verde

    # Círculo amarillo y etiqueta de conexión a Twitch [Bot]
    yellow_circle = tk.PhotoImage(file='./assets/yellow_circle.png').subsample(10, 10)
    yellow_label = tk.Label(status_frame, image=yellow_circle)
    yellow_label.grid(row=1, column=0, padx=5, pady=2)  # Círculo amarillo

    twitch_bot_label = tk.Label(status_frame, text="Conexion a Twitch [Bot]")
    twitch_bot_label.grid(row=1, column=1, sticky='w')

    # Círculo rojo y etiqueta de conexión a Twitch [Canal]
    red_circle = tk.PhotoImage(file='./assets/red_circle.png').subsample(10, 10)
    red_label = tk.Label(status_frame, image=red_circle)
    red_label.grid(row=2, column=0, padx=5, pady=2)  # Círculo rojo

    twitch_channel_label = tk.Label(status_frame, text="Conexion a Twitch [Canal]")
    twitch_channel_label.grid(row=2, column=1, sticky='w')

    # Inicialización del logger y resto del código funcional
    initialize_logger(log_widget)  # Inicializa el logger antes de cargar el dispositivo

    loquendo = Loquendo(log_callback=logger.log)
    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var, window, None, None, None)

    logger.log(f'⏳ [2/3] Canal de Twitch: Conectando...')

    try:
        bot_thread = threading.Thread(target=lambda: asyncio.run(run_bot(loquendo, logger, volume_scale, output_device_var, window, None, None, None)))
        bot_thread.start()

        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()

    except Exception as e:
        print(e)


if __name__ == "__main__":
    start_tkinter_and_bot()
