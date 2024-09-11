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

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.window = window
      #  self.circle_images = circle_images
    #    self.circle_labels = circle_labels
     #   self.circle_frame = circle_frame
        self.blinking = False
  #      self.no_circle_image = self.load_circle_image("no")
  #      self.blink_delay = 500  # Retraso en milisegundos para el parpadeo
  #      self.blink_rows = []
        self.voice_mapping = self.load_voice_mapping()
        self.available_voices = ["Carlos", "Jorge", "Diego", "Javier", "Paulina-Ml", "Angelica", "Isabela", "Francisca", "Soledad"]

 #   def log(self, message):
 #       #self.logger.log(message)
    @commands.command()
    async def voz(self, ctx: commands.Context):
    # Here we have a command hello, we can invoke our command with our prefix and command name
    # e.g ?hello
    # We can also give our commands aliases (different names) to invoke with.

    # Send a hello back!
    # Sending a reply back to the channel is easy... Below is an example.
        print("vc", ctx.content)
        await ctx.send(f'Hello!{ctx.content}')

    async def event_message(self, message):

        if message.author and message.author.name not in ignored_users:
            print(message.content)
            if message.content.startswith(voice_command):
                print("1")
                message_text = re.sub(r'^!voz\s*', '', message.content)
                if not message_text:
                    await message.channel.send(help_message)
                    print(self.available_voices)
                    print(message_text)
                if message_text in self.available_voices:
                    print("3")
             #       await self.set_voice(message)
                    self.voice_mapping[message.author.name] = message_text
                    print(message_text)
                    await message.channel.send(f"/me Voz cambiada a {message_text} para {message.author.name}")
                    self.save_voice_mapping()
                else:
                    voices = ', '.join(self.available_voices)
                    await message.channel.send(f"/me La voz {message_text} no existe, voces disponibles: {voices}")

            if not message.content.startswith("!"):
                message_text = re.sub(r'^!voz\s*', '', message.content)
                tts_texto = f"{message.author.name} dize: {message_text}"

                if message.author.name in self.voice_mapping:
                    voice = self.voice_mapping[message.author.name]
                else:
                    voice = random.choice(self.available_voices)
                    self.voice_mapping[message.author.name] = voice
                    self.save_voice_mapping()
            #    #self.log(f"Voz configurada: {voz}")
                print(f"Voz configurada: {voice}")
                audio_file_path = None
                while audio_file_path is None:
                    audio_file_path = loquendo.get_audio_file(text=tts_texto, voice=voice, token=token_loquendo)
            # Print the contents of our message to console...
                volume = volume_scale.get()
                print(audio_file_path)
                print(volume)
                name, index = load_selected_device()
                print(index)
                loquendo.play_file(audio_file_path, volume, index)          
                print("playfile") 
                loquendo.delete_file(audio_file_path)
                print("delete") 

    def load_voice_mapping(self):
        try:
            with open('voice_mapping.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_voice_mapping(self):
        with open('voice_mapping.json', 'w') as f:
            json.dump(self.voice_mapping, f, indent=4)

    
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
  #      bot_instance.start_circle("green", 1)
  #      bot_instance.stop_circle("yellow", 1)
  #      bot_instance.stop_circle("red", 1)
        print(f'Login Bot en Twitch | {self.nick}')
        channel_obj = self.get_channel(channel)
        if channel_obj:
            print(f"Canal obtenido: {channel_obj.name}")
        else:
            print("No se pudo obtener el canal.")

    async def event_channel_joined(self, channel: Channel) -> None:
  #      bot_instance.start_circle("green", 2)
  #      bot_instance.stop_circle("yellow", 2)
   #     bot_instance.stop_circle("red", 2)

        if channel and hasattr(channel, 'name'):
            self.window.update()
        else:
            print("❌ Error: El objeto canal no tiene un atributo 'name'")

    async def event_channel_join_failure(self, channel):
#        self.stop_circle("green", 2)
 #       self.stop_circle("yellow", 2)
  #      self.start_circle("red", 2)
     #   #self.log(f"❌ Error al conectar con el canal {channel}, canal no existe o hubo un error, revisa el archivo config.yaml")
        try:
            print("error al conectar al canal")
            await asyncio.sleep(10)
            os._exit(1)
        except Exception as e:
            print(e)


    def is_command_or_link(self, content):
        return content.startswith(('!', *ignored_messages))
    


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
    print("metodo ok")
    global bot_instance
    bot_instance = Bot()
    print(type(channel))
    print("clase ok")
    try:
        await bot_instance.start()
        print("instance ok")
    except errors.AuthenticationError:
 #       bot_instance.start_circle("red", 1)
 #       bot_instance.stop_circle("yellow", 1)
 #       bot_instance.stop_circle("green", 1)
 #       logger.log(f"❌ Token de Twitch incorrecto")
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
    window.geometry("200x580")

    main_frame = tk.Frame(window)
    main_frame.pack(fill='both', expand=True)

    # Crear un nuevo Frame para manejar los círculos con grid()
    circle_frame = tk.Frame(main_frame)
    circle_frame.pack(side='top', pady=10)  # Frame de círculos en la parte superior

    # Etiquetas de conexión en el frame circle_frame
    twitch_bot_label = tk.Label(circle_frame, text="Conexion a servidor de voces")
    twitch_bot_label.grid(row=0, column=0, pady=5, sticky='w')

    twitch_bot_label = tk.Label(circle_frame, text="Conexion a Twitch [Bot]")
    twitch_bot_label.grid(row=1, column=0, pady=5, sticky='w')

    twitch_channel_label = tk.Label(circle_frame, text="Conexion a Twitch [Canal]")
    twitch_channel_label.grid(row=2, column=0, pady=5, sticky='w')

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

    return window

def run_bot_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_twitch_bot(token, channel))

def on_closing():
    stop_event.set()  # Señaliza el evento de parada
    window.destroy()  # Cierra la ventana
    sys.exit()
def token_loquendo():
    global token_loquendo
    while not stop_event.is_set():
        token_loquendo = loquendo.get_token()  
        print(token_loquendo)
  #      status = loquendo.test_token(token_loquendo)
  #      print(status)
        if token_loquendo:
            time.sleep(10)
        else:
            time.sleep(1)

#start_tkinter()
loquendo = Loquendo()
window = start_tkinter()
stop_event = threading.Event()

loquendo_thread = threading.Thread(target=token_loquendo, daemon=True)
loquendo_thread.start()

twitch_bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
twitch_bot_thread.start()

#run_bot(token=token, channel=channel)
#loquendo.get_audio_file(text, voice, token)

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
loquendo_thread.join()
twitch_bot_thread.join()
