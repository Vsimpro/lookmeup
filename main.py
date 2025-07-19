from dotenv import load_dotenv; load_dotenv()
import io, os, logging, dnserver
from dnserver.main import logger

from modules import domainparsing


# Global Variables
PORT   = 53
ZONES  = "zones.toml"

DOMAIN = os.getenv("DOMAIN")

SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def listen_and_parse( capturer : io.StringIO ):
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
        query_domain = [ word for word in last_line.split(" ") if DOMAIN.lower() in word.lower() ][0].split(".[A]")[0]
        
        if f"exfil.{ DOMAIN }".lower()  in query_domain.lower():
            domainparsing.handle_exfil( query_domain )
        
        if f"beacon.{ DOMAIN }".lower() in query_domain.lower():
            domainparsing.handle_beacon( query_domain )

        previous_log = log
        

def initialize():
    global DOMAIN
    
    if not os.path.exists(".env"):
        raise Exception( ".env file is missing!" )
    
    no_slack_webhook   = (SLACK_WEBHOOK == ""   or SLACK_WEBHOOK == None)
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
    
    # Prepare log handling
    capture = io.StringIO()
    channel = logging.StreamHandler( capture )
    
    # Remove all existing previous handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.addHandler(logging.NullHandler())     
    logger.addHandler( channel )
    
    # Prepare DNS server
    server = dnserver.DNSServer.from_toml( ZONES, port = PORT )
    server.start()
    
    assert server.is_running
    
    # Parse the logs
    listen_and_parse( capture )

    
if __name__ == "__main__":
    initialize()
    main()
