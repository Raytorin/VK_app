from pprint import pprint

from progress.bar import Bar

from datetime import datetime

import requests

import time

from pydrive.auth import GoogleAuth

from pydrive.drive import GoogleDrive

import os

class GoogleUploader:
    def __init__(self, user_auth):
        self.user_auth = user_auth

    def upload(self, file_path: str):
        print('Save photo to the cloud')
        bar_upload = Bar('Processing', max=vk.vk_max_len, suffix='%(percent)d%%')
        drive = GoogleDrive(self.user_auth)

        folder_id = 'parent_folder_id'

        file_metadata = {'title': f'{file_path}', 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.folder'}
        folder_google = drive.CreateFile(file_metadata)
        folder_google.Upload()

        folders_all = drive.ListFile({'q': "title='" + f'{file_path}' + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()

        for data_photo in vk.max_size():
            correct_date = str(data_photo[2]).replace(':', '.')
            filename_img = f'{data_photo[1]} likes, {correct_date}'
            api = requests.get(data_photo[0])
            content_img = api.content
            with open('images/' + filename_img, 'wb') as f:
                f.write(content_img)
            for correct_folder in folders_all:
                if correct_folder['title'] == file_path:
                    upload_file = drive.CreateFile({'parents': [{'id': correct_folder['id']}]})
                    upload_file.SetContentFile('images/' + filename_img)
                    upload_file.Upload()
                    bar_upload.next()
            os.remove('images/' + filename_img)
        return
        

class YaUploader:
    def __init__(self, token: str):
        self.token = token
    
    def get_headers(self):
        return {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}
    
    def create_folder(self, disk_file_path):
        create_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.put(create_url, headers=headers, params=params)
    
    def _get_upload_link(self, disk_file_path, folder):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {"path": f'{folder}/%s' % disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload(self, file_path: str):
        print('Save photo to the cloud')
        bar_upload = Bar('Processing', max=vk.vk_max_len, suffix='%(percent)d%%')
        self.create_folder(file_path)
        for data_photo in vk.max_size():
            correct_date = str(data_photo[2]).replace(':', '.')
            response_link = self._get_upload_link(f'{data_photo[1]} likes, {correct_date}', file_path)
            href = response_link.get("href", "")
            bar_upload.next()
            api = requests.get(data_photo[0])
            response = requests.put(href, data=api.content)

class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': 1} 
        response = requests.get(url, params={**self.params, **params})
        time.sleep(0.33)
        return response.json()

    def max_size(self):
        limit_count = 0
        needed_data = []
        correct_photo = []
        dict_photo = self.users_info()
        for needed_data_level_1 in dict_photo['response']['items']:
            all_sum_size_1 = []
            for needed_data_level_2 in needed_data_level_1['sizes']:
                sum_size_1 = needed_data_level_2['height'] + needed_data_level_2['width']
                all_sum_size_1.append(sum_size_1)
            all_sum_size_1.sort(reverse=True)
            needed_data.append(all_sum_size_1[0])
        needed_data.sort(reverse=True)
        if dict_photo['response']['count'] >= 5:
            while True:
                for correct_photo_level_1 in dict_photo['response']['items']:
                    for correct_photo_level_2 in correct_photo_level_1['sizes']:
                        sum_size = correct_photo_level_2['height'] + correct_photo_level_2['width']
                        if needed_data[limit_count] == sum_size:
                            limit_count += 1
                            usual_date = datetime.fromtimestamp(correct_photo_level_1['date'])
                            correct_photo.append([correct_photo_level_2['url'], correct_photo_level_1['likes']['count'], usual_date])
                            if limit_count == 5:
                                self.vk_max_len = len(correct_photo)
                                return correct_photo
        else:
            while True:
                for correct_photo_level_1 in dict_photo['response']['items']:
                    for correct_photo_level_2 in correct_photo_level_1['sizes']:
                        sum_size = correct_photo_level_2['height'] + correct_photo_level_2['width']
                        if needed_data[limit_count] == sum_size:
                            limit_count += 1
                            usual_date = datetime.fromtimestamp(correct_photo_level_1['date'])
                            correct_photo.append([correct_photo_level_2['url'], correct_photo_level_1['likes']['count'], usual_date])
                            if limit_count == dict_photo['response']['count']:
                                self.vk_max_len = len(correct_photo)
                                return correct_photo


if __name__ == '__main__':
    access_token = input('Введите VK токен: ')
    user_id = input('Введите id пользователя: ')
    vk = VK(access_token, user_id)

    vk.max_size()

    path_to_file = 'images_from_vk'
    while True:
        print('\nКуда вы хотите загрузить фото?')
        print('Выберите нужный варинт ответа')
        print('1) Yandex disk \n2) Google disk\n')
        user_choice = int(input('Ваш ответ: '))
        if user_choice == 1:
            token_ya = input('\nВведите Yandex токен: ')
            uploader_ya = YaUploader(token_ya)
            result = uploader_ya.upload(path_to_file)
            print()
            print('DONE')
            break
        elif user_choice == 2:
            print('\nПройдите аунтефикацию')
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            user_go = GoogleUploader(gauth)
            result = user_go.upload(path_to_file)
            print()
            print('DONE')
            break
        else:
            print(f'Команда {user_choice} не найдена, проверьте доступные команды')