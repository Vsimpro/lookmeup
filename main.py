from dotenv import load_dotenv; load_dotenv()
import io, os, logging, dnserver
from dnserver.main import logger

import modules.queries as queries
from modules import domainparsing
from modules import database as db



# Global Variables
PORT   = 5311
ZONES  = "zones.toml"

DOMAIN = os.getenv("DOMAIN")

SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# TODO: Move to config.toml system
PREFIXES = {
    "exfil" : {
        "webhooks" : [DISCORD_WEBHOOK, SLACK_WEBHOOK],
        "type"    : "exfil",
        "decode_function" : None
    },
    "beacon" : {
        "webhooks" : [DISCORD_WEBHOOK, SLACK_WEBHOOK],
        "type"    : "beacon",
        "decode_function" : None
    }
}

def listen_and_parse( capturer : io.StringIO, decode_function ):
    global DOMAIN 
    
    log          = ""
    previous_log = ""
    
    while 1:
        log = str( capturer.getvalue() )
        
        # skip unintenteresting logs
        if log == previous_log:
            continue
        
        if DOMAIN.lower() not in log.lower():
            continue
        
        # split into lines, and get the last one
        lines     = log.split("\n")
        last_line = lines[-2]
        
        # get the domain that's being looked up.
        try:
            query_domain = [ word for word in last_line.split(" ") if DOMAIN.lower() in word.lower() ][0].split(".[A]")[0]
        except Exception as e:
            print( "Ran into an error. Details: ", last_line, "and exception:", e  )
            return
        
        for PREFIX in PREFIXES:
            if f".{PREFIX}.{ DOMAIN }".lower() not in query_domain.lower():
                continue
            
            message_function = None
            
            # Choose which message type to use
            if PREFIXES[ PREFIX ]["type"] == "exfil":
                message_function = domainparsing.handle_exfil
        
            if PREFIXES[ PREFIX ]["type"] == "beacon":
                message_function = domainparsing.handle_beacon
                
            if message_function != None:
                message_function( query_domain,  PREFIXES[ PREFIX ]["decode_function"], PREFIXES[ PREFIX ]["webhooks"] )
            

        previous_log = log
        

def initialize():
    global DOMAIN
    
    if not os.path.exists(".env"):
        raise Exception( ".env file is missing!" )
    
    no_slack_webhook   = (SLACK_WEBHOOK   == "" or SLACK_WEBHOOK   == None)
    no_discord_webhook = (DISCORD_WEBHOOK == "" or DISCORD_WEBHOOK == None)
    
    if no_slack_webhook and no_discord_webhook:
        raise Exception( "Both discord and slack webhook in .env are empty. Please provide either or both." )
    
    if DOMAIN == None or DOMAIN == "":
        raise ValueError( "DOMAIN in .env can not be 'None' or empty!" )
    
    if not os.path.exists("zones.toml"):  
        zones_template = ""
        with open("./statics/zones_template.toml", "r") as file:
            
            zones_template = file.read()
            
            zones_template = zones_template.replace("{{%DOMAIN%}}", DOMAIN)
            zones_template = zones_template.replace("{{%IP_ADDRESS%}}", "1.2.3.4")

        with open("./zones.toml", "w+") as file:
            file.write(zones_template)


def main():
    global ZONES
    
    db.initialize_db( {
        "file_table"      : queries.create_file_table, 
        "filechunk_table" : queries.create_filechunk_table,
        "sentlog_table"   : queries.create_sentlog_table
    } )
    
    # Prepare log handling
    capture = io.StringIO()
    channel = logging.StreamHandler( capture )
    
    # Remove all existing previous handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.addHandler( logging.NullHandler() )     
    logger.addHandler( channel )
    
    # Prepare DNS server
    server = dnserver.DNSServer.from_toml( ZONES, port = PORT )
    server.start()
    
    assert server.is_running
    
    # Parse the logs
    from plugins.b62 import decode
    
    PREFIXES["exfil"]["decode_function"] = decode
    PREFIXES["beacon"]["decode_function"] = decode
    
    listen_and_parse( capture, decode )

if __name__ == "__main__":
    initialize()
    main()
