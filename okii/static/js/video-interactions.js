document.addEventListener('DOMContentLoaded', function() {
    const commentModal = document.getElementById('commentModal');
    const commentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');
    let currentVideoId = null;

    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(commentModal);

    // Modal handlers
    commentModal?.addEventListener('hidden.bs.modal', () => {
        commentForm?.reset();
        commentsList.innerHTML = '';
        currentVideoId = null;
    });

    // Comment button click handler
    document.querySelectorAll('.comment-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            currentVideoId = button.dataset.videoId;
            await loadComments(currentVideoId);
            modal.show();
        });
    });

    // Like button handler
    // document.querySelectorAll('.like-btn').forEach(button => {
    //     button.addEventListener('click', async () => {
    //         const videoId = button.dataset.videoId;
    //         try {
    //             const response = await fetch(`/user/video/${videoId}/like`, {
    //                 method: 'POST',
    //                 headers: {'Content-Type': 'application/json'}
    //             });
    //             const data = await response.json();
                
    //             if (response.ok) {
    //                 button.querySelector('.likes-count').textContent = data.likes;
    //                 button.classList.toggle('liked', data.liked);
    //             }
    //         } catch (error) {
    //             console.error('Error:', error);
    //         }
    //     });
    // });

    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', async function() {
            if (!this.dataset.videoId) return;
            
            try {
                const response = await fetch(`/user/video/${this.dataset.videoId}/like`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Update like count
                    const likeCount = this.querySelector('.likes-count');
                    if (likeCount) {
                        likeCount.textContent = data.likes_count;
                        likeCount.style.display = 'inline-block';  // Ensure visibility
                    }
                    
                    // Update button state
                    this.classList.toggle('btn-outline-primary', !data.liked);
                    this.classList.toggle('btn-primary', data.liked);
                    
                    // Update icon
                    const icon = this.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('far', !data.liked);
                        icon.classList.toggle('fas', data.liked);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });

    // Comment form handler
    commentForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = document.getElementById('comment-content').value.trim();
        
        if (!content || !currentVideoId) return;

        try {
            const response = await fetch(`/user/video/${currentVideoId}/comment`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ comment: content })
            });

            if (response.ok) {
                document.getElementById('comment-content').value = '';
                await loadComments(currentVideoId);
                updateCommentCount(currentVideoId);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});

async function loadComments(videoId) {
    const commentsList = document.getElementById('comments-list');
    try {
        const response = await fetch(`/user/video/${videoId}/comments`);
        const data = await response.json();
        
        commentsList.innerHTML = data.comments?.length 
            ? data.comments.map(comment => createCommentHTML(comment)).join('')
            : createEmptyCommentsHTML();
    } catch (error) {
        console.error('Error:', error);
        commentsList.innerHTML = createErrorHTML();
    }
}

function createCommentHTML(comment) {
    return `
        <div class="comment-item p-3 border-bottom">
            <div class="d-flex align-items-start">
                <div class="comment-avatar me-2">
                    <i class="fas fa-user-circle fa-2x text-secondary"></i>
                </div>
                <div class="comment-content flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong class="text-primary">${comment.username}</strong>
                        <small class="text-muted">${timeAgo(new Date(comment.created_at))}</small>
                    </div>
                    <p class="mb-0 mt-1">${comment.content}</p>
                </div>
            </div>
        </div>
    `;
}

function createEmptyCommentsHTML() {
    return `
        <div class="text-center py-4 text-muted">
            <i class="fas fa-comments fa-2x mb-2"></i>
            <p>No comments yet. Be the first to comment!</p>
        </div>
    `;
}

function createErrorHTML() {
    return `
        <div class="alert alert-danger">
            Error loading comments. Please try again.
        </div>
    `;
}

function updateCommentCount(videoId) {
    const commentBtn = document.querySelector(`.comment-btn[data-video-id="${videoId}"]`);
    const countSpan = commentBtn?.querySelector('.comments-count');
    if (countSpan) {
        countSpan.textContent = parseInt(countSpan.textContent) + 1;
    }
}

function timeAgo(date) {
    const now = new Date();
    const utc1 = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds());
    const utc2 = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), now.getMinutes(), now.getSeconds());
    const seconds = Math.floor((utc2 - utc1) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
        second: 1
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
        }
    }
    return 'just now';
}

// Update comment form handler to prevent double submission
commentForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitButton = e.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    
    const content = document.getElementById('comment-content').value.trim();
    if (!content || !currentVideoId) {
        submitButton.disabled = false;
        return;
    }

    try {
        const response = await fetch(`/user/video/${currentVideoId}/comment`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ comment: content })
        });

        if (response.ok) {
            document.getElementById('comment-content').value = '';
            await loadComments(currentVideoId);
            updateCommentCount(currentVideoId);
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        submitButton.disabled = false;
    }
});


