import time
import threading
import requests
import base64
import wave
from pydub import AudioSegment
from datetime import datetime
import pyaudio
import os

class Loquendo:
    def __init__(self):
        self.session = requests.Session()
        if not self.session:
            raise Exception("No se pudo inicializar la sesión de requests")
        self.headers = {
            "user-agent": "PostmanRuntime/7.37.3",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "Cookie": "AWSALB=t4cqRO8QDNPjvFX1cnfjSJr7h7LU1AQ+6QwpYamc1oj5yHct51znARozVNyGI/Scx1/ZcJ9XtdPB2TidcdGueD6QEuYGFZEgUXujSQpDK7zSipZRNGnfKTc3cnAO"
        }
        self.session.headers.update(self.headers)
        self.token = None

    def get_token(self):
        token_url = 'https://www.nuance.com/bin/nuance/ttstoken.json'

        try:
            response = self.session.post(token_url)
            response.raise_for_status()  # Check for HTTP errors
            json_response = response.json()
            self.token = json_response.get("token")
            print(f"Token obtenido: {self.token}")
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener el token: {e}")
        except ValueError as e:
            print(f"Error al procesar la respuesta JSON: {e}")

    def test_token(self, token):
        url = 'https://tts.api.nuance.com/api/v1/synthesize'
        data = {
            "voice": {
                "name": "Francisca",
                "model": "standard"
            },
            "input": {
                "text": {
                    "text": "text"
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response2 = self.session.post(url, json=data, headers=headers)
        response2.raise_for_status()  # Check for HTTP errors
        json_response = response2.json()
        status = json_response.get("status", {}).get("code")
        if status == 200:
            return "ok"


    def get_audio_file(self, text, voice, token):
        print("generando archivo")
        if not self.token:
            raise Exception("Token no disponible")
        
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
        audio_file_path = f'{voice}_{fecha_hora_actual}.wav'

        url = 'https://tts.api.nuance.com/api/v1/synthesize'
        data = {
            "voice": {
                "name": voice,
                "model": "standard"
            },
            "input": {
                "text": {
                    "text": text
                }
            }
        }
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            response2 = self.session.post(url, json=data, headers=headers)
            response2.raise_for_status()  # Check for HTTP errors
            json_response = response2.json()
            audio64 = json_response.get("audio")
            if audio64 is None:
                raise Exception("No se recibió audio en la respuesta")
            
            bytes_audio = base64.b64decode(audio64)
            with wave.open(audio_file_path, "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(22050)
                f.writeframes(bytes_audio)
            print("path", audio_file_path)
            return audio_file_path

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud de audio: {e}")
        except Exception as err:
            print(f"Error al generar el archivo de audio: {err}")

        
    
    def play_file(self, path, volume, device_index):
        audio = AudioSegment.from_wav(path)
        dB = (volume / 100) * 40 - 30
        print("db", dB)
        audio = audio + dB
        p = pyaudio.PyAudio()
        if device_index is not None:
            stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=audio.frame_rate,
                output=True,
                output_device_index=device_index)
            stream.write(audio.raw_data)
            stream.stop_stream()
            stream.close()

    def delete_file(self, path):
        os.remove(path)
