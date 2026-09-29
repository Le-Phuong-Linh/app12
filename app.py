import streamlit as st
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pathlib import Path
import shutil

# =====================================================
# STREAMLIT UI CONFIGURATION
# =====================================================
st.set_page_config(page_title="MyDramaList Photo Downloader", page_icon="🖼️", layout="centered")

st.title("🖼️ MyDramaList Bulk Photo Downloader")
st.write("Enter the MyDramaList gallery URL and select the page range. The app will scrape full-size images, save them, and let you download the resulting collection as a ZIP archive[cite: 11].")

# =====================================================
# SIDEBAR / USER INPUTS
# =====================================================
st.sidebar.header("Download Settings")
base_url = st.sidebar.text_input(
    "Gallery Base URL", 
    value="https://mydramalist.com/54939-love-in-flames-of-war/photos"
)
start_page = st.sidebar.number_input("Start Page", min_value=1, value=1)
end_page = st.sidebar.number_input("End Page", min_value=1, value=3)

# =====================================================
# PROCESSING LOGIC
# =====================================================
def download_mdl_bulk_photos(base_url, start_page, end_page, status_placeholder):
    output_dir = Path("temp_mdl_photos")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Referer": "https://mydramalist.com/"
    }

    total_downloaded = 0
    log_messages = []

    for page in range(start_page, end_page + 1):
        page_url = f"{base_url}?page={page}"
        log_messages.append(f"=== Processing Page {page} of {end_page} ===")
        status_placeholder.text("\n".join(log_messages[-10:]))
        
        try:
            response = requests.get(page_url, headers=headers, timeout=15)
            if response.status_code != 200:
                log_messages.append(f"[ERROR] Skipped page {page}. Status code: {response.status_code}")
                continue
        except Exception as e:
            log_messages.append(f"[ERROR] Connection failed for page {page}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img", class_="mdl-rounded")
        
        image_urls = []
        for img in img_tags:
            if not img.has_attr("src"):
                continue
            src = img["src"]
            
            # Upgrade quality to original 'f.jpg'[cite: 11]
            if "m.jpg" in src:
                src = src.replace("m.jpg", "f.jpg")
            elif "s.jpg" in src:
                src = src.replace("s.jpg", "f.jpg")
            elif "t.jpg" in src:
                src = src.replace("t.jpg", "f.jpg")
                
            if src not in image_urls:
                image_urls.append(src)

        if not image_urls:
            log_messages.append(f"No photos found on page {page}.")
            continue

        log_messages.append(f"Found {len(image_urls)} unique photos on page {page}. Downloading...")
        status_placeholder.text("\n".join(log_messages[-10:]))

        for idx, img_url in enumerate(image_urls, start=1):
            try:
                parsed_url = urlparse(img_url)
                filename = os.path.basename(parsed_url.path)
                
                if not filename or "." not in filename:
                    filename = f"page{page}_photo_{idx}.jpg"
                    
                filepath = output_dir / filename
                
                if filepath.exists():
                    continue

                img_response = requests.get(img_url, headers=headers, timeout=10)
                if img_response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(img_response.content)
                    total_downloaded += 1
            except Exception:
                pass

        time.sleep(1)

    # Create ZIP archive
    archive_name = "mdl_photos_archive"
    shutil.make_archive(archive_name, "zip", output_dir)
    return f"{archive_name}.zip", total_downloaded, log_messages

# =====================================================
# MAIN ACTION BUTTON
# =====================================================
if st.button("Start Downloading Photos"):
    if not base_url:
        st.error("Please provide a valid gallery URL.")
    else:
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        try:
            with st.spinner("Scraping and downloading images... Please wait."):
                zip_path, count, logs = download_mdl_bulk_photos(base_url, int(start_page), int(end_page), status_placeholder)
                
            st.success(f"Done! Successfully downloaded {count} full-size photos[cite: 11].")
            
            with open(zip_path, "rb") as fp:
                st.download_button(
                    label="📦 Download Photos (ZIP)",
                    data=fp,
                    file_name="mydramalist_photos.zip",
                    mime="application/zip"
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")