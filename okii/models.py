from datetime import datetime
from bson import ObjectId
from flask_login import UserMixin
from okii import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    ROLES = {
        'creator': ['upload', 'watch', 'like', 'comment'],
        'consumer': ['watch', 'like', 'comment']
    }
    def __init__(self, user_data):
        if user_data is None:
            raise ValueError("User data cannot be None")
            
        self._user_data = user_data
        self._id = str(user_data.get('_id'))
        self._username = user_data.get('username')
        self._email = user_data.get('email')
        self._role = user_data.get('role', 'consumer')  
        self._password = user_data.get('password')
        self._created_at = user_data.get('created_at')
        self._avatar = user_data.get('avatar')
        self._bio = user_data.get('bio', '')
        self._followers = user_data.get('followers', [])
        self._following = user_data.get('following', [])
        self._is_active = user_data.get('is_active', True)
        self._is_admin = user_data.get('is_admin', False)
        self._last_login = user_data.get('last_login')
        
    @property
    def role(self):
        return self._role

    def has_permission(self, permission):
        return permission in self.ROLES.get(self._role, [])

    @property
    def is_creator(self):
        return self._role == 'creator'

    
    @property
    def id(self):
        return self._id

    @property
    def username(self):
        return self._username

    @property
    def email(self):
        return self._email

    @property
    def password(self):
        return self._password

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_admin(self):
        return self._is_admin

    def get_id(self):
        return str(self._id)

    @staticmethod
    def get(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    @staticmethod
    def get_by_email(email):
        try:
            user_data = mongo.db.users.find_one({'email': email.lower()})
            return User(user_data) if user_data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def update_last_login(self):
        try:
            mongo.db.users.update_one(
                {'_id': ObjectId(self._id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Error updating last login: {e}")

            
    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        return User(user_data) if user_data else None

    def update_profile(self, data):
        updates = {
            'bio': data.get('bio', self.bio),
            'avatar': data.get('avatar', self.avatar)
        }
        mongo.db.users.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': updates}
        )

    def follow(self, user_id):
        if user_id != self.id and user_id not in self.following:
            mongo.db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$push': {'following': user_id}}
            )
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$push': {'followers': self.id}}
            )
            return True
        return False

    def unfollow(self, user_id):
        if user_id in self.following:
            mongo.db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$pull': {'following': user_id}}
            )
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$pull': {'followers': self.id}}
            )
            return True
        return False

class Video:
    def __init__(self, video_data):
        self.video_data = video_data
        self.id = str(video_data['_id'])
        self.title = video_data.get('title')
        self.description = video_data.get('description', '')
        self.filename = video_data.get('filename')
        self.thumbnail = video_data.get('thumbnail')
        self.user_id = video_data.get('user_id')
        self.username = video_data.get('username')
        self.visibility = video_data.get('visibility', 'public')
        self.views = video_data.get('views', 0)
        self.likes = video_data.get('likes', [])
        self.comments = video_data.get('comments', [])
        self.tags = video_data.get('tags', [])
        self.created_at = video_data.get('created_at', datetime.utcnow())


    @staticmethod
    def create(data):
        video = {
            'title': data['title'],
            'description': data.get('description', ''),
            'filename': data['filename'],
            'thumbnail': data.get('thumbnail'),
            'user_id': data['user_id'],
            'username': data['username'],
            'visibility': data.get('visibility', 'public'),
            'views': 0,
            'likes': [],
            'comments': [],
            'tags': [tag.strip() for tag in data.get('tags', '').split(',') if tag.strip()],
            'created_at': datetime.utcnow()
        }
        result = mongo.db.videos.insert_one(video)
        video['_id'] = result.inserted_id
        return Video(video)

    @staticmethod
    def get(video_id):
        video_data = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        return Video(video_data) if video_data else None

    @staticmethod
    def get_user_videos(user_id, sort_by='created_at', limit=None):
        """Get user's videos with sorting options"""
        try:
            query = {'user_id': user_id}
            cursor = mongo.db.videos.find(query).sort([(sort_by, -1)])
            if limit:
                cursor = cursor.limit(limit)
            return [Video(video) for video in cursor]
        except Exception as e:
            print(f"Error fetching user videos: {e}")
            return []

    @staticmethod
    def get_public_videos(sort_by='created_at', limit=None):
        """Get public videos with sorting options"""
        try:
            query = {'visibility': 'public'}
            cursor = mongo.db.videos.find(query).sort([(sort_by, -1)])
            if limit:
                cursor = cursor.limit(limit)
            return [Video(video) for video in cursor]
        except Exception as e:
            print(f"Error fetching public videos: {e}")
            return []


    def add_view(self):
        mongo.db.videos.update_one(
            {'_id': ObjectId(self.id)},
            {'$inc': {'views': 1}}
        )
        self.views += 1

    def toggle_like(self, user_id):
        if user_id in self.likes:
            mongo.db.videos.update_one(
                {'_id': ObjectId(self.id)},
                {'$pull': {'likes': user_id}}
            )
            self.likes.remove(user_id)
            return False
        else:
            mongo.db.videos.update_one(
                {'_id': ObjectId(self.id)},
                {'$push': {'likes': user_id}}
            )
            self.likes.append(user_id)
            return True

    def add_comment(self, user_id, username, text):
        comment = {
            'user_id': user_id,
            'username': username,
            'text': text,
            'created_at': datetime.utcnow()
        }
        mongo.db.videos.update_one(
            {'_id': ObjectId(self.id)},
            {'$push': {'comments': comment}}
        )
        self.comments.append(comment)
        return comment

def get_trending_tags(limit=10):
    """Get trending tags based on video count and recency"""
    pipeline = [
        {
            '$match': {
                'visibility': 'public',
                'tags': {'$exists': True, '$ne': []}
            }
        },
        {'$unwind': '$tags'},
        {
            '$group': {
                '_id': '$tags',
                'count': {'$sum': 1},
                'total_views': {'$sum': '$views'},
                'total_likes': {
                    '$sum': {
                        '$cond': {
                            'if': {'$isArray': '$likes'},
                            'then': {'$size': '$likes'},
                            'else': 0
                        }
                    }
                }
            }
        },
        {
            '$project': {
                'tag': '$_id',
                'count': 1,
                'score': {
                    '$add': [
                        '$count',
                        {'$divide': ['$total_views', 100]},
                        {'$multiply': ['$total_likes', 2]}
                    ]
                }
            }
        },
        {'$sort': {'score': -1}},
        {'$limit': limit}
    ]
    
    try:
        return list(mongo.db.videos.aggregate(pipeline))
    except Exception as e:
        print(f"Error in get_trending_tags: {e}")
        return []
    
def get_popular_creators(limit=5):
    """Get popular creators based on their video metrics"""
    pipeline = [
        {
            '$match': {
                'visibility': 'public'  
            }
        },
        {
            '$group': {
                '_id': '$user_id',
                'username': {'$first': '$username'},
                'video_count': {'$sum': 1},
                'total_views': {'$sum': '$views'},
                'total_likes': {
                    '$sum': {
                        '$cond': {
                            'if': {'$isArray': '$likes'},
                            'then': {'$size': '$likes'},
                            'else': 0
                        }
                    }
                }
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'user_info'
            }
        },
        {
            '$addFields': {
                'user_info': {'$arrayElemAt': ['$user_info', 0]}
            }
        },
        {
            '$project': {
                'username': 1,
                'video_count': 1,
                'total_views': 1,
                'total_likes': 1,
                'avatar': '$user_info.avatar',
                'followers': {
                    '$size': {
                        '$cond': {
                            'if': {'$isArray': '$user_info.followers'},
                            'then': '$user_info.followers',
                            'else': []
                        }
                    }
                }
            }
        },
        {
            '$sort': {
                'total_views': -1,
                'total_likes': -1,
                'video_count': -1
            }
        },
        {
            '$limit': limit
        }
    ]
    
    try:
        return list(mongo.db.videos.aggregate(pipeline))
    except Exception as e:
        print(f"Error in get_popular_creators: {e}")
        return []

def create_user(username, email, password):
    user = {
        'username': username,
        'email': email,
        'password': password,
        'avatar': None,
        'bio': '',
        'followers': [],
        'following': [],
        'created_at': datetime.utcnow()
    }
    result = mongo.db.users.insert_one(user)
    user['_id'] = result.inserted_id
    return user


def get_all_videos():
    """Get all videos for admin view, regardless of visibility"""
    videos = mongo.db.videos.find().sort('created_at', -1)
    return [Video(video) for video in videos]

def get_all_users():
    """Get all users for admin view"""
    users = mongo.db.users.find().sort('created_at', -1)
    return [User(user) for user in users]

def get_system_stats():
    """Get system statistics for admin dashboard"""
    return {
        'total_users': mongo.db.users.count_documents({}),
        'total_videos': mongo.db.videos.count_documents({}),
        'total_public_videos': mongo.db.videos.count_documents({'visibility': 'public'}),
        'total_private_videos': mongo.db.videos.count_documents({'visibility': 'private'}),
        'total_views': sum(video['views'] for video in mongo.db.videos.find({}, {'views': 1})),
        'total_likes': sum(len(video.get('likes', [])) for video in mongo.db.videos.find({}, {'likes': 1})),
        'total_comments': sum(len(video.get('comments', [])) for video in mongo.db.videos.find({}, {'comments': 1}))
    }