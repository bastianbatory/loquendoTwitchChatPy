import os
import json
from dotenv import load_dotenv
from twitchio.ext import commands
from loquendo import Loquendo
from pydub import AudioSegment
from pydub.playback import play
import random

class Bot(commands.Bot):

    def __init__(self, loquendo):
        load_dotenv()  # Cargar variables de entorno desde el archivo .env
        token = os.getenv('TWITCH_OAUTH_TOKEN')
        channel = os.getenv('TWITCH_CHANNEL')
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.loquendo = loquendo
        self.voice_mapping = self.load_voice_mapping()  # Cargar las preferencias de voz desde el archivo JSON
        self.available_voices = ["Carlos", "Jorge", "Diego", "Javier", "Paulina-Ml", "Angelica", "Isabela", "Francisca", "Soledad"]

    def load_voice_mapping(self):
        try:
            with open('voice_mapping.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_voice_mapping(self):
        with open('voice_mapping.json', 'w') as f:
            json.dump(self.voice_mapping, f, indent=4)

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        # Verificar si el mensaje tiene un autor válido
 #       if message.author:
        if message.author and message.author.name != self.nick:
            # Comprobar si el mensaje es un comando !voz
            if message.content.startswith('!voz'):
                await self.set_voice(message)
            else:
                # Verificar si el mensaje es un comando o un enlace
                if not self.is_command_or_link(message.content):
                    await self.process_message(message)

    async def process_message(self, message):
        # Sintetizar el mensaje a voz
        texto = f"{message.author.name} dice: {message.content}"
        
        if message.author.name in self.voice_mapping:
            voz = self.voice_mapping[message.author.name]  # Obtener la voz asignada para este usuario
        else:
            voz = random.choice(self.available_voices)  # Seleccionar una voz aleatoria si no hay una voz asignada
            self.voice_mapping[message.author.name] = voz  # Asignar la voz seleccionada al usuario
            self.save_voice_mapping()  # Guardar la asociación entre el nombre de usuario y la voz en el archivo JSON

        archivo_salida = f"{message.author.name}_{message.id}.wav"  # Nombre del archivo de salida
        result = self.loquendo.tts(texto, voz, archivo_salida)

        if result["res"] == "OK":
            print(f"Mensaje de {message.author.name} sintetizado con éxito. Voz utilizada: {voz}")
            # Reproducir el archivo de audio
            audio = AudioSegment.from_wav(archivo_salida)
            play(audio)

            # Eliminar el archivo después de reproducirlo
            os.remove(archivo_salida)
            print(f"Archivo {archivo_salida} eliminado.")
        else:
            print(f"Error al sintetizar el mensaje de {message.author.name}: {result['res']}")

        await super().event_message(message)  # Llama al método event_message de la clase padre

    async def set_voice(self, message):
        # Obtener el nombre de la voz del mensaje
        voz = message.content.split(' ', 1)[1]
        # Verificar si la voz está disponible
        if voz in self.available_voices:
            # Asignar la voz al usuario
            self.voice_mapping[message.author.name] = voz
            self.save_voice_mapping()  # Guardar la asociación entre el nombre de usuario y la voz en el archivo JSON
            await message.channel.send(f"Voz cambiada a {voz} para {message.author.name}")
        else:
            await message.channel.send(f"La voz {voz} no está disponible")

    def is_command_or_link(self, content):
        # Verificar si el contenido comienza con un comando o contiene un enlace
        return content.startswith('!') or 'http://' in content or 'https://' in content

if __name__ == '__main__':
    loquendo = Loquendo()
    bot = Bot(loquendo)
    bot.run()
