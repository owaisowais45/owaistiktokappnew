document.addEventListener('DOMContentLoaded', function() {
    const inlineSearch = document.getElementById('inline-search');
    const searchInput = document.getElementById('search-input');
    const clearSearch = document.getElementById('clear-search');
    const videosContainer = document.getElementById('videos-container');

    inlineSearch?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const query = searchInput.value.trim();
        
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (response.ok) {
                videosContainer.innerHTML = data.videos.map(video => createVideoCard(video)).join('');
                
                // Update URL without page reload
                const url = new URL(window.location);
                url.searchParams.set('q', query);
                window.history.pushState({}, '', url);
                
                // Show clear button
                clearSearch.style.display = 'block';
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    });

    clearSearch?.addEventListener('click', function(e) {
        e.preventDefault();
        searchInput.value = '';
        window.location.href = window.location.pathname;
    });
});

function createVideoCard(video) {
    return `
        <div class="col-md-4 mb-4">
            <div class="card h-100">
                <div class="video-thumbnail position-relative">
                    <a href="/watch/${video._id}">
                        <video class="card-img-top">
                            <source src="${video.video_url}" type="video/mp4">
                        </video>
                        <span class="badge bg-dark position-absolute bottom-0 end-0 m-2">
                            ${video.views || 0} views
                        </span>
                    </a>
                </div>
                <div class="card-body">
                    <h5 class="card-title">${video.title}</h5>
                    <p class="card-text text-muted">${video.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary like-btn" data-video-id="${video._id}">
                                <i class="far fa-heart"></i>
                                <span class="likes-count">${video.likes?.length || 0}</span>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary comment-btn" data-video-id="${video._id}">
                                <i class="far fa-comment"></i>
                                <span class="comments-count">${video.comments?.length || 0}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.querySelector('input[name="q"]');
    const videosContainer = document.querySelector('.row.row-cols-1');

    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (!query) return;

            try {
                const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
                if (response.ok) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        });
    }
});