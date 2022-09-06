#Jonathans Cloudflare API program
#Must use python 3.10 or higher

import CloudFlare
import argparse
import configparser
import os

config_object = configparser.ConfigParser()

def configure():
    print('=============Configuring CloudFlared Record APIv4=============')
    print('To Rerun this script after configuring with cloudflared --configure')
    print('To Quit this script press CTRL+C')
    config_field = ('email', 'api-key')
    
    if os.path.isfile('config.ini'):
        config_object.read("config.ini")
        
    else:
        config_object['CONFIG'] = {'email': '', 'api-key': ''}

    for field in config_field:
        candidate = input(f'\nEnter the {field} associated with your cloudflare account: [{config_object["CONFIG"][field]}] \n')
        if candidate:
            config_object["CONFIG"][field] = candidate
            
    try:
        cf = CloudFlare.CloudFlare(email=config_object["CONFIG"]["email"], token=config_object["CONFIG"]["api-key"])
        cf.zones.get(params={})
        config_object.write(open("config.ini", "w"))
        print('Configuration completed successfully')
    except:
        print('Configuration Failed, Invalid Credentials or Zone')
        exit(2)
    exit(0)

class Configure(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        configure()


#parser.add_argument('--configure', action='store_true', help='Configure CloudFlared')
#args = parser.parse_args()
#if args.configure:
    #configure()

config_object.read("config.ini")

api_key = config_object["CONFIG"]["api-key"]
email = config_object["CONFIG"]["email"]

 

def argument_str(arg):
    arg = str(arg).strip()
    return arg

def argument_type(arg):
    arg = str(arg).strip().upper()
    if arg in ["A", "AAAA", "CNAME", "TXT", "SRV", "LOC", "MX", "NS", "SPF", "CERT"]:
        return arg
    else:
        print('-t/--type must be one of the following: A, AAAA, CNAME, SRV')
        exit(2)

parser = argparse.ArgumentParser() 
parser.register('action', 'docstring', Configure)
group1 = parser.add_argument_group('docs', 'doc printing')

group2 = parser.add_argument_group('args','main args')
group2.add_argument('--configure', action='docstring', help='Configure CloudFlared',nargs=0)



group1.add_argument('zone',type = argument_str, help='Zone to edit')
group1.add_argument('action',type = argument_str,help='add or delete')
group1.add_argument('type', type = argument_type, help='type of record')
group1.add_argument('name', type= argument_str ,help='name of record')
group1.add_argument('-n','--newname', type= argument_str ,help='updated name of record')
group1.add_argument('-c','--content', type = str, help='content of record',nargs='?', default="@")
group1.add_argument('--proxied', type=bool ,help='whether to proxy the record')
group1.add_argument('--ttl', type=lambda x: int(x) if (int(x)>=60 and int(x)<=86400) or int(x) == 1 else False)
group1.add_argument('--priority', type=lambda x: int(x) if (int(x)>=0 and int(x)<=65535) else False)
group1.add_argument('--port',type=int,help='port of record')

args = parser.parse_args()

zone = ".".join(args.zone.split(".")[-2:])
cf = CloudFlare.CloudFlare(email=email, token=api_key)

zones = cf.zones.get(params={"name": zone})

if len(zones) == 0:
    print(f"Could not find CloudFlare zone {zone}, please check domain {zone}")
    exit(2)
    
zone_id = zones[0]["id"]
records = cf.zones.dns_records.get(zones[0]['id'], params={"name": zone})

matched_records = cf.zones.dns_records.get(zone_id, params={"name":args.name,"type":args.type})

def search_record():
    if len(matched_records) == 0:
        print(f"Could not find record {args.name} in zone {zone}")
        exit(2)
    else:
        for record in matched_records:
            for key in record:
                print(f"{key}: {record[key]}")

def add_record():
        if matched_records:
            print(f"{args.type} record {args.name} in zone {zone} already exists")
            exit(2)
        record = {}
        record["type"] = args.type
        record["name"] = args.name
        record["content"] = args.content
        record["ttl"] = args.ttl
        record["proxied"] = args.proxied
        record["priority"] = args.priority
        cf.zones.dns_records.post(zone_id, data=record)
        print(f"Added {args.type} record {args.name} in zone {zone}")

def update_record():
    if len(matched_records) == 0:
        print(f"Could not find {args.type} record {args.name} in zone {zone}")
    if len(matched_records) == 1:
        record = matched_records[0]
        if args.content != None:
            record["content"] = args.content
        if args.ttl != None:
            record['ttl'] = args.ttl
        if args.proxied != None:
            record['proxied'] = args.proxied
        if args.priority != None:
            record['priority'] = args.priority
        if args.updatename != None:
            record['name'] = args.updatename
        cf.zones.dns_records.put(zone_id, record['id'], data=record)
        print(f"Updated record {args.name} in zone {zone}")
        
def delete_record():
    if len(matched_records) == 0:
        print(f"Could not find {args.type} record {args.name} in zone {zone}")
        exit(2)
    elif len(matched_records) > 1:
        if args.content is None:
            print(f"Found multiple {args.type} records for {args.name} in zone {zone}, please specify a content value")
            exit(2)
        else:
            for record in matched_records:
                if record["content"] == args.content:
                    cf.zones.dns_records.delete(zone_id, record["id"])
                    print(f"Deleted record {args.name} in zone {zone} with content {args.content}")
                    exit(0)
            print(f"Could not find record {args.name} in zone {zone} with content {args.content}")
            exit(2)
    elif len(matched_records) == 1:
        cf.zones.dns_records.delete(zone_id, matched_records[0]["id"])
        print(f"Deleted record {args.name} in zone {zone}")
    
def main():
    match args.action:
        case "add":
            add_record()
        case "delete":
            delete_record()
        case "search":
            search_record()
        case "update":
            update_record()
        case other:
            print("Invalid action, must be add or delete, or search")
            exit(2)
if __name__ == '__main__':
    main()