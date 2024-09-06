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
    def __init__(self, loquendo, logger, volume_scale, output_device_var, window, circle_images, circle_labels, circle_frame):
        self.loquendo = loquendo
        self.logger = logger
        self.volume_scale = volume_scale
        self.output_device_var = output_device_var
        self.window = window
        self.circle_images = circle_images
        self.circle_labels = circle_labels
        self.circle_frame = circle_frame
        self.blinking = False
        self.no_circle_image = self.load_circle_image("no")
        self.blink_delay = 500  # Retraso en milisegundos para el parpadeo
        self.blink_rows = []
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

    
    def start_circle(self, color, row):
        """Enciende el círculo del color dado en la fila especificada."""
        if self.circle_images[color][row] is None:
            self.circle_images[color][row] = self.load_circle_image(color)
        
        self.circle_labels[color][row] = tk.Label(self.circle_frame, image=self.circle_images[color][row])
        self.circle_labels[color][row].grid(row=row, column=0, padx=5, pady=2)

    def stop_circle(self, color, row):
        """Apaga el círculo del color dado en la fila especificada."""
        if self.circle_labels[color][row] is not None:
            self.circle_labels[color][row].grid_forget()
            self.circle_labels[color][row] = None

    def load_circle_image(self, image_name):
        """Cargar la imagen del círculo según el nombre de archivo."""
        try:
            return tk.PhotoImage(file=f'./assets/{image_name}_circle.png').subsample(10, 10)
        except Exception as e:
            print(f"Error al cargar la imagen {image_name}.png: {e}")
            return None

    def blink_yellow_circle(self, rows):
        """Hace que los círculos amarillos parpadeen alternando entre el círculo y no_circle."""
        if not self.blinking:
            self.blinking = True
            self.blink_rows = rows
            self._blink_all_circles()
        else:
            self.blinking = False
            self._reset_circles()

    def _blink_all_circles(self):
        """Parpadea todos los círculos amarillos sincronizadamente."""
        if self.blinking:
            for row in self.blink_rows:
                label = self.circle_labels["yellow"][row]
                if label:
                    if label.cget("image") == str(self.circle_images["yellow"][row]):
                        label.config(image=self.no_circle_image)
                    else:
                        label.config(image=self.circle_images["yellow"][row])
            # Vuelve a llamar a _blink_all_circles después del retraso
            self.window.after(self.blink_delay, self._blink_all_circles)

    def _reset_circles(self):
        """Restablece la imagen de todos los círculos amarillos."""
        for row in self.blink_rows:
            label = self.circle_labels["yellow"][row]
            if label:
                label.config(image=self.circle_images["yellow"][row])

    async def event_ready(self):
        #self.log(f'Bot {self.nick} conectado ')
        bot_instance.start_circle("green", 1)
        bot_instance.stop_circle("yellow", 1)
        bot_instance.stop_circle("red", 1)
        print(f'Login Bot en Twitch | {self.nick}')
        channel_obj = self.get_channel(channel)
        if channel_obj:
            print(f"Canal obtenido: {channel_obj.name}")
        else:
            print("No se pudo obtener el canal.")

    async def event_channel_joined(self, channel: Channel) -> None:
        bot_instance.start_circle("green", 2)
        bot_instance.stop_circle("yellow", 2)
        bot_instance.stop_circle("red", 2)
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
        self.stop_circle("green", 2)
        self.stop_circle("yellow", 2)
        self.start_circle("red", 2)
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


async def run_bot(loquendo, logger, volume_scale, output_device_var, window, circle_images, circle_labels, circle_frame):
    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var, window, circle_images, circle_labels, circle_frame)
    try:
        await bot_instance.start()
    except errors.AuthenticationError:
        bot_instance.start_circle("red", 1)
        bot_instance.stop_circle("yellow", 1)
        bot_instance.stop_circle("green", 1)
        logger.log(f"❌ Token de Twitch incorrecto")
        await asyncio.sleep(10)
        os._exit(1)


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

def start_tkinter_and_bot():
    global yellow_circle_image0
    global yellow_circle_image1
    global yellow_circle_image2
    state = "OFF"
    width = 0
    height = 0

    def on_closing():
        if bot_instance:
            bot_instance.loop.run_until_complete(bot_instance.close())
        window.destroy()

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

    output_device_var = tk.StringVar(window)
    output_devices = list_audio_output_devices()
    selected_device = load_selected_device(window)

    if selected_device:
        output_device_var.set(selected_device)

    output_device_menu = ttk.Combobox(main_frame, textvariable=output_device_var, values=output_devices, background="red")
    output_device_menu.place(x=150, y=10, width=200)

    output_device_menu.bind("<<ComboboxSelected>>", lambda event: bot_instance.on_device_selected(output_device_var.get()))

    log_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, background="green")
    log_widget.place(x=10, y=50, width=480, height=350)

    volume_label = tk.Label(main_frame, text="Volumen:", background="yellow")
    volume_label.place(x=520, y=50)

    volume_scale = tk.Scale(main_frame, from_=0, to=100, orient=tk.VERTICAL, background="yellow")
    volume_scale.set(50)
    volume_scale.place(x=520, y=80, height=320)

    # Usa el frame circle_frame para los círculos con grid()
    twitch_bot_label = tk.Label(circle_frame, text="Conexion a servidor de voces")
    twitch_bot_label.grid(row=0, column=1, sticky='w')

    twitch_bot_label = tk.Label(circle_frame, text="Conexion a Twitch [Bot]")
    twitch_bot_label.grid(row=1, column=1, sticky='w')

    twitch_channel_label = tk.Label(circle_frame, text="Conexion a Twitch [Canal]")
    twitch_channel_label.grid(row=2, column=1, sticky='w')

    initialize_logger(log_widget)

    loquendo = Loquendo(log_callback=logger.log)
    global bot_instance
    bot_instance = Bot(loquendo, logger, volume_scale, output_device_var, window, circle_images, circle_labels, circle_frame)

    # Utilizamos grid() en el frame circle_frame para evitar conflictos
    bot_instance.start_circle("yellow", 0)
    bot_instance.start_circle("yellow", 1)
    bot_instance.start_circle("yellow", 2)
    bot_instance.blink_yellow_circle([0, 1, 2])

    
    logger.log(f'⏳ [2/3] Canal de Twitch: Conectando...')

    try:
        bot_thread = threading.Thread(target=lambda: asyncio.run(run_bot(loquendo, logger, volume_scale, output_device_var, window, circle_images, circle_labels, circle_frame)))
        bot_thread.start()


        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()

    except Exception as e:
        print(e)


if __name__ == "__main__":
    start_tkinter_and_bot()
