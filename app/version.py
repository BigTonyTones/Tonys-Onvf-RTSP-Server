"""
Version management for Tonys Onvif-RTSP Server
Single source of truth for version information
"""

CURRENT_VERSION = "5.7.1"

def parse_version(version_str):
    """
    Parse version string like 'v5.5.0' or '5.5.0' into a list of integers [5, 5, 0]
    
    Args:
        version_str: Version string to parse
        
    Returns:
        List of integers representing version components
    """
    try:
        # Remove 'v' prefix if present
        clean_version = version_str.lstrip('v')
        parts = clean_version.split('.')
        return [int(p) for p in parts]
    except (ValueError, AttributeError):
        return [0, 0, 0]

def compare_versions(current, latest):
    """
    Compare two version strings
    
    Args:
        current: Current version string (e.g., '5.5.0')
        latest: Latest version string (e.g., '5.6.0')
        
    Returns:
        -1 if current < latest (update available)
         0 if current == latest (up to date)
         1 if current > latest (current is newer)
    """
    curr_parts = parse_version(current)
    late_parts = parse_version(latest)
    
    # Compare each component
    for i in range(max(len(curr_parts), len(late_parts))):
        curr_val = curr_parts[i] if i < len(curr_parts) else 0
        late_val = late_parts[i] if i < len(late_parts) else 0
        
        if curr_val < late_val:
            return -1
        elif curr_val > late_val:
            return 1
    
    return 0

def is_newer_version(current, latest):
    """
    Check if latest version is newer than current version
    
    Args:
        current: Current version string
        latest: Latest version string
        
    Returns:
        True if latest is newer than current
    """
    return compare_versions(current, latest) == -1
