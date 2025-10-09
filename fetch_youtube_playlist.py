import requests
import re
import json
import os
from bs4 import BeautifulSoup

def fetch_playlist_videos(playlist_id):
    """Fetch video information from a YouTube playlist."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch playlist: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try to extract the JSON data that contains video information
    pattern = r'var ytInitialData = (.+?);</script>'
    matches = re.search(pattern, response.text)
    
    videos = []
    
    if matches:
        json_str = matches.group(1)
        try:
            data = json.loads(json_str)
            
            # Navigate through the JSON structure to find video items
            contents = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [{}])[0].get('tabRenderer', {}).get('content', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [{}])[0].get('playlistVideoListRenderer', {}).get('contents', [])
            
            for item in contents:
                video_renderer = item.get('playlistVideoRenderer', {})
                if not video_renderer:
                    continue
                
                video_id = video_renderer.get('videoId', '')
                title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', 'Untitled Video')
                
                if video_id and title:
                    videos.append({
                        'id': video_id,
                        'title': title,
                        'embed_url': f"https://www.youtube.com/embed/{video_id}"
                    })
        except json.JSONDecodeError:
            print("Failed to parse JSON data")
    
    # If we couldn't extract from JSON, try parsing HTML directly
    if not videos:
        print("Falling back to HTML parsing...")
        video_elements = soup.select('a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer')
        
        for element in video_elements:
            href = element.get('href', '')
            if '/watch?v=' in href:
                video_id = href.split('v=')[1].split('&')[0]
                title_element = element.select_one('h3')
                title = title_element.text.strip() if title_element else 'Untitled Video'
                
                videos.append({
                    'id': video_id,
                    'title': title,
                    'embed_url': f"https://www.youtube.com/embed/{video_id}"
                })
    
    return videos

def update_html_with_videos(videos, html_file_path):
    """Update the HTML file with the fetched videos."""
    if not videos:
        print("No videos to update!")
        return
    
    # Read the current HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Create sidebar navigation items
    sidebar_items = ""
    for i, video in enumerate(videos):
        topic_id = f"topic-{i+1}"
        sidebar_items += f"""
                        <li><a href="#" data-target="{topic_id}" class="{'active' if i == 0 else ''}">{video['title']}</a></li>"""
    
    # Create content sections for each video
    content_sections = ""
    for i, video in enumerate(videos):
        topic_id = f"topic-{i+1}"
        content_sections += f"""
                    <!-- {video['title']} -->
                    <div id="{topic_id}" class="topic-content{'active' if i == 0 else ''}">
                        <h2 class="mb-4">{video['title']}</h2>
                        <div class="video-container">
                            <iframe src="{video['embed_url']}" title="{video['title']}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                        </div>
                        <div class="content-description">
                            <h4>What You'll Learn</h4>
                            <ul>
                                <li>Key concepts from this video</li>
                                <li>Important techniques covered</li>
                                <li>Practical applications</li>
                                <li>Related topics</li>
                                <li>Next steps</li>
                            </ul>
                            <div class="topic-navigation d-md-none mt-4">
                                <div class="d-flex justify-content-between">
                                    <button class="btn btn-outline-primary btn-sm prev-topic"><i class="fas fa-arrow-left me-1"></i> Previous</button>
                                    <button class="btn btn-primary btn-sm next-topic">Next <i class="fas fa-arrow-right ms-1"></i></button>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
    
    # Find and replace the sidebar navigation
    sidebar_pattern = r'<ul id="topicList" class="list-unstyled mb-0">(.*?)</ul>'
    updated_html = re.sub(sidebar_pattern, f'<ul id="topicList" class="list-unstyled mb-0">{sidebar_items}\n                    </ul>', html_content, flags=re.DOTALL)
    
    # Find and replace the content sections
    content_pattern = r'<div class="col-lg-9">(.*?)</div>\s+</div>\s+</div>\s+</section>'
    updated_html = re.sub(content_pattern, f'<div class="col-lg-9">{content_sections}\n                </div>\n            </div>\n        </div>\n    </section>', updated_html, flags=re.DOTALL)
    
    # Write the updated HTML back to the file
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(updated_html)
    
    print(f"Updated {html_file_path} with {len(videos)} videos!")

if __name__ == "__main__":
    playlist_id = "PL4-IK0AVhVjOJs_UjdQeyEZ_cmEV3uJvx"
    html_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "courses", "frontend-learning.html")
    
    print(f"Fetching videos from playlist: {playlist_id}")
    videos = fetch_playlist_videos(playlist_id)
    
    print(f"Found {len(videos)} videos")
    for i, video in enumerate(videos):
        print(f"{i+1}. {video['title']} - {video['embed_url']}")
    
    update_html_with_videos(videos, html_file_path)