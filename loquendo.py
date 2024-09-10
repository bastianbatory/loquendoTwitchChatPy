import time
import threading
import requests
import base64
import wave
from pydub import AudioSegment
from datetime import datetime

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
        self.refresh_thread = threading.Thread(target=self.get_token, daemon=True)
        self.refresh_thread.start()

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

    def get_audio_file(self, text, voice, token):
        if not self.token:
            raise Exception("Token no disponible")
        
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
        inicio = time.time()  # Initialize 'inicio' here
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
            
            time = time.time() - inicio
            return audio_file_path
            response = "OK"
            #########################
            ####### PLAY ##############
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud de audio: {e}")
        except Exception as err:
            print(f"Error al generar el archivo de audio: {err}")

        
    
 #   def play_file

 #   def delete_file
