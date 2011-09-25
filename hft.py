import csv
import re
import urllib2
import json
import string

reader = csv.reader(open('Price Spreadsheet.csv', 'rU'))
rows = [row for row in reader if row][3:-6]
classes = ['SCOUT', 'SOLDIER', 'PYRO', 'DEMOMAN', 'HEAVY', 'ENGINEER', 'MEDIC',
    'SNIPER', 'SPY' 
]

def chunk_to_items(chunk):
    def convert_metal(metal): 
        low, high, kind = re.match('([\d.]*)-*([\d.]+) (S|Rc|Rf|Buds)', metal).group(1,2,3)
        
        if not low:
            low = '0'

        if kind == 'S':
            return float(low), float(high)
        elif kind == 'Rc':
            return float(low)*3, float(high)*3
        elif kind == 'Rf':
            return float(low)*9, float(high)*9
        elif kind == 'Buds':
            return 0, 0
        else:
            assert "wrong metal kind"
            
    items = {}
    slot = header.match(chunk[0][0]).group('slot')
    
    for row in chunk:
        s = header.match(row[0])
        
        if not s:
            if row[1] == '---':
                u = ''
            else:
                u = convert_metal(row[1])
            if row[2] == '---':
                v = ''
            else:
                v = convert_metal(row[2])
            if row[3] == '---':
                s = ''
            else:
                s = convert_metal(row[3])
                
            items[row[0].strip('*')] = {
            'slot': slot,
            'u': u,
            'v': v,
            's': s,
        }
        else:
            slot = s.group('slot')
            
    return items

header = re.compile('(?P<class>\w+) Slot (?P<slot>\d)')

items = {}
start = 0

for end, row in enumerate(rows):
    if '~' in row[0]:
        chunk = rows[start:end]
        m = header.match(chunk[0][0])
        items[m.group('class')] = chunk_to_items(chunk)
        start = end + 1
chunk = rows[start:]
m = header.match(chunk[0][0])
items[m.group('class')] = chunk_to_items(chunk)

#Spelling hotfixes, because the spreadsheet and schema use different names
hotfixes = [
    ('SCOUT', "Fan O'War", "Fan O' War"),
    ('SCOUT', 'Force-a-Nature', 'Force-A-Nature'),
    ('SOLDIER', 'Upgradeable TF_WEAPON_SHOTGUN_PRIMARY', 'Shotgun'),
    ('PYRO', 'Upgradeable TF_WEAPON_FLAMETHROWER', 'Flamethrower'),
    ('DEMOMAN', 'Loch-n-Load', 'Loch-N-Load'),
    ('DEMOMAN', 'Claidheamohmor', 'Claidheamh Mor'),
    ('ENGINEER', 'Upgradeable TF_WEAPON_WRENCH', 'Wrench'),
    ('MEDIC', 'Upgradeable TF_WEAPON_BONESAW', 'Bonesaw'),
    ('MEDIC', 'Upgradeable TF_WEAPON_SYRINGEGUN_MEDIC', 'Syringe Gun'),
    ('MEDIC', 'Upgradeable TF_WEAPON_MEDIGUN', 'Medi Gun'),
    ('SNIPER', 'Upgradeable TF_WEAPON_SNIPERRIFLE', 'Sniper Rifle'),
]

for hotfix in hotfixes:
    items[hotfix[0]][hotfix[1]] = items[hotfix[0]].pop(hotfix[2])

API_KEY = raw_input('Steam Api Key : ')
username = raw_input('Login Name (NOT alias)/Steam ID : ')
username = unicode(username)

if username.isnumeric()==False:
    xml = urllib2.urlopen("http://steamcommunity.com/id/"+username+"?xml=1").read()
    username = re.search("<steamID64>(\d+)</steamID64>", xml).group(1)

def get_items(key, userid):
    url = ''.join([
        'http://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/?key=',
        key, '&format=json&SteamID=', userid])
    print url
    return json.load(urllib2.urlopen(url))

def get_schema(key):
    url = 'http://api.steampowered.com/IEconItems_440/GetSchema/v0001/?format=json&key=' + key
    print url
    return json.load(urllib2.urlopen(url))
    

def search_item(defindex, schema):
    for item in schema['result']['items']:
        if item['defindex'] == defindex:
            return item

def parse_backpack(result):
    status = result['result']['status']
    slots = result['result']['num_backpack_slots']
    _items = result['result']['items']
    
    mapping = {6: 'u', 3: 'v', 11: 's'}
    low_sum, high_sum = 0.0, 0.0
    
    for item in _items:
        match = search_item(item['defindex'], schema)
        
        if not match['item_class'].startswith('tf_weapon'):
            continue
        
        name = re.sub('The ', '', match['name'])
        used = match['used_by_classes'][0].upper()
        
        if used in items and name in items[used]:
            low, high = items[used][name][mapping[item['quality']]]
            print name, mapping[item['quality']], low, high
            
            high_sum += high
            low_sum += low if low == 0.0 else high
        else:
            print "mismatch...", name, used
            
    print "Between ", low_sum, " to ", high_sum, " scrap."

result = get_items(API_KEY, username)
schema = get_schema(API_KEY)
parse_backpack(result)

