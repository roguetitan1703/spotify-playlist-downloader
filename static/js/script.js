document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("log_in").addEventListener("click", redirectToLogin)
    console.log("Is logged in:", isLoggedIn);
    console.log("User Id:", userId);
    console.log("User Name:", userName);

    if (isLoggedIn === true) {
        console.log("Its true", localStorage.getItem('isLoggedIn'))
        const loggedIn = document.getElementById("logged-in");
        const loggedOut = document.getElementById("logged-out");
        loggedIn.style.display =  'none';
        loggedOut.style.display = 'block';

        fetchUserPlaylists();
    } else {
        console.log("Its false", localStorage.getItem('isLoggedIn'))
    }

});

const appState = {
    buttonArea: null,
    downloadButtonsCard: null,
    current: null,
  };

async function redirectToLogin() {
    try {
        const response = await fetch('/login_user');
        const data = await response.json();
        const redirectLink = data.redirect_link;
        window.location.href = redirectLink;
    } catch (error) {
        console.error('Error:', error);
    }
}


async function fetchUserPlaylists() {
    try {
        const userId = localStorage.getItem('userId')
        if (userId) {
            const response = await fetch(`/get_user_playlists?user_id=${userId}`);
            const data = await response.json();

            if (data.status === 'success') {
                console.log("Playlists retrieval successfull")
                // get the playlists container
                const playlistsContainer = document.getElementById('playlist-container');
                playlistsContainer.innerHTML = ''; // Clear previous playlists

                const playlists = data.playlists

                // Looping through the playlists
                playlists.forEach(playlist => {
                    const playlistHTML = 
                    `
                    <div class="cards">
                    <div class="card_header">
                        <img src="${playlist.image}" height="180px" alt="top 50 songs">
                    </div>
                    <div class="card_body">
                        <div class="card_title">
                            <h5><strong>${playlist.name}</strong></h5>
                        </div>
                        <p>${playlist.description}</p>
                    </div>
                    <div class="button-area">
                    <a class="download-complete-button">
                    <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" class="bi bi-check-circle-fill" viewBox="0 0 16 16">
                        <circle cx="8" cy="8" r="7.5" fill="black"></circle>
                        <path fill="#1ED760" d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z">
                        </path>
                    </svg>
                    </a>
                    <div class="loading-spinner"></div>
                    <a class="download-button" data-playlist-id=${playlist.id}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 16 16" class="bi bi-arrow-down-circle-fill">
                        <circle cx="8" cy="8" r="7.5" fill="black"></circle>
                        <path fill="#1ED760" d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M8.5 4.5a.5.5 0 0 0-1 0v5.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293z">
                        </path>
                    </svg>
                    </a>
                    </div>
                    </div>
                    `;

                    playlistsContainer.innerHTML += playlistHTML; 

                });
                // Add eventlistenres to download button
                const downloadButtons = document.querySelectorAll('.download-button');
                downloadButtons.forEach(button => {
                    button.addEventListener('click', downloadPlaylist);
                });
            }
        }
        
    } catch (error) {
        console.log('Error:', error)
    }
}

async function showMessage(message) {
    console.log(message);
}

async function handleDownloadComplete(data) {
    appState.buttonArea.classList.remove('loading');
    appState.buttonArea.classList.add('download-complete');
    appState.current.removeEventListener('click', downloadPlaylist);

    showMessage(data.message);

    // Make a request to the server to fetch the file
    const response = await fetch(`/get_downloads?download_dir=${data.download_dir}`);

    // Convert the response to a blob
    const blob = await response.blob();

    // Create a URL for the blob
    const blobUrl = URL.createObjectURL(blob);

    // Create a temporary anchor element
    const tempLink = document.createElement('a');
    tempLink.href = blobUrl;
    tempLink.setAttribute('download', `${data.processToken}.zip`); // Specify the file name here
    tempLink.style.display = 'none';
    document.body.appendChild(tempLink);

    // Programmatically trigger the download
    tempLink.click();

    // Clean up
    URL.revokeObjectURL(blobUrl);
    document.body.removeChild(tempLink);
}


async function handleFailedDownload() {
    appState.buttonArea.classList.remove('loading');
    appState.downloadButtonsCard.classList.remove('highlight-card');
}

async function checkProgress(playlistId, prevProcessToken) {
    try {
        const progressResponse = await fetch(`/check_progress`);
        const progressData = await progressResponse.json();
        // console.log('Progress:', progressData);
        
        // if process is complete
        if (progressData.status === 'complete') {
            handleDownloadComplete(progressData);
            
        }
        
        else {
            showMessage(progressData.message);
            setTimeout(() => {
                checkProgress(playlistId, prevProcessToken);
            }, 5000);
        }
        // If the still proccessing
        // else if (progressData.status === 'processing') {
        //     if (progressData.processToken !== prevProcessToken) {
        //     showMessage(progressData.message);   
        //     console.log(prevProcessToken)
        //     } else {
        //         // Continue polling until download is complete
        //         setTimeout(() => {
        //             checkProgress(playlistId, progressData.processToken);
        //         }, 5000);
        //     }
        // } else {
        //     showMessage(progressData.message);
        // }

    } catch (error) {
        console.log('Error fetching progress:', error);
    }
}

async function downloadPlaylist(event) {
    try {
        const playlistId = this.getAttribute('data-playlist-id');

        // Show loading spinner
        const buttonArea = this.closest('.button-area');
        const downloadButtonsCard = this.closest('.cards');
        
        appState.buttonArea = buttonArea;
        appState.downloadButtonsCard = downloadButtonsCard;
        appState.current = this;

        appState.buttonArea.classList.add('loading');
        appState.downloadButtonsCard.classList.add('highlight-card');

        console.log("Playlist Id:", playlistId)

        const response = await fetch(`/download_playlist?playlist_id=${playlistId}`);
        
        const data = await response.json();
        
        if (data.status === 'processing') {


            console.log("Downloading Playlist");
            
            // Start polling to check progress
            checkProgress(playlistId, data.processToken);

        } else {
            console.log("Error downloading playlist");
            console.log(data.message);
            appState.buttonArea.classList.remove('loading');
            appState.downloadButtonsCard.classList.remove('highlight-card');
        }

        // Handle response...
    } catch (error) {
        console.log('Error:', error);

        // Hide loading spinner if an error occurs
        appState.buttonArea.classList.remove('loading');
    }
} 
