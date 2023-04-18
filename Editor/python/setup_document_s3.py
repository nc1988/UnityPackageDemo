
import os
import json
import stat
import datetime
import argparse
import requests

from document_utils import *
from datetime import datetime

def download_filesystem_metadata(document, file_systems_slug, file_system_url, headers, content_harbinger_path):
    file_system_res = requests.get(file_system_url, headers=headers)
    print(file_system_res.text)
    file_system_res_json = file_system_res.json()
    file_system_data = file_system_res_json['data']
    data_file_name = document + '.data'
    data_file_path = os.path.join(content_harbinger_path, data_file_name)
    if os.path.exists(data_file_path):
        os.remove(data_file_path)
    with open(data_file_path, 'w') as data_file:
        json_obj = json.dumps(file_system_data, indent=4)
        data_file.write(json_obj)

def download_document(platform, document, project_path, hydra_environment_id):

    print('*************************************')
    print(document)
    print()
    
    headers = hydra_request_headers(hydra_environment_id)
    file_systems_slug = document + '-fs'
    
    hydra_file_system_url = 'https://int-api.wbagora.com/file_systems/' + file_systems_slug
    
    content_path = os.path.join(project_path, 'Assets', 'StreamingAssets')
    if not os.path.exists(content_path):
        os.mkdir(content_path)
    content_hydraharbinger_path = os.path.join(content_path, 'HydraHarbinger')
    if not os.path.exists(content_hydraharbinger_path):
        os.mkdir(content_hydraharbinger_path)
    
    # get file system metadata
    download_filesystem_metadata(document, file_systems_slug, hydra_file_system_url, headers, content_hydraharbinger_path)
    
    # query instances
    hydra_instances_list_url = hydra_file_system_url + '/instances/list'
    # query fields files and download_url 
    hydra_instances_list_url = hydra_instances_list_url + '?fields=files.download_url'
    
    instances_list_res = requests.get(hydra_instances_list_url, headers=headers)
    print(instances_list_res.text)
    
    instances_list_res_json = instances_list_res.json()
    instance_id = ''
    has_instance_4_platform = False
    files_map = {}
    found_inst = None
    default_inst = None
    first_inst = None
    for inst in instances_list_res_json['results']:
        if first_inst == None:
            first_inst = inst
        if inst['unique_key'] == 'default':
            default_inst = inst
        if inst['unique_key'] == platform:
            found_inst = inst
            has_instance_4_platform = True
    if not has_instance_4_platform:
        if default_inst != None:
            print('There is no instance for platform ' + platform + '. Use default platform instead.')
            print()
            found_inst = default_inst
        elif first_inst != None:
            print('There is no instance for platform ' + platform + ' nor default platform. Use the first platform ' + first_inst['unique_key'])
            print()
            found_inst = first_inst
    
    if found_inst == None:
        print('There is no instance for platform ' + platform)
        return False, ''
    
    instance_id = found_inst['id']
    for file in found_inst['files']:
        filename = file['filename']
        file_data = {}
        file_data['md5'] = file['md5_checksum']
        file_data['url'] = file['download_url']
        file_data['need_download'] = True
        files_map[filename] = file_data
    
    platform_path = os.path.join(content_hydraharbinger_path, instance_id)
    if not os.path.exists(platform_path):
        os.mkdir(platform_path)
    #platform_path = os.path.join(platform_path, platform)
    #if not os.path.exists(platform_path):
    #    os.mkdir(platform_path)
    
    # get downloaded files's md5
    for f in os.listdir(platform_path):
        f_path = os.path.join(platform_path, f)
        if os.path.isfile(f_path):# and (f.endswith('.txt') or f == 'metadata.json'):
            # make eula file read-write able
            os.chmod(f_path, stat.S_IRUSR | stat.S_IWUSR)
            md5 = get_md5_base64(f_path)
            if f in files_map and md5 == files_map[f]['md5']:
                files_map[f]['need_download'] = False
                print('file ' + f + ' already latest.')
    
    for file in files_map:
        file_data = files_map[file]
        need_download = file_data['need_download']
        if need_download:
            print('download file ' + file + ' with url')
            download_url = file_data['url']
            print(download_url)
            download_res = requests.get(download_url)
            file_path = os.path.join(platform_path, file)
            print('to destination : ' + file_path)
            if os.path.exists(file_path):
                # remove old file
                os.remove(file_path)
            with open(file_path, 'wb') as f:
                f.write(download_res.content)
    print('Done download ' +  document)
    return True, instance_id

def modify_config(project_path, platform, document, instance_id):
    config_path = os.path.join(project_path, 'Assets', 'GameData', 'HarbingerSetting.json')
    
    if os.path.isfile(config_path):
        # set DefaultGame.ini read-write able
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        try:
            config_file = open(config_path, 'r')
            data = json.load(config_file)
            config_file.close()
        except:
            data = {}
        if platform == 'Stm' or platform == 'stm':
            data['sPlatform'] = 'Steam'
        else:
            data['sPlatform'] = platform.capitalize()
        if not ('sInstanceId' in data):
            data['sInstanceId'] = {}
        instance_data = data['sInstanceId']
        instance_data[document_class(document)] = instance_id
        config_file = open(config_path, 'w')
        config_file.write(json.dumps(data, indent=4))
        config_file.close()
    else:
        data = {}
        if platform == 'Stm' or platform == 'stm':
            data['sPlatform'] = 'Steam'
        else:
            data['sPlatform'] = platform.capitalize()
        data['sInstanceId'] = {}
        data['sInstanceId'][document_class(document)] = instance_id
        config_file = open(config_path, 'w')
        config_file.write(json.dumps(data, indent=4))
        config_file.close()
    
    print('Done setting HarbingerSetting.json file.')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Hydra Harbinger setup schema')
    parser.add_argument('--platform', dest='platform', default='window', help='hydra harbinger platform [window/discord/epic/ps/stadia/steam/switch/xb/android/ios]')
    parser.add_argument('--path', dest='path', default='', help='path to uproject file')
    parser.add_argument('--project-version', dest='project_version', default='', help='version of current uproject')
    parser.add_argument('--increase-version', dest='increase_version', default='no', help='should auto increase version of current uproject!')
    parser.add_argument('--hydra-environment-id', dest='hydra_environment_id', default='', help='hydra environment id')
    args = parser.parse_args()
    
    project_path = args.path
    if (not project_path) or (len(project_path) < 1):
        #promp Unity project folder
        project_path = input('Unity Project : ')             # Harbinger folder
    
    platform = args.platform
    if (not platform) or (len(platform) < 1):
        print('Invalid platform. Platform must be one of [window/discord/epic/ps/stadia/steam/switch/xb/android/ios]')
        exit(1)
    platform = platform.lower()
    if platform not in ['window','discord','epic','ps','stadia','steam','switch','xb','android','ios']:
        print('Invalid platform. Platform must be one of [window/discord/epic/ps/stadia/steam/switch/xb/android/ios]')
        exit(1)
    if platform == 'steam':
        platform = 'stm'
    
    hydra_environment_id = args.hydra_environment_id
    if (not hydra_environment_id) or (len(hydra_environment_id) < 1):
        #no hydra_environment_id, look for saved one in hydra_config.txt file
        saved_environment_id = load_saved_hydra_environment_id(project_path)
        if len(saved_environment_id) < 1:
            #promp input hydra_environment_id
            hydra_environment_id = input('Hydra Enviroment Id: ')
            save_hydra_environment_id(hydra_environment_id, project_path)
        else:
            hydra_environment_id = saved_environment_id
    else:
        #has hydra_environment_id, save/update hydra_config.txt file
        save_hydra_environment_id(hydra_environment_id, project_path)

    #for test purpose only : when 'window' platform, download 'xb' instead
    document_list = ['eula','tos','pp','trackingconsent','epilepsy','agegate']
    for doc in document_list:
        document = doc.strip()
        if len(document) > 1:
            if platform == 'window':
                success_download, instance_id = download_document('xb', document, project_path, hydra_environment_id)
            else:
                success_download, instance_id = download_document(platform, document, project_path, hydra_environment_id)
    
            if success_download:
                modify_config(project_path, platform, document, instance_id)
            else:
                print('Couldnot download ' + document)
    
    project_version = args.project_version
    increase_version = args.increase_version
    should_increase_version = False
    if increase_version:
        increase_version = increase_version.lower()
        if increase_version == 'true' or increase_version == 'yes':
            should_increase_version = True
    
    print('Done.')