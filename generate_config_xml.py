import re
import argparse
import requests
from xml.sax.saxutils import escape

def parse_env_file():
    config_vars = []
    # Get the latest release tag
    release_info = requests.get('https://api.github.com/repos/matszwe02/ytdlp_web_player/releases/latest').json()
    latest_tag = release_info['tag_name']
    
    # Construct the URL to example.env using the latest release tag
    req = requests.get(f'https://raw.githubusercontent.com/matszwe02/ytdlp_web_player/{latest_tag}/src/example.env')
    f = req.text.splitlines()
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') and '=' not in line:
            continue
        match = re.match(r'^\s*#?\s*([A-Z_][A-Z0-9_]*)\s*=\s*(?:"([^"]*)"|([^#]*?))\s*(?:#\s*(.*))?\s*$', line)
        if match:
            print(f'{line=}')
            print(f'{match.group(1)=}')
            print(f'{match.group(2)=}')
            print(f'{match.group(3)=}')
            print(f'{match.group(4)=}')
            name = match.group(1)
            value = match.group(2) if match.group(2) is not None else match.group(3).strip()
            description = match.group(4).strip().strip('"') if match.group(4) else "" # Extract comment as description
            config_vars.append({'name': name, 'value': value, 'description': description})
    return config_vars

def generate_xml_config(config_vars):
    xml_output = []
    for var in config_vars:
        name = var['name']
        value = var['value']
        description = var['description']

        # Escape XML special characters (&, <, >, ") for use inside attributes
        escape_attr = lambda text: escape(text, {'"': '&quot;'})
        value = escape_attr(value)
        description = escape_attr(description)

        # Use the description directly from the .env file.
        # Ensure description is only added if it has content
        desc_attr = f'Description="{description}"' if description else ''

        config_name = name.replace('_', ' ').title()

        config_type = "Variable"
        extra_sections = ''
        if 'PATH' in name:
            config_type = "Path"
            extra_sections = 'Mode="rw"'
        elif 'PORT' in name:
            continue
        else:
            xml_output.append(
                f'  <Config Name="{config_name}" Target="{name}" Default="{value}" {desc_attr} Type="{config_type}" {extra_sections} Display="always" Required="false" Mask="false"/>'
            )
    return "\n".join(xml_output)


parser = argparse.ArgumentParser(description="Generate Unraid XML Configs from an .env file.")
parser.add_argument("env_file", help="Path to the .env file.")

config_vars = parse_env_file()
xml_configs = generate_xml_config(config_vars)
with open('templates/ytdlp-web-player.xml', 'r') as f:
    xml = f.read()

out = re.sub(r'<!-- config start -->.*?<!-- config end -->', lambda _: f'<!-- config start -->\n{xml_configs}\n<!-- config end -->', xml, flags=re.DOTALL)

with open('templates/ytdlp-web-player.xml', 'w') as f:
    f.write(out)