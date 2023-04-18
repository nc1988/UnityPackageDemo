
import os
import stat
import base64
import hashlib
#import getpass

hydra_environment_id_str = 'hydra_environment_id='

def get_md5_base64_bytes(data):
    hash = hashlib.md5(data)
    return base64.b64encode(hash.digest()).decode()

def get_md5_base64(filepath):
    with open(filepath, 'rb') as f:
        hash = hashlib.md5(f.read())
        return base64.b64encode(hash.digest()).decode()

def document_class(document):
    if document == 'eula':
        return 'EULADocument'
    elif document == 'tos':
        return 'ToSDocument'
    elif document == 'pp':
        return 'PPDocument'
    elif document == 'trackingconsent':
        return 'TrackingConsentDocument'
    elif document == 'epilepsy':
        return 'EpilepsyDocument'
    elif document == 'agegate':
        return 'AgeGateDocument'
    
    return 'HydraDocument'

def hydra_request_headers(hydra_environment_id):
    headers = {}
    headers['X-Hydra-Environment-Id'] = hydra_environment_id
    headers['Content-Type'] = 'application/json'
    return headers

def load_saved_hydra_environment_id(project_path):
    global hydra_environment_id_str
    config_path = os.path.join(project_path, 'hydra_config.txt')
    if os.path.isfile(config_path):
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        lines = []
        with open(config_path, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        count = 0
        while count < line_count:
            line = lines[count].strip()
            count += 1
            if line.startswith(hydra_environment_id_str):
                hydra_environment_id = line.replace(hydra_environment_id_str, '')
                return hydra_environment_id
    return ''

def save_hydra_environment_id(hydra_environment_id, project_path):
    global hydra_environment_id_str
    config_path = os.path.join(project_path, 'hydra_config.txt')
    if os.path.isfile(config_path):
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        lines = []
        is_config_changed = False
        got_config = False
        line_count = len(lines)
        count = 0
        while count < line_count and not got_config:
            line = lines[count].strip()
            count += 1
            if line.startswith(hydra_environment_id_str):
                got_config = True
                old_hydra_environment_id = line.replace(hydra_environment_id_str, '')
                if old_hydra_environment_id != hydra_environment_id:
                    lines[count] = hydra_environment_id_str + hydra_environment_id
                    is_config_changed = True
        if not is_config_changed and not got_config:
            lines.append(hydra_environment_id_str + hydra_environment_id)
            is_config_changed = True
        if is_config_changed:
            with open(config_path, 'w') as f:
                f.writelines(lines)
    else:
        lines = []
        lines.append(hydra_environment_id_str + hydra_environment_id)
        with open(config_path, 'w') as f:
            f.writelines(lines)