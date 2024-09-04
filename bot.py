import os
import json
import yaml
import re
import time
import random
import threading
from twitchio.ext import commands
from twitchio import Channel
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
    def __init__(self, loquendo, logger, volume_scale, output_device_var):
        self.loquendo = loquendo
        self.logger = logger
        self.volume_scale = volume_scale
        self.output_device_var = output_device_var
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
            self.log(f"{voz}")
            self.log(f"{self.available_voices}")
            self.voice_mapping[message.author.name] = voz
            self.save_voice_mapping()
            await message.channel.send(f"Voz cambiada a {voz} para {message.author.name}")
            self.log(f"Voz cambiada a {voz} para {message.author.name}")
            print(f"Voz cambiada a {voz} para {message.author.name}")
        else:
            await message.channel.send(f"La voz {voz} no existe o {message.author.name} ya la tiene")
            self.log(f"❌ La voz {voz} no existe o ya la tiene")
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


async def run_bot(loquendo, logger, volume_scale, output_device_var):
    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var)
    await bot_instance.start()


def load_selected_device(bot_instance=None):
    logger.log(f"⏳ [0/3] Dispositivo de salida: Cargando...")
    if os.path.exists('selected_device.json'):
        with open('selected_device.json', 'r') as f:
            data = json.load(f)
            device_name = data.get("selected_device")
            logger.log(f"✔ [1/3] Dispositivo de salida: OK -> {device_name}")
            print(f"Dispositivo de salida cargado: {device_name}")
            return device_name
    return None

def start_tkinter_and_bot():
    def on_closing():
        if bot_instance:
            bot_instance.loop.run_until_complete(bot_instance.close())
        window.destroy()

    window = tk.Tk()
    window.title("Bot de Twitch")

    log_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=50, height=20)
    log_widget.pack()

    volume_label = tk.Label(window, text="Volumen:")
    volume_label.pack()

    volume_scale = tk.Scale(window, from_=0, to=100, orient=tk.HORIZONTAL)
    volume_scale.set(50)
    volume_scale.pack()

    output_device_label = tk.Label(window, text="Dispositivo de salida:")
    output_device_label.pack()

    initialize_logger(log_widget)  # Inicializa el logger antes de cargar el dispositivo

    output_devices = list_audio_output_devices()
    output_device_var = tk.StringVar(window)
    selected_device = load_selected_device()  # Ahora debería funcionar sin problemas

    if selected_device:
        output_device_var.set(selected_device)

    output_device_menu = ttk.Combobox(window, textvariable=output_device_var, values=output_devices)
    output_device_menu.pack()

    loquendo = Loquendo(log_callback=logger.log)

    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var)
    
    output_device_menu.bind("<<ComboboxSelected>>", lambda event: bot_instance.on_device_selected(output_device_var.get()))

    logger.log(f'⏳ [2/3] Canal de Twitch: Conectando...')
    bot_thread = threading.Thread(target=lambda: asyncio.run(run_bot(loquendo, logger, volume_scale, output_device_var)))
    bot_thread.start()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()


if __name__ == "__main__":
    start_tkinter_and_bot()
