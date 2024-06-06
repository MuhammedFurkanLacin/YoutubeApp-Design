import sys
import os
import sqlite3
from googleapiclient.discovery import build
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QGridLayout, QVBoxLayout, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QEvent, QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

__version__ = 'v1.2'
__author__ = 'Muhammed Furkan LAÇİN'

# YouTube API anahtarını buraya ekleyin
YOUTUBE_API_KEY = ''

# YouTube API istemcisi oluştur
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_videos_by_keyword(keyword):
    # YouTube arama isteği oluştur
    request = youtube.search().list(
        q=keyword,
        part='snippet',
        type='video',
        maxResults=10
    )
    response = request.execute()

    videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_thumbnail = item['snippet']['thumbnails']['default']['url']
        videos.append({'id': video_id, 'title': video_title, 'thumbnail': video_thumbnail})
    return videos

def get_video_info(video_id):
    # YouTube video bilgileri isteği oluştur
    request = youtube.videos().list(
        part='snippet',
        id=video_id
    )
    response = request.execute()

    if response['items']:
        video_title = response['items'][0]['snippet']['title']
        video_url = f'http://www.youtube.com/embed/{video_id}?rel=0'
        return {'title': video_title, 'url': video_url}
    return None

def add_video_to_database(video_id, video_title, video_url):
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Youtube')
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)
    database_path = os.path.join(desktop_path, 'video_database.db')

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT
        )
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO videos (id, title, url)
        VALUES (?, ?, ?)
    ''', (video_id, video_title, video_url))

    conn.commit()
    conn.close()

class YoutubePlayer(QWidget):
    def __init__(self, video_id, parent=None):
        super().__init__()
        self.parent = parent
        self.video_id = video_id

        # WebEngine ayarları
        defaultSettings = QWebEngineSettings.globalSettings()
        defaultSettings.setFontSize(QWebEngineSettings.MinimumFontSize, 28)

        # Widget düzeni
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Web view ekleniyor
        self.addWebView(self.video_id)

    def addWebView(self, video_id):
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl(f'http://www.youtube.com/embed/{video_id}?rel=0'))
        self.layout.addWidget(self.webview)

    def updateVideo(self, video_id):
        self.video_id = video_id
        video_info = get_video_info(self.video_id)
        if video_info:
            add_video_to_database(self.video_id, video_info['title'], video_info['url'])
            self.webview.setUrl(QUrl(video_info['url']))

class YoutubeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Youtube Video Oynatıcı')
        self.setWindowIcon(QIcon('Resimler/Kaydedilmiş Resimler/Youtube.png'))
        self.setMinimumSize(1800, 600)
        self.players = []
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Arama kutusu ve arama butonu
        self.searchInput = QLineEdit()
        self.searchButton = QPushButton('Ara', clicked=self.searchVideo)
        self.searchInput.setPlaceholderText('Video Adı Girin')

        self.layout.addWidget(self.searchInput)
        self.layout.addWidget(self.searchButton)

        # Video listesi
        self.videoList = QListWidget()
        self.videoList.itemClicked.connect(self.videoSelected)
        self.layout.addWidget(self.videoList)

        # Video oynatıcı
        self.player = YoutubePlayer('lTUMU7Zf7yA', parent=self)
        self.layout.addWidget(self.player)

        # Bilgi etiketi
        self.layout.addWidget(QLabel(__version__ + ' tarafından ' + __author__), alignment=Qt.AlignBottom | Qt.AlignRight)

        # Stil
        self.setStyleSheet("""
          * {
             background-color: white;
             font-size: 30px;
          }

          QLineEdit {
              background-color: white;
          }

          QListWidget {
              background-color: white;
          }
        """)

        # Veritabanı dosyasının tam yolunu bul
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Youtube')
        database_path = os.path.join(desktop_path, 'video_database.db')
        print(f"Veritabanı Dosyasının Tam Yolu: {database_path}")

    def searchVideo(self):
        keyword = self.searchInput.text()
        videos = get_videos_by_keyword(keyword)

        self.videoList.clear()
        for video in videos:
            item = QListWidgetItem(video['title'])
            item.setData(Qt.UserRole, video['id'])
            item.setIcon(QIcon(QPixmap(video['thumbnail'])))
            self.videoList.addItem(item)

    def videoSelected(self, item):
        video_id = item.data(Qt.UserRole)
        self.player.updateVideo(video_id)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = YoutubeWindow()
    window.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Oynatıcı Penceresi Kapatıldı')
