#!/usr/bin/env python3
"""
Data Validation Helpers - Prevent data structure bugs
"""
import logging
logger = logging.getLogger(__name__)

def safe_get_from_dict(obj, key, default=None):
    """Safely get value from object that should be a dict"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    else:
        logger.warning(f"Expected dict, got {type(obj)} for key {key}")
        return default

def safe_iterate_apps(apps_data):
    """Safely iterate over apps data"""
    if not isinstance(apps_data, list):
        logger.error(f"Expected list of apps, got {type(apps_data)}")
        return []
    
    validated_apps = []
    for app in apps_data:
        if isinstance(app, dict):
            validated_apps.append(app)
        else:
            logger.warning(f"Skipping non-dict app: {type(app)}")
    
    return validated_apps

def safe_calculate_stats(apps_list):
    """Safely calculate statistics from apps list"""
    if not isinstance(apps_list, list):
        return {'count': 0, 'avg_stars': 0, 'categories': []}
    
    valid_apps = [app for app in apps_list if isinstance(app, dict)]
    
    if not valid_apps:
        return {'count': 0, 'avg_stars': 0, 'categories': []}
    
    total_stars = sum(app.get('total_stars', 0) for app in valid_apps)
    avg_stars = total_stars / len(valid_apps) if valid_apps else 0
    
    categories = list(set(app.get('category', 'OTHER') for app in valid_apps))
    
    return {
        'count': len(valid_apps),
        'avg_stars': avg_stars,
        'categories': categories
    }
