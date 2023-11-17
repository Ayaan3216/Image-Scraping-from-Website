import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin
import base64
from io import BytesIO
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

def extract_image_url(img_tag):
    for attr in ['src', 'data-src']:
        if attr in img_tag.attrs:
            return img_tag[attr]
    return None

def download_image(image_info):
    url, folder_path, index, image = image_info
    image_url = extract_image_url(image)
    if image_url:
        if image_url.startswith('data:image/gif;base64'):
            img_data = image_url.split(',')[1]
            img_data = base64.b64decode(img_data)
            image_name = f"base64_image_{index}.gif"
        else:
            image_url = urljoin(url, image_url)
            image_name = os.path.basename(urlparse(image_url).path)

        image_path = os.path.join(folder_path, image_name)

        if not image_url.startswith('data:image/gif;base64'):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            }

            response = requests.get(image_url, headers=headers, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=128):
                        file.write(chunk)
        else:
            with open(image_path, 'wb') as file:
                file.write(img_data)

def download_images(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors

        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img')

        if not images:
            print('No images found on the webpage.')
            return

        # Extract domain from the URL
        domain = urlparse(url).hostname
        if not domain:
            print('Invalid URL. Unable to determine domain.')
            return

        # Create a folder based on the domain in the same directory as the script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(script_dir, f'image_folder_{domain}')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        image_infos = [(url, folder_path, i, image) for i, image in enumerate(images)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(tqdm(executor.map(download_image, image_infos), total=len(image_infos), desc='Downloading Images'))

        print('Download complete!')
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    url = input('Enter the URL of the webpage: ')
    download_images(url)
