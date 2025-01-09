from flask import Blueprint, render_template, request, jsonify
from okii.models import Video, get_trending_tags, get_popular_creators
from okii import mongo
from flask import Blueprint, render_template, request
from bson import ObjectId

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    try:
        sort = request.args.get('sort', 'latest')
        page = int(request.args.get('page', 1))
        per_page = 12
        print("Database collections:", mongo.db.list_collection_names())
       
        query = {}  
            
        all_videos = list(mongo.db.videos.find())
        print(f"Total videos in DB: {len(all_videos)}")
        for video in all_videos:
            print(f"Video: {video.get('title')} - {video.get('video_url')}")

        
        sort_order = [('created_at', -1)]
        if sort == 'popular':
            sort_order = [('views', -1)]
        elif sort == 'trending':
            sort_order = [('likes', -1)]

        
        videos = list(mongo.db.videos.find(query)
                     .sort(sort_order)
                     .skip((page-1)*per_page)
                     .limit(per_page))

        total_videos = mongo.db.videos.count_documents(query)
        total_pages = (total_videos + per_page - 1) // per_page

        return render_template('index.html',
                             videos=videos,
                             active_sort=sort,
                             current_page=page,
                             total_pages=total_pages,)

    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html',
                             videos=[],
                             active_sort='latest',
                             current_page=1,
                             total_pages=1)         
           
@main_bp.route('/search')
def search():
    try:
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 12

        if query:
            search_query = {
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}},
                    {'username': {'$regex': query, '$options': 'i'}}
                ]
            }
            
            
            videos = list(mongo.db.videos.find(search_query)
                        .sort('created_at', -1)
                        .skip((page-1)*per_page)
                        .limit(per_page))
            
            total_results = mongo.db.videos.count_documents(search_query)
        else:
            videos = []
            total_results = 0

        
        for video in videos:
            video['_id'] = str(video['_id'])
            if 'created_at' in video:
                video['created_at'] = video['created_at'].isoformat()

        return render_template('index.html',
                            videos=videos,
                            query=query,
                            total_results=total_results,
                            current_page=page,
                            total_pages=(total_results + per_page - 1) // per_page,
                            is_search=True)

    except Exception as e:
        print(f"Search error: {str(e)}")
        return render_template('index.html', 
                            videos=[],
                            query=query,
                            error="An error occurred during search")  
        
@main_bp.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            videos = list(mongo.db.videos.find().sort('created_at', -1).limit(12))
        else:
            videos = list(mongo.db.videos.find({
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            }).sort('created_at', -1))

        
        for video in videos:
            video['_id'] = str(video['_id'])
            
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    """API endpoint for live search suggestions"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    
    videos = list(mongo.db.videos.find(
        {'title': {'$regex': f'^{query}', '$options': 'i'}, 'visibility': 'public'},
        {'title': 1}
    ).limit(5))
    
    users = list(mongo.db.users.find(
        {'username': {'$regex': f'^{query}', '$options': 'i'}},
        {'username': 1}
    ).limit(5))
    
    tags = list(mongo.db.videos.distinct(
        'tags',
        {'tags': {'$regex': f'^{query}', '$options': 'i'}}
    ))[:5]
    
    suggestions = {
        'videos': [{'id': str(v['_id']), 'title': v['title']} for v in videos],
        'users': [{'id': str(u['_id']), 'username': u['username']} for u in users],
        'tags': [{'tag': tag} for tag in tags]
    }
    
    return jsonify(suggestions)