# 📋 Spotify Playlist Downloader

## 📝 Description

The Spotify Playlist Downloader is a web application that allows users to log in and download their Spotify playlists. The application mimics the design of Spotify, providing users with a familiar interface. Users can access their playlists, select the ones they want to download, and save them locally.

## 🌟 Features

- User Authentication (Login)
- Display Spotify Playlists
- Download Spotify Playlists
- Convert Spotify Playlist Tracks to Audio
- Mimics Spotify Design for Familiarity

## 💻 Technologies Used

- Backend: Python (FastAPI), MongoDB
- Frontend: HTML, CSS (Bootstrap), JavaScript (Vanilla)
- Spotify API
- YouTube API
- Pytube (Python YouTube API)
- Pydub (Audio Processing Library)

## 🛠️ Setup Instructions

1. Clone the repository to your local machine.
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate.bat  # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Create a `.env` file and add your Spotify API credentials.
   - Configure `oauth.json` file for YouTube API access.

5. Run the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```

6. Access the application in your web browser at `http://localhost:8000`.

## 🚀 Usage

1. Log in with your Spotify credentials.
2. Your Spotify playlists will be displayed similar to the Spotify interface.
3. Select the playlist you want to download.
4. The application will fetch the songs from the playlist and download them from YouTube.
5. Downloaded tracks will be saved locally in audio format.

## 📚 Additional Libraries and Frameworks

- FastAPI: Python web framework for building APIs.
- MongoDB: Document-oriented NoSQL database for storing user data and playlist information.
- Bootstrap: CSS framework for frontend design.

## Combined Takeaways and Challenges

The development of the Spotify Playlist Downloader involved several challenges and takeaways. One of the main challenges was integrating multiple APIs seamlessly to fetch playlist data from Spotify and download tracks from YouTube. Handling user authentication securely and efficiently was another key challenge.

Despite the challenges, the project provided valuable insights into API integration, authentication mechanisms, and frontend design. It highlighted the importance of thorough testing and robust error handling to ensure a smooth user experience.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
