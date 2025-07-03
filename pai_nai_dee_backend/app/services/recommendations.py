from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..models.places import Place
from ..models.activity_log import UserActivityLog
from ..schemas.places import PlaceBase # Assuming a base schema for Place exists or will be created

def get_recommendations_for_user(db: Session, user_id: int, limit: int = 10):
    """
    Generates place recommendations for a user.
    Initial simple logic:
    1. Places bookmarked by the user.
    2. Most frequently viewed places by the user.
    3. (Fallback) Most popular places overall (e.g., by number of reviews or bookmarks if implemented).
       For now, let's use recently added places as a proxy for popular if no user activity.
    """
    recommendations = []
    place_ids_added = set()

    # 1. Places bookmarked by the user (activity_type 'bookmark_place' needs to be defined)
    bookmarked_places = (
        db.query(Place)
        .join(UserActivityLog, Place.id == UserActivityLog.place_id)
        .filter(UserActivityLog.user_id == user_id, UserActivityLog.activity_type == "bookmark_place")
        .order_by(desc(UserActivityLog.timestamp))
        .limit(limit)
        .all()
    )
    for place in bookmarked_places:
        if place.id not in place_ids_added:
            recommendations.append(place)
            place_ids_added.add(place.id)
            if len(recommendations) >= limit:
                return recommendations

    # 2. Most frequently viewed places by the user
    viewed_places = (
        db.query(Place, func.count(UserActivityLog.id).label("view_count"))
        .join(UserActivityLog, Place.id == UserActivityLog.place_id)
        .filter(UserActivityLog.user_id == user_id, UserActivityLog.activity_type == "view_place")
        .group_by(Place.id)
        .order_by(desc("view_count"), desc(func.max(UserActivityLog.timestamp)))
        .limit(limit - len(recommendations))
        .all()
    )
    for place_view in viewed_places:
        place = place_view[0] # The Place object
        if place.id not in place_ids_added:
            recommendations.append(place)
            place_ids_added.add(place.id)
            if len(recommendations) >= limit:
                return recommendations

    # 3. Fallback: Recently added distinct places if not enough recommendations
    if len(recommendations) < limit:
        fallback_places = (
            db.query(Place)
            .order_by(desc(Place.created_at))
            .limit(limit - len(recommendations))
            .all()
        )
        for place in fallback_places:
            if place.id not in place_ids_added: # Ensure no duplicates if somehow they exist
                recommendations.append(place)
                place_ids_added.add(place.id)
                if len(recommendations) >= limit:
                    break

    return recommendations

# Placeholder for more advanced recommendation logic later
# e.g., using collaborative filtering or content-based filtering.
# def get_advanced_recommendations(db: Session, user_id: int, limit: int = 10):
#     # Logic using ML libraries or more complex queries
#     pass
