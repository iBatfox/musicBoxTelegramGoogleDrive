import asyncio
from io import BytesIO 
from telegram import Bot
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient import http as googleapiclient

# Параметры Google Диска
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Укажите путь к файлу учетных данных
FOLDER_ID = '1DY65saVpCSrFo505hkkEQbESSWk3exCs'  # ID папки с музыкой на Google Диске

# Параметры Telegram бота
TELEGRAM_TOKEN = '6524739739:AAFlJtJcQLeQPttPZ6EYgWE8juVpfbWhUgE'
GROUP_ID = -1002043738628 # ID вашей группы в Telegram (можно узнать, например, через бота @userinfobot)

async def download_music_from_drive():
    print("Downloading music from Google Drive...")
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    try:
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            fields="files(id, name)",
            pageToken=None
        ).execute()

        files = results.get('files', [])
        print(f"Found {len(files)} files in the folder.")

        bot = Bot(token=TELEGRAM_TOKEN)

        # Чтение списка уже отправленных файлов
        sent_files = set()
        try:
            with open('sent_files.txt', 'r') as file:
                sent_files = set(file.read().splitlines())
        except FileNotFoundError:
            pass

        for file in files:
            file_id = file.get('id')
            file_name = file.get('name')

            if file_name not in sent_files:
                try:
                    print(f"Sending file {file_name} to Telegram...")
                    request = service.files().get_media(fileId=file_id)
                    downloader = request.execute()

                    # Отправляем музыку в Telegram
                    audio_data = BytesIO(downloader)
                    audio_data.name = file_name
                    audio_data.seek(0)
                    await bot.send_audio(chat_id=GROUP_ID, audio=audio_data)

                    print(f"File {file_name} sent.")

                    # Добавляем отправленный файл в список отправленных файлов
                    sent_files.add(file_name)
                except Exception as e:
                    print(f"An error occurred while sending file {file_name}: {e}")

        # Запись списка отправленных файлов в файл
        with open('sent_files.txt', 'w') as file:
            file.write('\n'.join(sent_files))

    except Exception as e:
        print(f"An error occurred: {e}")

async def main():
    await download_music_from_drive()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
